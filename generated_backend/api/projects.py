"""
项目管理API
"""

from flask import request, jsonify, current_app
from sqlalchemy import or_, and_
from datetime import datetime

from database import db
from db_models import Project, User, ProjectMember, Document, SystemLog
from db_models import ProjectType, ProjectStatus, Priority, RiskLevel, ProjectMemberRole
from utils import validate_request, log_action

def register_project_routes(app):
    """注册项目相关路由"""
    
    @app.route('/api/projects', methods=['GET'])
    def get_projects():
        """获取项目列表"""
        try:
            # 获取查询参数
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 20, type=int)
            search = request.args.get('search', '')
            project_type = request.args.get('type', '')
            status = request.args.get('status', '')

            # 构建查询
            query = Project.query

            # 搜索过滤
            if search and search not in ['undefined', 'null', '']:
                query = query.filter(
                    or_(
                        Project.name.contains(search),
                        Project.description.contains(search)
                    )
                )

            # 类型过滤
            if project_type and project_type not in ['undefined', 'null', '']:
                try:
                    # 将字符串转换为枚举值（枚举值是小写）
                    type_enum = ProjectType(project_type.lower())
                    query = query.filter(Project.type == type_enum)
                except ValueError:
                    # 如果转换失败，记录日志但不过滤
                    current_app.logger.warning(f"Invalid project type: {project_type}")

            # 状态过滤
            if status and status not in ['undefined', 'null', '']:
                try:
                    # 将字符串转换为枚举值（枚举值是小写）
                    status_enum = ProjectStatus(status.lower())
                    query = query.filter(Project.status == status_enum)
                except ValueError:
                    # 如果转换失败，记录日志但不过滤
                    current_app.logger.warning(f"Invalid project status: {status}")

            # 分页
            total = query.count()
            projects = query.order_by(Project.updated_at.desc()).offset((page - 1) * limit).limit(limit).all()

            # 转换为字典列表，使用简化的格式与mock保持一致
            projects_data = []
            for project in projects:
                project_dict = {
                    'id': project.id,
                    'name': project.name,
                    'type': project.type.value.lower(),
                    'status': project.status.value.lower(),
                    'score': project.score,
                    'riskLevel': project.risk_level.value.lower(),
                    'lastUpdate': project.updated_at.strftime('%Y-%m-%d'),
                    'documents': len(list(project.documents)),
                    'progress': project.progress,
                    # 知识库相关字段
                    'dataset_id': project.dataset_id,
                    'knowledge_base_name': project.knowledge_base_name
                }
                projects_data.append(project_dict)

            # 直接返回项目数组，与mock格式完全一致
            return jsonify(projects_data)

        except Exception as e:
            current_app.logger.error(f"获取项目列表失败: {e}")
            return jsonify({'error': '获取项目列表失败'}), 500
    
    @app.route('/api/projects/<int:project_id>', methods=['GET'])
    def get_project(project_id):
        """获取项目详情"""
        try:
            project = Project.query.get_or_404(project_id)

            # 使用完整的格式，包含扩展信息
            project_data = {
                'id': project.id,
                'name': project.name,
                'type': project.type.value.lower(),
                'status': project.status.value.lower(),
                'score': project.score,
                'riskLevel': project.risk_level.value.lower(),
                'lastUpdate': project.updated_at.strftime('%Y-%m-%d'),
                'documents': len(list(project.documents)),
                'progress': project.progress,
                # 知识库相关字段
                'dataset_id': project.dataset_id,
                'knowledge_base_name': project.knowledge_base_name,
                # 添加扩展信息
                'companyInfo': project.company_info,
                'personalInfo': project.personal_info,
                'financialData': project.financial_data
            }

            # 直接返回项目数据
            return jsonify(project_data)

        except Exception as e:
            current_app.logger.error(f"获取项目详情失败: {e}")
            return jsonify({'error': '获取项目详情失败'}), 500
    
    @app.route('/api/projects', methods=['POST'])
    def create_project():
        """创建项目"""
        try:
            import uuid
            data = request.get_json()
            
            # 验证必需字段
            required_fields = ['name', 'type']
            for field in required_fields:
                if field not in data:
                    return jsonify({'success': False, 'error': f'缺少必需字段: {field}'}), 400
            
            # 验证项目类型
            if data['type'] not in ['enterprise', 'individual']:
                return jsonify({'success': False, 'error': '无效的项目类型'}), 400
            
            # 创建项目
            project = Project(
                name=data['name'],
                folder_uuid=str(uuid.uuid4()),  # 生成唯一的文件夹UUID
                type=ProjectType(data['type']),
                description=data.get('description', ''),
                category=data.get('category', ''),
                priority=Priority(data.get('priority', 'medium')),
                created_by=1,  # TODO: 从JWT token获取用户ID
                assigned_to=data.get('assigned_to')
            )
            
            db.session.add(project)
            db.session.flush()  # 获取项目ID
            
            # 创建项目成员关系（创建者自动成为owner）
            member = ProjectMember(
                project_id=project.id,
                user_id=project.created_by,
                role=ProjectMemberRole.OWNER
            )
            db.session.add(member)
            
            db.session.commit()
            
            # 记录日志
            log_action(
                user_id=project.created_by,
                action='project_create',
                resource_type='project',
                resource_id=project.id,
                details=f'创建项目: {project.name}'
            )

            # 记录活动日志
            try:
                from services.stats_service import ActivityLogger
                user = User.query.get(project.created_by)
                user_name = user.full_name if user else 'Unknown'
                ActivityLogger.log_project_created(
                    project.id, project.name, project.created_by, user_name
                )
            except Exception as e:
                current_app.logger.warning(f"记录活动日志失败: {e}")
            
            # 返回完整的项目数据
            project_data = {
                'id': project.id,
                'name': project.name,
                'folder_uuid': project.folder_uuid,
                'type': project.type.value.lower(),
                'status': project.status.value.lower(),
                'description': project.description,
                'category': project.category,
                'priority': project.priority.value.lower(),
                'score': project.score,
                'riskLevel': project.risk_level.value.lower(),
                'progress': project.progress,
                'createdBy': project.created_by,
                'assignedTo': project.assigned_to,
                'createdAt': project.created_at.isoformat(),
                'updatedAt': project.updated_at.isoformat(),
                'lastUpdate': project.updated_at.strftime('%Y-%m-%d'),
                'documents': len(list(project.documents))
            }

            return jsonify({
                'success': True,
                'message': '项目创建成功',
                'data': project_data
            }), 201
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建项目失败: {e}")
            return jsonify({'success': False, 'error': '创建项目失败'}), 500
    
    @app.route('/api/projects/<int:project_id>', methods=['PUT'])
    def update_project(project_id):
        """更新项目"""
        try:
            project = Project.query.get_or_404(project_id)
            data = request.get_json()
            
            # 更新字段
            if 'name' in data:
                project.name = data['name']
            if 'description' in data:
                project.description = data['description']
            if 'category' in data:
                project.category = data['category']
            if 'priority' in data and data['priority'] in ['low', 'medium', 'high']:
                project.priority = Priority(data['priority'])
            if 'status' in data and data['status'] in ['collecting', 'processing', 'completed', 'archived']:
                project.status = ProjectStatus(data['status'])
            if 'score' in data:
                project.score = data['score']
            if 'risk_level' in data and data['risk_level'] in ['low', 'medium', 'high']:
                project.risk_level = RiskLevel(data['risk_level'])
            if 'progress' in data:
                project.progress = data['progress']
            if 'assigned_to' in data:
                project.assigned_to = data['assigned_to']
            
            project.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # 记录日志
            log_action(
                user_id=1,  # TODO: 从JWT token获取用户ID
                action='project_update',
                resource_type='project',
                resource_id=project.id,
                details=f'更新项目: {project.name}'
            )
            
            return jsonify({
                'success': True,
                'data': project.to_dict(),
                'message': '项目更新成功'
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新项目失败: {e}")
            return jsonify({'success': False, 'error': '更新项目失败'}), 500
    
    @app.route('/api/projects/<int:project_id>', methods=['DELETE'])
    def delete_project(project_id):
        """删除项目"""
        try:
            # 检查项目是否存在
            project = Project.query.get(project_id)
            if not project:
                return jsonify({'success': False, 'error': '项目不存在'}), 404

            project_name = project.name
            current_app.logger.info(f"开始删除项目: {project_name} (ID: {project_id})")

            # 先记录日志（在删除之前）
            try:
                log_action(
                    user_id=1,  # TODO: 从JWT token获取用户ID
                    action='project_delete',
                    resource_type='project',
                    resource_id=project.id,
                    details=f'删除项目: {project_name}'
                )
            except Exception as log_error:
                current_app.logger.warning(f"记录删除日志失败: {log_error}")
                # 继续删除操作，不因为日志失败而中断

            # 删除项目相关的知识库
            try:
                from services.knowledge_base_service import knowledge_base_service
                knowledge_base_service.delete_knowledge_base(project.id)
            except Exception as kb_error:
                current_app.logger.warning(f"删除知识库失败: {kb_error}")
                # 继续删除操作，不因为知识库删除失败而中断

            # 删除项目相关的所有文档文件
            from services.document_processor import document_processor
            document_processor.delete_project_documents(project)

            # 删除数据库记录（依赖级联删除）
            db.session.delete(project)
            db.session.commit()

            current_app.logger.info(f"项目删除成功: {project_name}")

            return jsonify({
                'success': True,
                'message': f'项目 "{project_name}" 删除成功'
            })

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"删除项目失败 (ID: {project_id}): {str(e)}")
            import traceback
            current_app.logger.error(f"错误详情: {traceback.format_exc()}")

            # 返回更详细的错误信息
            error_message = '删除项目失败'
            if 'FOREIGN KEY constraint failed' in str(e):
                error_message = '无法删除项目，存在关联数据'
            elif 'IntegrityError' in str(e):
                error_message = '数据完整性错误，无法删除项目'

            return jsonify({'success': False, 'error': error_message}), 500
