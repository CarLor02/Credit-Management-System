"""
项目详情API
包括财务分析、经营状况、时间轴等详细信息
"""

from flask import request, jsonify, current_app
from sqlalchemy import desc
from datetime import datetime, date

from database import db
from db_models import (
    Project, FinancialAnalysis, BusinessStatus, ProjectTimeline,
    ProjectType, EventType, EventStatus, Priority
)
from utils import validate_request, log_action

def register_project_detail_routes(app):
    """注册项目详情相关路由"""
    
    @app.route('/api/projects/<int:project_id>/financial', methods=['GET'])
    def get_project_financial(project_id):
        """获取项目财务分析数据"""
        try:
            # 验证项目是否存在
            project = Project.query.get_or_404(project_id)
            
            # 只有企业项目才有财务分析
            if project.type != ProjectType.ENTERPRISE:
                return jsonify({
                    'success': False,
                    'error': '个人项目没有财务分析数据'
                }), 400
            
            # 获取财务分析数据，按年份降序排列
            financial_analyses = FinancialAnalysis.query.filter_by(
                project_id=project_id
            ).order_by(desc(FinancialAnalysis.analysis_year)).all()
            
            if not financial_analyses:
                return jsonify({
                    'success': True,
                    'data': [],
                    'message': '暂无财务分析数据'
                })
            
            # 转换为字典格式
            data = [analysis.to_dict() for analysis in financial_analyses]
            
            return jsonify({
                'success': True,
                'data': data
            })
            
        except Exception as e:
            current_app.logger.error(f"获取项目财务分析失败: {e}")
            return jsonify({
                'success': False,
                'error': '获取财务分析数据失败'
            }), 500
    
    @app.route('/api/projects/<int:project_id>/business-status', methods=['GET'])
    def get_project_business_status(project_id):
        """获取项目经营状况数据"""
        try:
            # 验证项目是否存在
            project = Project.query.get_or_404(project_id)
            
            # 只有企业项目才有经营状况
            if project.type != ProjectType.ENTERPRISE:
                return jsonify({
                    'success': False,
                    'error': '个人项目没有经营状况数据'
                }), 400
            
            # 获取最新的经营状况数据
            business_status = BusinessStatus.query.filter_by(
                project_id=project_id
            ).order_by(desc(BusinessStatus.evaluation_date)).first()
            
            if not business_status:
                return jsonify({
                    'success': True,
                    'data': None,
                    'message': '暂无经营状况数据'
                })
            
            return jsonify({
                'success': True,
                'data': business_status.to_dict()
            })
            
        except Exception as e:
            current_app.logger.error(f"获取项目经营状况失败: {e}")
            return jsonify({
                'success': False,
                'error': '获取经营状况数据失败'
            }), 500
    
    @app.route('/api/projects/<int:project_id>/timeline', methods=['GET'])
    def get_project_timeline(project_id):
        """获取项目时间轴数据"""
        try:
            # 验证项目是否存在
            project = Project.query.get_or_404(project_id)
            
            # 获取查询参数
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)
            status = request.args.get('status')  # 可选的状态过滤
            
            # 构建查询
            query = ProjectTimeline.query.filter_by(project_id=project_id)
            
            # 状态过滤
            if status:
                query = query.filter(ProjectTimeline.status == status)
            
            # 按事件日期降序排列
            query = query.order_by(desc(ProjectTimeline.event_date))
            
            # 分页
            timeline_events = query.offset(offset).limit(limit).all()
            total_count = query.count()
            
            # 转换为字典格式
            data = [event.to_dict() for event in timeline_events]
            
            return jsonify({
                'success': True,
                'data': data,
                'pagination': {
                    'total': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': offset + limit < total_count
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"获取项目时间轴失败: {e}")
            return jsonify({
                'success': False,
                'error': '获取时间轴数据失败'
            }), 500
    
    @app.route('/api/projects/<int:project_id>/timeline', methods=['POST'])
    def create_timeline_event(project_id):
        """创建时间轴事件"""
        try:
            # 验证项目是否存在
            project = Project.query.get_or_404(project_id)
            
            data = request.get_json()
            
            # 验证必需字段
            required_fields = ['event_title', 'event_date']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'缺少必需字段: {field}'
                    }), 400
            
            # 转换日期字符串为date对象
            event_date = datetime.strptime(data['event_date'], '%Y-%m-%d').date()
            planned_date = None
            if data.get('planned_date'):
                planned_date = datetime.strptime(data['planned_date'], '%Y-%m-%d').date()

            # 创建时间轴事件
            timeline_event = ProjectTimeline(
                project_id=project_id,
                event_title=data['event_title'],
                event_description=data.get('event_description'),
                event_type=data.get('event_type', 'other'),
                status=data.get('status', 'pending'),
                priority=data.get('priority', 'medium'),
                event_date=event_date,
                planned_date=planned_date,
                progress=data.get('progress', 0),
                created_by=1  # TODO: 从JWT token获取用户ID
            )
            
            db.session.add(timeline_event)
            db.session.commit()
            
            # 记录日志
            log_action(
                user_id=1,  # TODO: 从JWT token获取用户ID
                action='timeline_create',
                resource_type='timeline',
                resource_id=timeline_event.id,
                details=f'创建时间轴事件: {timeline_event.event_title}'
            )
            
            return jsonify({
                'success': True,
                'data': timeline_event.to_dict(),
                'message': '时间轴事件创建成功'
            }), 201
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建时间轴事件失败: {e}")
            return jsonify({
                'success': False,
                'error': '创建时间轴事件失败'
            }), 500
    
    @app.route('/api/projects/<int:project_id>/timeline/<int:event_id>', methods=['PUT'])
    def update_timeline_event(project_id, event_id):
        """更新时间轴事件"""
        try:
            # 验证项目和事件是否存在
            project = Project.query.get_or_404(project_id)
            timeline_event = ProjectTimeline.query.filter_by(
                id=event_id,
                project_id=project_id
            ).first_or_404()
            
            data = request.get_json()
            
            # 更新字段
            if 'event_title' in data:
                timeline_event.event_title = data['event_title']
            if 'event_description' in data:
                timeline_event.event_description = data['event_description']
            if 'status' in data:
                timeline_event.status = data['status']
            if 'progress' in data:
                timeline_event.progress = data['progress']
            if 'completed_date' in data:
                if data['completed_date']:
                    timeline_event.completed_date = datetime.strptime(data['completed_date'], '%Y-%m-%d').date()
                else:
                    timeline_event.completed_date = None
            
            db.session.commit()
            
            # 记录日志
            log_action(
                user_id=1,  # TODO: 从JWT token获取用户ID
                action='timeline_update',
                resource_type='timeline',
                resource_id=timeline_event.id,
                details=f'更新时间轴事件: {timeline_event.event_title}'
            )
            
            return jsonify({
                'success': True,
                'data': timeline_event.to_dict(),
                'message': '时间轴事件更新成功'
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新时间轴事件失败: {e}")
            return jsonify({
                'success': False,
                'error': '更新时间轴事件失败'
            }), 500
    
    @app.route('/api/projects/<int:project_id>/summary', methods=['GET'])
    def get_project_detail_summary(project_id):
        """获取项目详情摘要（用于概览页面）"""
        try:
            # 验证项目是否存在
            project = Project.query.get_or_404(project_id)
            
            summary = {
                'project': project.to_dict(),
                'has_financial_data': False,
                'has_business_status': False,
                'timeline_events_count': 0,
                'latest_events': []
            }
            
            # 检查是否有财务数据
            if project.type == ProjectType.ENTERPRISE:
                financial_count = FinancialAnalysis.query.filter_by(project_id=project_id).count()
                business_count = BusinessStatus.query.filter_by(project_id=project_id).count()
                
                summary['has_financial_data'] = financial_count > 0
                summary['has_business_status'] = business_count > 0
            
            # 获取时间轴统计
            timeline_count = ProjectTimeline.query.filter_by(project_id=project_id).count()
            summary['timeline_events_count'] = timeline_count
            
            # 获取最近的时间轴事件
            latest_events = ProjectTimeline.query.filter_by(
                project_id=project_id
            ).order_by(desc(ProjectTimeline.event_date)).limit(5).all()
            
            summary['latest_events'] = [event.to_dict() for event in latest_events]
            
            return jsonify({
                'success': True,
                'data': summary
            })
            
        except Exception as e:
            current_app.logger.error(f"获取项目详情摘要失败: {e}")
            return jsonify({
                'success': False,
                'error': '获取项目详情摘要失败'
            }), 500
