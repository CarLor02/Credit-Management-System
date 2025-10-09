"""
文档管理API
"""

import os
import uuid
from flask import request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from sqlalchemy import or_

from database import db
from db_models import Document, Project, DocumentStatus, User, UserRole
from utils import validate_request, log_action
from api.auth import token_required
from services.knowledge_base_service import KnowledgeBaseService
from services.document_processor import DocumentProcessor

def allowed_file(filename):
    """检查文件类型是否允许"""
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'md'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_type(filename):
    """根据文件扩展名获取文件类型"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if ext in ['pdf']:
        return 'pdf'
    elif ext in ['xls', 'xlsx']:
        return 'excel'
    elif ext in ['docx']:
        return 'word'
    elif ext in ['jpg', 'jpeg', 'png']:
        return 'image'
    elif ext in ['md']:
        return 'markdown'
    else:
        return 'other'

def register_document_routes(app):
    @app.route('/api/documents/<int:document_id>/kb-retry', methods=['POST'])
    @token_required
    def retry_kb_parse_failed(document_id):
        """知识库解析失败重试：删除知识库绑定文件后重新上传解析"""
        try:
            current_user = request.current_user
            document = Document.query.get_or_404(document_id)
            if document.status != DocumentStatus.KB_PARSE_FAILED:
                return jsonify({'success': False, 'error': '仅知识库解析失败状态可重试'}), 400
            # 删除知识库绑定文件
            from services.knowledge_base_service import knowledge_base_service
            kb_deleted = knowledge_base_service.delete_document_from_knowledge_base(document.project_id, document.id)
            # 重新上传知识库并解析
            kb_uploaded = knowledge_base_service.upload_document_to_knowledge_base(document.project_id, document.id)
            # 记录操作日志
            log_action(
                user_id=current_user.id,
                action='retry_kb_parse_failed',
                resource_type='document',
                resource_id=document_id,
                details=f'重试知识库解析失败文档"{document.name}"'
            )
            if kb_uploaded:
                return jsonify({'success': True, 'message': f'文档"{document.name}"知识库重试任务已启动'})
            else:
                return jsonify({'success': False, 'error': '知识库重试失败'}), 500
        except Exception as e:
            current_app.logger.error(f"知识库重试API错误: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'error': '服务器内部错误'}), 500
    """注册文档相关路由"""
    
    @app.route('/api/documents', methods=['GET'])
    @token_required
    def get_documents():
        """获取文档列表"""
        try:
            # 获取查询参数
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 20, type=int)
            search = request.args.get('search', '')
            project_id = request.args.get('project_id', type=int)
            status = request.args.get('status', '')
            file_type = request.args.get('type', '')

            # 过滤掉无效值
            if search in ['undefined', 'null', '']:
                search = ''
            if status in ['undefined', 'null', '']:
                status = ''
            if file_type in ['undefined', 'null', '']:
                file_type = ''

            # 构建查询
            query = Document.query.join(Project)

            # 根据用户角色筛选数据
            current_user = request.current_user
            if current_user.role != UserRole.ADMIN:
                # 非管理员只能看到自己上传的文档或自己项目中的文档
                query = query.filter(
                    or_(
                        Document.upload_by == current_user.id,
                        Project.created_by == current_user.id,
                        Project.assigned_to == current_user.id
                    )
                )

            # 搜索过滤
            if search:
                query = query.filter(
                    or_(
                        Document.name.contains(search),
                        Project.name.contains(search)
                    )
                )
            
            # 项目过滤
            if project_id:
                query = query.filter(Document.project_id == project_id)
            
            # 状态过滤
            if status and status in ['uploading', 'processing', 'processed', 'uploading_to_kb', 'parsing_kb', 'completed', 'failed', 'kb_parse_failed']:
                query = query.filter(Document.status == DocumentStatus(status))
            
            # 文件类型过滤
            if file_type:
                query = query.filter(Document.file_type == file_type)
            
            # 分页
            total = query.count()
            documents = query.order_by(Document.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
            
            # 转换为字典列表，使用简化的格式与mock保持一致
            documents_data = []
            for doc in documents:
                # 获取标签的中文显示名称
                from db_models import DOCUMENT_LABEL_NAMES
                label_display = DOCUMENT_LABEL_NAMES.get(doc.label) if doc.label else None
                
                doc_dict = {
                    'id': doc.id,
                    'name': doc.original_filename,  # 使用原始文件名显示
                    'project': doc.project.name if doc.project else '',
                    'project_id': doc.project_id,  # 添加项目ID
                    'type': doc.file_type,  # 直接使用数据库中的原始值
                    'size': doc.format_file_size(),
                    'status': doc.status.value.lower(),
                    'uploadTime': doc.created_at.strftime('%Y-%m-%d %H:%M'),
                    'progress': doc.progress,
                    'label': label_display,  # 返回中文标签显示
                    'label_code': doc.label.value if doc.label else None  # 同时返回英文代码
                }
                documents_data.append(doc_dict)

            # 直接返回文档数组，与mock格式完全一致
            return jsonify(documents_data)
            
        except Exception as e:
            current_app.logger.error(f"重试文档处理失败: {e}")
            return jsonify({'success': False, 'error': '重试失败'}), 500

    @app.route('/api/documents/<int:document_id>/upload-to-knowledge-base', methods=['POST'])
    @token_required
    def upload_document_to_knowledge_base(document_id):
        """手动上传文档到知识库"""
        try:
            current_user = request.current_user
            
            # 获取文档信息
            document = Document.query.get(document_id)
            if not document:
                return jsonify({'success': False, 'error': '文档不存在'}), 404
            
            # 权限检查：只有文档上传者、项目创建者或管理员可以上传
            project = document.project
            if not project:
                return jsonify({'success': False, 'error': '项目不存在'}), 404
            
            if (current_user.role != UserRole.ADMIN and 
                document.upload_by != current_user.id and 
                project.created_by != current_user.id):
                return jsonify({'success': False, 'error': '权限不足'}), 403
            
            # 检查文档状态
            if document.status != DocumentStatus.PROCESSED:
                status_messages = {
                    DocumentStatus.UPLOADING: '文档正在上传中',
                    DocumentStatus.PROCESSING: '文档正在处理中',
                    DocumentStatus.UPLOADING_TO_KB: '文档正在上传到知识库',
                    DocumentStatus.PARSING_KB: '文档正在解析中',
                    DocumentStatus.COMPLETED: '文档已完成知识库解析',
                    DocumentStatus.FAILED: '文档处理失败',
                    DocumentStatus.KB_PARSE_FAILED: '文档知识库解析失败'
                }
                message = status_messages.get(document.status, f'文档状态不正确: {document.status.value}')
                return jsonify({'success': False, 'error': message}), 400
            
            # 调用文档处理器的手动上传方法
            from services.document_processor import document_processor
            success = document_processor.upload_to_knowledge_base_manually(document_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '文档已开始上传到知识库，请稍后查看状态'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '上传到知识库失败，请稍后重试'
                }), 500
                
        except Exception as e:
            current_app.logger.error(f"手动上传文档到知识库API失败: {e}")
            return jsonify({'success': False, 'error': '服务器内部错误'}), 500
    
    @app.route('/api/documents/<int:document_id>', methods=['GET'])
    @token_required
    def get_document(document_id):
        """获取文档详情"""
        try:
            current_user = request.current_user
            document = Document.query.get_or_404(document_id)

            # 检查用户是否有权限访问此文档
            if current_user.role != UserRole.ADMIN:
                if (document.upload_by != current_user.id and
                    document.project.created_by != current_user.id and
                    document.project.assigned_to != current_user.id):
                    return jsonify({'error': '您没有权限访问此文档'}), 403

            # 使用简化的格式与mock保持一致
            from db_models import DOCUMENT_LABEL_NAMES
            label_display = DOCUMENT_LABEL_NAMES.get(document.label) if document.label else None
            
            document_data = {
                'id': document.id,
                'name': document.original_filename,  # 使用原始文件名显示
                'project': document.project.name if document.project else '',
                'project_id': document.project_id,  # 添加项目ID
                'type': document.file_type,  # 直接使用数据库中的原始值
                'size': document.format_file_size(),
                'status': document.status.value.lower(),
                'uploadTime': document.created_at.strftime('%Y-%m-%d %H:%M'),
                'progress': document.progress,
                'label': label_display,  # 返回中文标签显示
                'label_code': document.label.value if document.label else None  # 同时返回英文代码
            }

            # 直接返回文档数据，与mock格式完全一致
            return jsonify(document_data)
            
        except Exception as e:
            current_app.logger.error(f"获取文档详情失败: {e}")
            return jsonify({'success': False, 'error': '获取文档详情失败'}), 500
    
    @app.route('/api/documents/upload', methods=['POST'])
    def upload_document():
        """上传文档"""
        try:
            # 先进行基本的文件检查，再进行认证
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': '没有文件被上传'}), 400

            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': '没有选择文件'}), 400

            # 特别检查doc/docx格式，直接拦截（在认证之前）
            file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if file_ext in ['doc', 'docx']:
                return jsonify({'message': '暂不支持该格式，请转化成PDF格式上传'}), 400

            # 检查文件类型
            if not allowed_file(file.filename):
                return jsonify({'success': False, 'error': '不支持的文件类型'}), 400

            # 进行用户认证检查
            from api.auth import verify_token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'success': False, 'error': '需要认证'}), 401

            token = auth_header.split(' ')[1]
            user_id = verify_token(token)
            if not user_id:
                return jsonify({'success': False, 'error': '认证失败'}), 401

            # 获取用户对象
            current_user = User.query.get(user_id)
            if not current_user or not current_user.is_active:
                return jsonify({'success': False, 'error': '用户不存在或已禁用'}), 401

            # 获取其他参数
            project_id = request.form.get('project_id')
            project_name = request.form.get('project')  # 保留用于兼容性
            document_name = request.form.get('name', file.filename)
            label = request.form.get('label')  # 获取label参数

            # 优先使用project_id，如果没有则使用project_name（向后兼容）
            if project_id:
                try:
                    project_id = int(project_id)
                    project = Project.query.get(project_id)
                    current_app.logger.info(f"使用project_id查找项目: {project_id}, 找到项目: {project.name if project else 'None'}")
                    if not project:
                        return jsonify({'success': False, 'error': '项目不存在'}), 404
                except ValueError:
                    return jsonify({'success': False, 'error': '项目ID格式错误'}), 400
            elif project_name:
                # 向后兼容：使用项目名称查找
                project = Project.query.filter_by(name=project_name).first()
                current_app.logger.info(f"使用project_name查找项目: {project_name}, 找到项目ID: {project.id if project else 'None'}")
                if not project:
                    return jsonify({'success': False, 'error': '项目不存在'}), 404
            else:
                return jsonify({'success': False, 'error': '缺少项目信息'}), 400

            # 检查用户是否有权限向此项目上传文档
            if current_user.role != UserRole.ADMIN:
                if (project.created_by != current_user.id and
                    project.assigned_to != current_user.id):
                    return jsonify({'error': '您没有权限向此项目上传文档'}), 403
            
            # 先获取文件类型（使用原始文件名）
            original_filename = file.filename
            file_type = get_file_type(original_filename)

            # 生成安全的文件名
            filename = secure_filename(original_filename)

            # 如果secure_filename过滤掉了所有字符（比如中文文件名），使用原始扩展名
            if not filename or '.' not in filename:
                # 提取原始扩展名
                if '.' in original_filename:
                    ext = original_filename.rsplit('.', 1)[1]
                    filename = f"document.{ext}"
                else:
                    filename = "document"

            unique_filename = f"{uuid.uuid4().hex}_{filename}"

            # 确保上传目录存在 - 使用项目的folder_uuid创建子目录
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            project_folder = os.path.join(upload_folder, project.folder_uuid)

            # 创建项目文件夹（如果不存在）
            if not os.path.exists(project_folder):
                os.makedirs(project_folder)

            # 保存文件到项目特定的文件夹
            file_path = os.path.join(project_folder, unique_filename)
            file.save(file_path)

            # 获取文件信息
            file_size = os.path.getsize(file_path)
            
            # 处理label参数
            document_label = None
            if label:
                try:
                    from db_models import DocumentLabel, DOCUMENT_LABEL_NAMES
                    # 直接将前端传来的英文值转换为枚举
                    if hasattr(DocumentLabel, label):
                        document_label = getattr(DocumentLabel, label)
                        current_app.logger.info(f"找到文档标签: {label} -> {document_label}")
                    else:
                        # 如果传来的是中文，通过映射找到对应的枚举
                        for enum_item in DocumentLabel:
                            if DOCUMENT_LABEL_NAMES.get(enum_item) == label:
                                document_label = enum_item
                                current_app.logger.info(f"通过中文标签找到枚举: {label} -> {document_label}")
                                break
                        if not document_label:
                            current_app.logger.warning(f"未找到匹配的文档标签: {label}")
                except Exception as e:
                    current_app.logger.warning(f"处理文档标签失败: {e}")
            
            # 如果有label，修改document_name添加中文前缀
            final_document_name = document_name
            if document_label:
                from db_models import DOCUMENT_LABEL_NAMES
                chinese_label = DOCUMENT_LABEL_NAMES.get(document_label)
                if chinese_label:
                    label_prefix = chinese_label + "_"
                    # 检查是否已经有前缀了（避免重复添加）
                    if not document_name.startswith(label_prefix):
                        final_document_name = label_prefix + document_name
                    current_app.logger.info(f"添加中文标签前缀: {chinese_label} -> {final_document_name}")
                else:
                    current_app.logger.warning(f"无法找到标签的中文名称: {document_label}")
            
            # 创建文档记录 - 初始状态为UPLOADING
            document = Document(
                name=final_document_name,  # 使用添加了label前缀的文件名
                original_filename=original_filename,  # 使用原始文件名
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
                mime_type=file.mimetype,
                project_id=project.id,
                status=DocumentStatus.UPLOADING,  # 初始状态为上传中
                progress=0,
                upload_by=current_user.id,  # 使用当前用户ID
                label=document_label  # 添加label字段
            )
            
            db.session.add(document)
            db.session.commit()
            
            # 记录日志
            log_action(
                user_id=document.upload_by,
                action='document_upload_start',
                resource_type='document',
                resource_id=document.id,
                details=f'开始上传文档: {document.name}'
            )
            
            # 先返回上传完成状态的文档信息
            upload_response = {
                'success': True,
                'data': {
                    'id': document.id,
                    'name': document.name,
                    'project': project.name,
                    'project_id': project.id,  # 添加项目ID
                    'type': document.file_type,  # 直接使用数据库中的原始值
                    'size': document.format_file_size(),
                    'status': 'uploading',
                    'uploadTime': document.created_at.strftime('%Y-%m-%d %H:%M'),
                    'progress': 0
                },
                'message': '文档上传开始'
            }
            
            # 记录上传完成日志
            log_action(
                user_id=document.upload_by,
                action='document_upload_complete',
                resource_type='document',
                resource_id=document.id,
                details=f'文档上传完成: {document.name}'
            )
            
            # 触发文档处理
            from services.document_processor import document_processor
            
            # 保存文档ID和项目名，避免会话问题
            doc_id = document.id
            project_name_for_log = project.name
            
            # 检查是否为md文件
            if file_type == 'markdown':
                # md文件直接处理
                def process_md_file():
                    """处理md文件"""
                    try:
                        with app.app_context():
                            current_app.logger.info(f"开始处理md文件: {doc_id}")
                            success = document_processor.process_markdown_file(doc_id)
                            
                            if success:
                                current_app.logger.info(f"md文件处理完成: {doc_id}")
                                # 知识库创建和上传由document_processor处理，这里不再重复调用
                                
                                # 记录活动日志
                                try:
                                    from services.stats_service import ActivityLogger
                                    doc = Document.query.get(doc_id)
                                    if doc:
                                        user = User.query.get(doc.upload_by)
                                        user_name = user.full_name if user else 'Unknown'
                                        ActivityLogger.log_document_uploaded(
                                            doc.id, doc.name, project_name_for_log, doc.upload_by, user_name
                                        )
                                except Exception as e:
                                    current_app.logger.warning(f"记录活动日志失败: {e}")
                            else:
                                current_app.logger.error(f"md文件处理失败: {doc_id}")
                                
                    except Exception as e:
                        current_app.logger.error(f"md文件处理异常: {e}")
                
                # 在后台线程中处理md文件
                import threading
                thread = threading.Thread(target=process_md_file)
                thread.daemon = True
                thread.start()
            elif file_type == 'word':
                # Word文件处理
                def process_word_file():
                    """处理Word文件"""
                    try:
                        with app.app_context():
                            current_app.logger.info(f"开始处理Word文件: {doc_id}")
                            success = document_processor.process_word_file(doc_id)
                            
                            if success:
                                current_app.logger.info(f"Word文件处理完成: {doc_id}")
                                # 知识库创建和上传由document_processor处理，这里不再重复调用
                                
                                # 记录活动日志
                                try:
                                    from services.stats_service import ActivityLogger
                                    doc = Document.query.get(doc_id)
                                    if doc:
                                        user = User.query.get(doc.upload_by)
                                        user_name = user.username if user else 'Unknown'
                                        ActivityLogger.log_document_uploaded(
                                            doc.id, doc.name, project_name_for_log, doc.upload_by, user_name
                                        )
                                except Exception as e:
                                    current_app.logger.warning(f"记录活动日志失败: {e}")
                            else:
                                current_app.logger.error(f"Word文件处理失败: {doc_id}")
                                
                    except Exception as e:
                        current_app.logger.error(f"Word文件处理异常: {e}")
                
                # 在后台线程中处理Word文件
                import threading
                thread = threading.Thread(target=process_word_file)
                thread.daemon = True
                thread.start()
            else:
                # 非md和Word文件，使用外部API处理
                def start_document_processing():
                    """启动文档处理"""
                    try:
                        with app.app_context():
                            current_app.logger.info(f"开始文档处理: {doc_id}")
                            success = document_processor.process_document(doc_id)
                            
                            if success:
                                current_app.logger.info(f"文档处理完成: {doc_id}")
                                # 知识库创建和上传由document_processor处理，这里不再重复调用
                                
                                # 记录活动日志
                                try:
                                    from services.stats_service import ActivityLogger
                                    doc = Document.query.get(doc_id)
                                    if doc:
                                        user = User.query.get(doc.upload_by)
                                        user_name = user.username if user else 'Unknown'
                                        ActivityLogger.log_document_uploaded(
                                            doc.id, doc.name, project_name_for_log, doc.upload_by, user_name
                                        )
                                except Exception as e:
                                    current_app.logger.warning(f"记录活动日志失败: {e}")
                            else:
                                current_app.logger.error(f"文档处理失败: {doc_id}")
                                
                    except Exception as e:
                        current_app.logger.error(f"文档处理异常: {e}")
                
                # 在后台线程中启动文档处理
                import threading
                thread = threading.Thread(target=start_document_processing)
                thread.daemon = True
                thread.start()
            
            return jsonify(upload_response), 201
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"上传文档失败: {e}")
            return jsonify({'success': False, 'error': '上传文档失败'}), 500
    
    @app.route('/api/documents/<int:document_id>/status', methods=['GET'])
    def get_document_status(document_id):
        """获取文档状态"""
        try:
            document = Document.query.get_or_404(document_id)
            
            return jsonify({
                'success': True,
                'data': {
                    'id': document.id,
                    'status': document.status.value.lower(),
                    'progress': document.progress,
                    'error_message': document.error_message,
                    'processing_started_at': document.processing_started_at.isoformat() if document.processing_started_at else None,
                    'processed_at': document.processed_at.isoformat() if document.processed_at else None,
                    'has_processed_file': bool(document.processed_file_path and os.path.exists(document.processed_file_path)) if document.processed_file_path else False
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"获取文档状态失败: {e}")
            return jsonify({'success': False, 'error': '获取文档状态失败'}), 500
    
    @app.route('/api/documents/<int:document_id>/download', methods=['GET'])
    @token_required
    def download_document(document_id):
        """下载文档"""
        try:
            current_user = request.current_user
            document = Document.query.get_or_404(document_id)

            # 检查用户是否有权限访问此文档
            if current_user.role != UserRole.ADMIN:
                if (document.upload_by != current_user.id and
                    document.project.created_by != current_user.id and
                    document.project.assigned_to != current_user.id):
                    return jsonify({'error': '您没有权限访问此文档'}), 403

            # 检查文件是否存在
            if not os.path.exists(document.file_path):
                return jsonify({'success': False, 'error': '文件不存在'}), 404

            # 记录日志
            log_action(
                user_id=current_user.id,  # 使用当前用户ID
                action='document_download',
                resource_type='document',
                resource_id=document.id,
                details=f'下载文档: {document.name}'
            )

            # 处理中文文件名，优先使用文档名称（通常包含中文）
            # 优先使用document.name（用户设置的名称），如果没有则使用original_filename
            filename = document.name or document.original_filename

            # 确保文件名包含扩展名
            if filename and not os.path.splitext(filename)[1]:
                # 如果没有扩展名，根据文件类型添加
                if document.file_type == 'pdf':
                    filename += '.pdf'
                elif document.file_type == 'excel':
                    filename += '.xlsx'
                elif document.file_type == 'word':
                    filename += '.docx'
                elif document.file_type == 'image':
                    filename += '.jpg'
                elif document.file_type == 'markdown':
                    filename += '.md'
                else:
                    # 尝试从原始路径获取扩展名
                    original_ext = os.path.splitext(document.file_path)[1]
                    if original_ext:
                        filename += original_ext

            # 确保文件名使用UTF-8编码
            try:
                filename = filename.encode('utf-8').decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                # 如果编码失败，使用安全的文件名
                filename = f"document_{document.id}{os.path.splitext(document.file_path)[1]}"

            return send_file(
                document.file_path,
                as_attachment=True,
                download_name=filename
            )

        except Exception as e:
            current_app.logger.error(f"下载文档失败: {e}")
            return jsonify({'success': False, 'error': '下载文档失败'}), 500
    
    @app.route('/api/documents/<int:document_id>/progress', methods=['GET'])
    def get_document_progress(document_id):
        """获取文档处理进度"""
        try:
            document = Document.query.get_or_404(document_id)
            
            # 获取实时进度信息
            from services.document_processor import document_processor
            progress_info = document_processor.get_processing_progress(document_id)
            
            # 如果有错误，返回文档的当前状态
            if 'error' in progress_info:
                progress_info = {
                    'status': document.status.value,
                    'progress_percent': document.progress,
                    'filename': document.filename,
                    'processing_started_at': document.processing_started_at.isoformat() if document.processing_started_at else None,
                    'processed_at': document.processed_at.isoformat() if document.processed_at else None,
                    'processed_file_path': document.processed_file_path
                }
            
            return jsonify({
                'success': True,
                'data': progress_info
            })
            
        except Exception as e:
            current_app.logger.error(f"获取文档处理进度失败: {e}")
            return jsonify({'success': False, 'error': '获取处理进度失败'}), 500
    
    @app.route('/api/documents/<int:document_id>/processed-file', methods=['GET'])
    @token_required
    def download_processed_file(document_id):
        """下载处理后的文件"""
        try:
            current_user = request.current_user
            document = Document.query.get_or_404(document_id)

            # 检查用户是否有权限访问此文档
            if current_user.role != UserRole.ADMIN:
                if (document.upload_by != current_user.id and
                    document.project.created_by != current_user.id and
                    document.project.assigned_to != current_user.id):
                    return jsonify({'error': '您没有权限访问此文档'}), 403

            if not document.processed_file_path or not os.path.exists(document.processed_file_path):
                return jsonify({'success': False, 'error': '处理后的文件不存在'}), 404

            # 记录下载日志
            log_action(
                user_id=current_user.id,  # 使用当前用户ID
                action='processed_document_download',
                resource_type='document',
                resource_id=document.id,
                details=f'下载处理后文档: {document.name}'
            )

            # 构建处理后的文件名，优先使用文档名称（通常包含中文）
            # 优先使用document.name（用户设置的名称），如果没有则使用original_filename
            original_filename = document.name or document.original_filename

            # 确保原始文件名包含扩展名
            if original_filename and not os.path.splitext(original_filename)[1]:
                # 如果没有扩展名，根据文件类型添加
                if document.file_type == 'pdf':
                    original_filename += '.pdf'
                elif document.file_type == 'excel':
                    original_filename += '.xlsx'
                elif document.file_type == 'word':
                    original_filename += '.docx'
                elif document.file_type == 'image':
                    original_filename += '.jpg'
                elif document.file_type == 'markdown':
                    original_filename += '.md'

            try:
                # 确保文件名使用UTF-8编码
                original_filename = original_filename.encode('utf-8').decode('utf-8')
                base_name = os.path.splitext(original_filename)[0]
            except (UnicodeEncodeError, UnicodeDecodeError):
                # 如果编码失败，使用安全的文件名
                base_name = f"document_{document.id}"

            processed_filename = f"{base_name}_processed.md"

            return send_file(
                document.processed_file_path,
                as_attachment=True,
                download_name=processed_filename
            )

        except Exception as e:
            current_app.logger.error(f"下载处理后文档失败: {e}")
            return jsonify({'success': False, 'error': '下载处理后文档失败'}), 500

    @app.route('/api/documents/<int:document_id>/preview', methods=['GET'])
    @token_required
    def preview_document(document_id):
        """预览处理后的文档内容"""
        try:
            current_user = request.current_user
            document = Document.query.get_or_404(document_id)

            # 检查用户是否有权限访问此文档
            if current_user.role != UserRole.ADMIN:
                if (document.upload_by != current_user.id and
                    document.project.created_by != current_user.id and
                    document.project.assigned_to != current_user.id):
                    return jsonify({'error': '您没有权限访问此文档'}), 403

            if not document.processed_file_path or not os.path.exists(document.processed_file_path):
                return jsonify({'success': False, 'error': '处理后的文件不存在，请等待文件处理完成'}), 404

            # 读取处理后的Markdown文件内容
            try:
                with open(document.processed_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # 如果UTF-8解码失败，尝试其他编码
                try:
                    with open(document.processed_file_path, 'r', encoding='gbk') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(document.processed_file_path, 'r', encoding='latin-1') as f:
                        content = f.read()

            # 记录预览日志
            log_action(
                user_id=current_user.id,
                action='document_preview',
                resource_type='document',
                resource_id=document.id,
                details=f'预览文档: {document.name}'
            )

            # 构建用户友好的文件名
            display_name = document.name or document.original_filename
            if display_name and not os.path.splitext(display_name)[1]:
                # 如果没有扩展名，根据文件类型添加
                if document.file_type == 'pdf':
                    display_name += '.pdf'
                elif document.file_type == 'excel':
                    display_name += '.xlsx'
                elif document.file_type == 'word':
                    display_name += '.docx'
                elif document.file_type == 'image':
                    display_name += '.jpg'
                elif document.file_type == 'markdown':
                    display_name += '.md'

            return jsonify({
                'success': True,
                'data': {
                    'content': content,
                    'document_name': document.name,
                    'original_filename': document.original_filename,
                    'display_name': display_name,  # 添加用于显示的文件名
                    'file_type': document.file_type,
                    'processed_at': document.updated_at.isoformat() if document.updated_at else None
                }
            })

        except Exception as e:
            current_app.logger.error(f"预览文档失败: {e}")
            return jsonify({'success': False, 'error': '预览文档失败'}), 500

    @app.route('/api/documents/<int:document_id>', methods=['DELETE'])
    @token_required
    def delete_document(document_id):
        """删除文档"""
        try:
            current_user = request.current_user
            document = Document.query.get_or_404(document_id)

            # 检查用户是否有权限删除此文档
            if current_user.role != UserRole.ADMIN:
                if (document.upload_by != current_user.id and
                    document.project.created_by != current_user.id):
                    return jsonify({'error': '您没有权限删除此文档'}), 403

            document_name = document.name
            file_path = document.file_path

            # 记录日志
            log_action(
                user_id=current_user.id,  # 使用当前用户ID
                action='document_delete',
                resource_type='document',
                resource_id=document.id,
                details=f'删除文档: {document_name}'
            )
            
            # 从知识库中删除文档
            try:
                from services.knowledge_base_service import knowledge_base_service
                knowledge_base_service.delete_document_from_knowledge_base(document.project_id, document.id)
            except Exception as kb_error:
                current_app.logger.warning(f"从知识库删除文档失败: {kb_error}")
                # 继续删除操作，不因为知识库删除失败而中断
            
            # 删除处理后的文档
            from services.document_processor import document_processor
            document_processor.delete_processed_document(document)
            
            # 删除数据库记录
            db.session.delete(document)
            db.session.commit()
            
            # 删除原始文件
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                current_app.logger.warning(f"删除原始文件失败: {e}")
            
            return jsonify({
                'success': True,
                'message': f'文档 "{document_name}" 删除成功'
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"删除文档失败: {e}")
            return jsonify({'success': False, 'error': '删除文档失败'}), 500

    @app.route('/api/documents/<int:document_id>/retry', methods=['POST'])
    @token_required
    def retry_document_processing(document_id):
        """重试文档处理"""
        try:
            current_user = request.current_user

            # 获取文档信息
            document = Document.query.get(document_id)
            if not document:
                return jsonify({'success': False, 'error': '文档不存在'}), 404

            # 检查权限：只有文档上传者、项目创建者、分配者或管理员可以重试
            project = Project.query.get(document.project_id)
            if not project:
                return jsonify({'success': False, 'error': '关联项目不存在'}), 404

            if (current_user.role != UserRole.ADMIN and
                document.upload_by != current_user.id and
                project.created_by != current_user.id and
                project.assigned_to != current_user.id):
                return jsonify({'success': False, 'error': '权限不足'}), 403

            # 检查文档状态：只有失败状态的文档可以重试
            if document.status not in [DocumentStatus.FAILED, DocumentStatus.KB_PARSE_FAILED]:
                return jsonify({
                    'success': False,
                    'error': f'文档状态为"{document.status.value}"，无法重试。只有失败状态的文档可以重试。'
                }), 400

            # 重置文档状态和相关字段
            document.status = DocumentStatus.PROCESSING
            document.processed_file_path = None
            document.processing_progress = 0
            document.error_message = None
            document.rag_document_id = None

            # 删除processed文件夹中的对应文件（如果存在）
            if document.processed_file_path and os.path.exists(document.processed_file_path):
                try:
                    os.remove(document.processed_file_path)
                    current_app.logger.info(f"删除旧的processed文件: {document.processed_file_path}")
                except Exception as e:
                    current_app.logger.warning(f"删除旧的processed文件失败: {e}")

            # 提交数据库更改
            db.session.commit()

            # 启动文档重新处理（异步）
            from services.document_processor import DocumentProcessor
            processor = DocumentProcessor()

            # 获取当前应用实例，用于传递给异步线程
            app = current_app._get_current_object()
            processor.process_document_async(document.id, app)

            # 记录操作日志
            log_action(
                user_id=current_user.id,
                action='retry_document_processing',
                resource_type='document',
                resource_id=document_id,
                details=f'重试处理文档"{document.name}"'
            )

            return jsonify({
                'success': True,
                'message': f'文档"{document.name}"重试处理任务已启动'
            })

        except Exception as e:
            current_app.logger.error(f"重试文档处理API错误: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'error': '服务器内部错误'}), 500

def _check_and_create_knowledge_base(doc_id, project_name):
    """
    检查并创建知识库
    在项目首次上传文件并解析完成后自动创建知识库
    
    Args:
        doc_id: 文档ID
        project_name: 项目名称
    """
    try:
        from services.knowledge_base_service import knowledge_base_service
        
        # 获取文档信息
        document = Document.query.get(doc_id)
        if not document:
            current_app.logger.error(f"文档不存在: {doc_id}")
            return
        
        project = document.project
        if not project:
            current_app.logger.error(f"项目不存在: {doc_id}")
            return
            
        # 检查项目是否已经有知识库
        if project.dataset_id:
            current_app.logger.info(f"项目已有知识库: {project.name}, Dataset ID: {project.dataset_id}")
            # 如果已有知识库，直接上传当前文档
            knowledge_base_service.upload_document_to_knowledge_base(project.id, document.id)
            return
        
        current_app.logger.info(f"开始为项目创建知识库: {project.name}")
        
        # 调用知识库服务创建知识库
        dataset_id = knowledge_base_service.create_knowledge_base_for_project(
            project_id=project.id,
            user_id=document.upload_by
        )
        
        if dataset_id:
            current_app.logger.info(f"知识库创建成功: {project.knowledge_base_name}, Dataset ID: {dataset_id}")
            
            # 记录日志
            log_action(
                user_id=document.upload_by,
                action='knowledge_base_create',
                resource_type='project',
                resource_id=project.id,
                details=f'自动创建知识库: {project.knowledge_base_name}'
            )
            
            # 将当前文档上传到知识库
            knowledge_base_service.upload_document_to_knowledge_base(project.id, document.id)
            
        else:
            current_app.logger.error(f"创建知识库失败: {project.name}")
            
    except Exception as e:
        current_app.logger.error(f"检查并创建知识库失败: {e}")
        db.session.rollback()

def _upload_document_to_knowledge_base(document, knowledge_base):
    """
    将文档上传到知识库
    
    Args:
        document: 文档对象
        knowledge_base: 知识库对象 (已废弃，改用project.dataset_id)
    """
    try:
        from services.knowledge_base_service import knowledge_base_service
        
        # 检查是否有处理后的文件
        if not document.processed_file_path or not os.path.exists(document.processed_file_path):
            current_app.logger.warning(f"文档没有处理后的文件: {document.id}")
            return
            
        current_app.logger.info(f"开始上传文档到知识库: {document.name}")
        
        # 直接使用知识库服务上传文档
        success = knowledge_base_service.upload_document_to_knowledge_base(
            project_id=document.project_id,
            document_id=document.id
        )
        
        if success:
            current_app.logger.info(f"文档上传到知识库成功: {document.name}")
        else:
            current_app.logger.error(f"上传文档到知识库失败: {document.name}")
            
    except Exception as e:
        current_app.logger.error(f"上传文档到知识库失败: {e}")
        db.session.rollback()