"""
数据库迁移脚本：添加统计相关表
包括：dashboard_stats 和 activity_logs 表
"""

import sys
import os
from datetime import datetime, date
import logging

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from db_models import DashboardStats, ActivityLog

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_stats_tables():
    """创建统计相关表"""
    try:
        logger.info("开始创建统计相关表...")
        
        # 创建所有表
        db.create_all()
        
        logger.info("统计表创建成功！")
        return True
        
    except Exception as e:
        logger.error(f"创建统计表失败: {e}")
        return False

def init_dashboard_stats():
    """初始化仪表板统计数据"""
    try:
        logger.info("开始初始化仪表板统计数据...")
        
        # 检查是否已有今天的数据
        today = date.today()
        existing_stats = DashboardStats.query.filter_by(date=today).first()
        
        if existing_stats:
            logger.info("今天的统计数据已存在，跳过初始化")
            return True
        
        # 从现有数据计算统计
        from db_models import Project, Document, User, ProjectStatus, DocumentStatus, RiskLevel
        from sqlalchemy import func
        
        # 项目统计
        total_projects = Project.query.count()
        completed_projects = Project.query.filter_by(status=ProjectStatus.COMPLETED).count()
        processing_projects = Project.query.filter_by(status=ProjectStatus.PROCESSING).count()
        collecting_projects = Project.query.filter_by(status=ProjectStatus.COLLECTING).count()
        archived_projects = Project.query.filter_by(status=ProjectStatus.ARCHIVED).count()

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
        
        # 创建今天的统计记录
        stats = DashboardStats(
            date=today,
            total_projects=total_projects,
            completed_projects=completed_projects,
            processing_projects=processing_projects,
            collecting_projects=collecting_projects,
            archived_projects=archived_projects,
            total_documents=total_documents,
            completed_documents=completed_documents,
            processing_documents=processing_documents,
            failed_documents=failed_documents,
            total_users=total_users,
            active_users=active_users,
            average_score=average_score,
            high_risk_projects=high_risk_projects,
            medium_risk_projects=medium_risk_projects,
            low_risk_projects=low_risk_projects
        )
        
        db.session.add(stats)
        db.session.commit()
        
        logger.info(f"初始化统计数据成功: {stats.to_dict()}")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"初始化统计数据失败: {e}")
        return False

def create_sample_activities():
    """创建示例活动数据"""
    try:
        logger.info("开始创建示例活动数据...")
        
        # 检查是否已有活动数据
        existing_count = ActivityLog.query.count()
        if existing_count > 0:
            logger.info(f"已存在 {existing_count} 条活动记录，跳过示例数据创建")
            return True
        
        # 创建示例活动
        sample_activities = [
            {
                'type': 'user_login',
                'title': '管理员 登录系统',
                'user_id': 1,
                'resource_type': 'user',
                'resource_id': 1,
                'created_at': datetime.utcnow()
            },
            {
                'type': 'project_created',
                'title': '创建了新项目：腾讯科技征信分析',
                'description': '项目ID: 1',
                'user_id': 1,
                'resource_type': 'project',
                'resource_id': 1,
                'activity_metadata': {'project_name': '腾讯科技征信分析'},
                'created_at': datetime.utcnow()
            },
            {
                'type': 'document_uploaded',
                'title': '腾讯科技征信分析 文档上传完成',
                'description': '文件: 企业营业执照.pdf',
                'user_id': 1,
                'resource_type': 'document',
                'resource_id': 1,
                'activity_metadata': {'document_name': '企业营业执照.pdf', 'project_name': '腾讯科技征信分析'},
                'created_at': datetime.utcnow()
            },
            {
                'type': 'report_generated',
                'title': '腾讯科技征信分析 征信报告已生成',
                'description': '项目ID: 1, 评分: 85',
                'user_id': 1,
                'resource_type': 'project',
                'resource_id': 1,
                'activity_metadata': {'project_name': '腾讯科技征信分析', 'score': 85},
                'created_at': datetime.utcnow()
            }
        ]
        
        for activity_data in sample_activities:
            activity = ActivityLog(**activity_data)
            db.session.add(activity)
        
        db.session.commit()
        
        logger.info(f"创建了 {len(sample_activities)} 条示例活动记录")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建示例活动数据失败: {e}")
        return False

def run_migration():
    """运行完整的迁移"""
    logger.info("开始运行统计表迁移...")
    
    success = True
    
    # 1. 创建表
    if not create_stats_tables():
        success = False
    
    # 2. 初始化统计数据
    if success and not init_dashboard_stats():
        success = False
    
    # 3. 创建示例活动
    if success and not create_sample_activities():
        success = False
    
    if success:
        logger.info("统计表迁移完成！")
    else:
        logger.error("统计表迁移失败！")
    
    return success

if __name__ == '__main__':
    # 确保在应用上下文中运行
    from app import app
    
    with app.app_context():
        run_migration()
