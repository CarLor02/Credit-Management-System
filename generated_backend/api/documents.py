"""
文档管理API
"""

import os
import uuid
from flask import request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from sqlalchemy import or_

from database import db
from db_models import Document, Project, DocumentStatus, User
from utils import validate_request, log_action

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
    elif ext in ['doc', 'docx']:
        return 'word'
    elif ext in ['jpg', 'jpeg', 'png']:
        return 'image'
    elif ext in ['md']:
        return 'markdown'
    else:
        return 'other'

def register_document_routes(app):
    """注册文档相关路由"""
    
    @app.route('/api/documents', methods=['GET'])
    def get_documents():
        """获取文档列表"""
        try:
            # 获取查询参数
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 20, type=int)
            search = request.args.get('search', '')
            project_id = request.args.get('project', type=int)
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
            if status and status in ['uploading', 'processing', 'completed', 'failed']:
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
                doc_dict = {
                    'id': doc.id,
                    'name': doc.name,
                    'project': doc.project.name if doc.project else '',
                    'type': doc.get_frontend_file_type(),
                    'size': doc.format_file_size(),
                    'status': doc.status.value.lower(),
                    'uploadTime': doc.created_at.strftime('%Y-%m-%d %H:%M'),
                    'progress': doc.progress
                }
                documents_data.append(doc_dict)

            # 直接返回文档数组，与mock格式完全一致
            return jsonify(documents_data)
            
        except Exception as e:
            current_app.logger.error(f"获取文档列表失败: {e}")
            return jsonify({'success': False, 'error': '获取文档列表失败'}), 500
    
    @app.route('/api/documents/<int:document_id>', methods=['GET'])
    def get_document(document_id):
        """获取文档详情"""
        try:
            document = Document.query.get_or_404(document_id)

            # 使用简化的格式与mock保持一致
            document_data = {
                'id': document.id,
                'name': document.name,
                'project': document.project.name if document.project else '',
                'type': document.get_frontend_file_type(),
                'size': document.format_file_size(),
                'status': document.status.value.lower(),
                'uploadTime': document.created_at.strftime('%Y-%m-%d %H:%M'),
                'progress': document.progress
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
            # 检查文件
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': '没有文件被上传'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': '没有选择文件'}), 400
            
            # 检查文件类型
            if not allowed_file(file.filename):
                return jsonify({'success': False, 'error': '不支持的文件类型'}), 400
            
            # 获取其他参数
            project_name = request.form.get('project')
            document_name = request.form.get('name', file.filename)
            
            if not project_name:
                return jsonify({'success': False, 'error': '缺少项目信息'}), 400
            
            # 查找项目
            project = Project.query.filter_by(name=project_name).first()
            if not project:
                return jsonify({'success': False, 'error': '项目不存在'}), 404
            
            # 生成安全的文件名
            filename = secure_filename(file.filename)
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
            file_type = get_file_type(filename)
            
            # 创建文档记录 - 初始状态为UPLOADING
            document = Document(
                name=document_name,
                original_filename=filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
                mime_type=file.mimetype,
                project_id=project.id,
                status=DocumentStatus.UPLOADING,  # 初始状态为上传中
                progress=0,
                upload_by=1  # TODO: 从JWT token获取用户ID
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
                    'type': document.get_frontend_file_type(),
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
            
            # 触发OCR处理或md文件处理
            from services.document_processor import document_processor
            
            # 保存文档ID和项目名，避免会话问题
            doc_id = document.id
            project_name_for_log = project.name
            
            # 检查是否为md文件
            if file_type == 'markdown':
                # md文件直接处理，不需要OCR
                def process_md_file():
                    """处理md文件"""
                    try:
                        with app.app_context():
                            current_app.logger.info(f"开始处理md文件: {doc_id}")
                            success = document_processor.process_markdown_file(doc_id)
                            
                            if success:
                                current_app.logger.info(f"md文件处理完成: {doc_id}")
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
            else:
                # 非md文件，使用OCR处理
                def start_ocr_processing():
                    """启动OCR处理"""
                    try:
                        with app.app_context():
                            current_app.logger.info(f"开始OCR处理文档: {doc_id}")
                            success = document_processor.process_document(doc_id)
                            
                            if success:
                                current_app.logger.info(f"OCR处理完成: {doc_id}")
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
                                current_app.logger.error(f"OCR处理失败: {doc_id}")
                                
                    except Exception as e:
                        current_app.logger.error(f"OCR处理异常: {e}")
                
                # 在后台线程中启动OCR处理
                import threading
                thread = threading.Thread(target=start_ocr_processing)
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
    def download_document(document_id):
        """下载文档"""
        try:
            document = Document.query.get_or_404(document_id)
            
            # 检查文件是否存在
            if not os.path.exists(document.file_path):
                return jsonify({'success': False, 'error': '文件不存在'}), 404
            
            # 记录日志
            log_action(
                user_id=1,  # TODO: 从JWT token获取用户ID
                action='document_download',
                resource_type='document',
                resource_id=document.id,
                details=f'下载文档: {document.name}'
            )
            
            return send_file(
                document.file_path,
                as_attachment=True,
                download_name=document.original_filename
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
    def download_processed_file(document_id):
        """下载处理后的文件"""
        try:
            document = Document.query.get_or_404(document_id)
            
            if not document.processed_file_path or not os.path.exists(document.processed_file_path):
                return jsonify({'success': False, 'error': '处理后的文件不存在'}), 404
            
            # 记录下载日志
            log_action(
                user_id=1,  # TODO: 从JWT token获取用户ID
                action='processed_document_download',
                resource_type='document',
                resource_id=document.id,
                details=f'下载处理后文档: {document.name}'
            )
            
            # 构建处理后的文件名
            base_name = os.path.splitext(document.original_filename)[0]
            processed_filename = f"{base_name}_processed.md"
            
            return send_file(
                document.processed_file_path,
                as_attachment=True,
                download_name=processed_filename
            )
            
        except Exception as e:
            current_app.logger.error(f"下载处理后文档失败: {e}")
            return jsonify({'success': False, 'error': '下载处理后文档失败'}), 500

    @app.route('/api/documents/<int:document_id>', methods=['DELETE'])
    def delete_document(document_id):
        """删除文档"""
        try:
            document = Document.query.get_or_404(document_id)
            document_name = document.name
            file_path = document.file_path
            
            # 记录日志
            log_action(
                user_id=1,  # TODO: 从JWT token获取用户ID
                action='document_delete',
                resource_type='document',
                resource_id=document.id,
                details=f'删除文档: {document_name}'
            )
            
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
