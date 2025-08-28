"""
统计服务模块
提供仪表板统计、趋势分析等功能
"""

from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
from database import db
from db_models import (
    Project, Document, User, AnalysisReport,
    DashboardStats, ActivityLog, ProjectStatus, DocumentStatus, RiskLevel
)


class StatsService:
    """统计服务类"""

    @staticmethod
    def get_dashboard_stats():
        """获取仪表板统计数据"""
        try:
            # 获取今天的统计数据，如果不存在则实时计算
            today = date.today()
            cached_stats = DashboardStats.query.filter_by(date=today).first()
            
            if cached_stats:
                # 如果缓存数据存在且是今天的，直接返回
                return StatsService._format_dashboard_response(cached_stats.to_dict())
            
            # 实时计算统计数据
            stats_data = StatsService._calculate_current_stats()
            
            # 保存到缓存表
            StatsService._save_daily_stats(today, stats_data)
            
            return StatsService._format_dashboard_response(stats_data)
            
        except Exception as e:
            print(f"获取仪表板统计失败: {e}")
            return None

    @staticmethod
    def _calculate_current_stats():
        """计算当前统计数据"""
        # 项目统计
        total_projects = Project.query.count()
        completed_projects = Project.query.filter_by(status=ProjectStatus.COMPLETED).count()
        processing_projects = Project.query.filter_by(status=ProjectStatus.PROCESSING).count()
        collecting_projects = Project.query.filter_by(status=ProjectStatus.COLLECTING).count()

        # 文档统计
        total_documents = Document.query.count()
        completed_documents = Document.query.filter_by(status=DocumentStatus.COMPLETED).count()
        processing_documents = Document.query.filter_by(status=DocumentStatus.PROCESSING).count()
        failed_documents = Document.query.filter_by(status=DocumentStatus.FAILED).count()

        # 用户统计
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()

        # 平均分数
        avg_score_result = db.session.query(func.avg(Project.score)).scalar()
        average_score = round(avg_score_result, 1) if avg_score_result else 0.0

        # 风险等级统计
        high_risk_projects = Project.query.filter_by(risk_level=RiskLevel.HIGH).count()
        medium_risk_projects = Project.query.filter_by(risk_level=RiskLevel.MEDIUM).count()
        low_risk_projects = Project.query.filter_by(risk_level=RiskLevel.LOW).count()

        return {
            'total_projects': total_projects,
            'completed_projects': completed_projects,
            'processing_projects': processing_projects,
            'collecting_projects': collecting_projects,
            'total_documents': total_documents,
            'completed_documents': completed_documents,
            'processing_documents': processing_documents,
            'failed_documents': failed_documents,
            'total_users': total_users,
            'active_users': active_users,
            'average_score': average_score,
            'high_risk_projects': high_risk_projects,
            'medium_risk_projects': medium_risk_projects,
            'low_risk_projects': low_risk_projects
        }

    @staticmethod
    def _save_daily_stats(date_obj, stats_data):
        """保存每日统计数据"""
        try:
            # 检查是否已存在
            existing = DashboardStats.query.filter_by(date=date_obj).first()
            
            if existing:
                # 更新现有记录
                for key, value in stats_data.items():
                    setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
            else:
                # 创建新记录
                new_stats = DashboardStats(
                    date=date_obj,
                    **stats_data
                )
                db.session.add(new_stats)
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            print(f"保存统计数据失败: {e}")

    @staticmethod
    def _format_dashboard_response(stats_data):
        """格式化仪表板响应数据"""
        # 计算完成率
        projects_completion_rate = 0
        if stats_data['total_projects'] > 0:
            projects_completion_rate = round(
                (stats_data['completed_projects'] / stats_data['total_projects']) * 100, 1
            )

        documents_completion_rate = 0
        if stats_data['total_documents'] > 0:
            documents_completion_rate = round(
                (stats_data['completed_documents'] / stats_data['total_documents']) * 100, 1
            )

        return {
            'projects': {
                'total': stats_data['total_projects'],
                'completed': stats_data['completed_projects'],
                'processing': stats_data['processing_projects'],
                'collecting': stats_data['collecting_projects'],
                'archived': stats_data['archived_projects'],
                'completion_rate': projects_completion_rate
            },
            'documents': {
                'total': stats_data['total_documents'],
                'completed': stats_data['completed_documents'],
                'processing': stats_data['processing_documents'],
                'failed': stats_data['failed_documents'],
                'completion_rate': documents_completion_rate
            },
            'users': {
                'total': stats_data['total_users'],
                'active': stats_data['active_users']
            },
            'risk_analysis': {
                'high_risk': stats_data['high_risk_projects'],
                'medium_risk': stats_data['medium_risk_projects'],
                'low_risk': stats_data['low_risk_projects']
            },
            'average_score': stats_data['average_score']
        }

    @staticmethod
    def get_trends_data(period='month', months=6):
        """获取趋势数据"""
        try:
            end_date = date.today()
            
            if period == 'month':
                # 获取过去N个月的数据
                start_date = end_date - timedelta(days=months * 30)
                
                # 按月分组查询
                trends = db.session.query(
                    func.date_format(DashboardStats.date, '%Y-%m').label('period'),
                    func.avg(DashboardStats.total_projects).label('total_projects'),
                    func.avg(DashboardStats.high_risk_projects).label('risk_projects'),
                    func.avg(DashboardStats.low_risk_projects + DashboardStats.medium_risk_projects).label('normal_projects'),
                    func.avg(DashboardStats.average_score).label('average_score')
                ).filter(
                    DashboardStats.date >= start_date
                ).group_by(
                    func.date_format(DashboardStats.date, '%Y-%m')
                ).order_by(
                    func.date_format(DashboardStats.date, '%Y-%m')
                ).all()

                # 格式化数据
                formatted_trends = []
                for trend in trends:
                    formatted_trends.append({
                        'period': trend.period,
                        'month': f"{trend.period.split('-')[1]}月",
                        'total_projects': int(trend.total_projects or 0),
                        'risk_projects': int(trend.risk_projects or 0),
                        'normal_projects': int(trend.normal_projects or 0),
                        'average_score': round(trend.average_score or 0, 1)
                    })

                return formatted_trends

        except Exception as e:
            print(f"获取趋势数据失败: {e}")
            return []

    @staticmethod
    def get_recent_activities(limit=10):
        """获取最近活动"""
        try:
            activities = ActivityLog.query.order_by(
                ActivityLog.created_at.desc()
            ).limit(limit).all()

            return [activity.to_dict() for activity in activities]

        except Exception as e:
            print(f"获取最近活动失败: {e}")
            return []

    @staticmethod
    def log_activity(activity_type, title, description=None, user_id=None,
                    resource_type=None, resource_id=None, activity_metadata=None):
        """记录活动日志"""
        try:
            activity = ActivityLog(
                type=activity_type,
                title=title,
                description=description,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                activity_metadata=activity_metadata
            )
            
            db.session.add(activity)
            db.session.commit()
            
            return True

        except Exception as e:
            db.session.rollback()
            print(f"记录活动日志失败: {e}")
            return False

    @staticmethod
    def update_daily_stats():
        """更新每日统计数据 - 用于定时任务"""
        today = date.today()
        stats_data = StatsService._calculate_current_stats()
        StatsService._save_daily_stats(today, stats_data)
        return True


class ActivityLogger:
    """活动日志记录器"""

    @staticmethod
    def log_user_login(user_id, user_name):
        """记录用户登录"""
        StatsService.log_activity(
            activity_type='user_login',
            title=f'{user_name} 登录系统',
            user_id=user_id,
            resource_type='user',
            resource_id=user_id
        )

    @staticmethod
    def log_project_created(project_id, project_name, user_id, user_name):
        """记录项目创建"""
        StatsService.log_activity(
            activity_type='project_created',
            title=f'创建了新项目：{project_name}',
            description=f'项目ID: {project_id}',
            user_id=user_id,
            resource_type='project',
            resource_id=project_id,
            activity_metadata={'project_name': project_name, 'user_name': user_name}
        )

    @staticmethod
    def log_document_uploaded(document_id, document_name, project_name, user_id, user_name):
        """记录文档上传"""
        StatsService.log_activity(
            activity_type='document_uploaded',
            title=f'{project_name} 文档上传完成',
            description=f'文件: {document_name}',
            user_id=user_id,
            resource_type='document',
            resource_id=document_id,
            activity_metadata={'document_name': document_name, 'project_name': project_name}
        )

    @staticmethod
    def log_report_generated(project_id, project_name, user_id, user_name, score=None):
        """记录报告生成"""
        title = f'{project_name} 征信报告已生成'
        description = f'项目ID: {project_id}'
        if score:
            description += f', 评分: {score}'
            
        StatsService.log_activity(
            activity_type='report_generated',
            title=title,
            description=description,
            user_id=user_id,
            resource_type='project',
            resource_id=project_id,
            activity_metadata={'project_name': project_name, 'score': score}
        )
