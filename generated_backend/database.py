"""
数据库初始化和配置
专为MySQL数据库设计
"""

import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import event
from sqlalchemy.engine import Engine

# 创建数据库实例
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """初始化数据库"""
    # 使用新的数据库管理器
    from db_config import db_manager
    db_instance = db_manager.init_app(app)
    
    # MySQL连接配置
    if 'mysql' in app.config['SQLALCHEMY_DATABASE_URI']:
        @event.listens_for(Engine, "connect")
        def set_mysql_charset(dbapi_connection, connection_record):
            # 设置MySQL连接字符集
            with dbapi_connection.cursor() as cursor:
                cursor.execute("SET NAMES utf8mb4")
                cursor.execute("SET CHARACTER SET utf8mb4")
                cursor.execute("SET character_set_connection=utf8mb4")
    
    return db_instance

def create_tables(app):
    """创建所有数据库表"""
    with app.app_context():
        # 导入所有模型以确保它们被注册
        from db_models import User, Project, Document, ProjectMember, AnalysisReport, WorkflowEvent, SystemLog, SystemSetting
        
        # 创建所有表
        db.create_all()
        
        # 创建索引
        create_indexes()
        
        print("数据库表创建完成")

def create_indexes():
    """创建数据库索引（MySQL）"""
    try:
        # MySQL索引创建语句
        index_queries = [
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)", 
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
            "CREATE INDEX IF NOT EXISTS idx_projects_type ON projects(type)",
            "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
            "CREATE INDEX IF NOT EXISTS idx_projects_created_by ON projects(created_by)",
            "CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)",
            "CREATE INDEX IF NOT EXISTS idx_documents_upload_by ON documents(upload_by)",
            "CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON project_members(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_project_members_user_id ON project_members(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_analysis_reports_project_id ON analysis_reports(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_analysis_reports_status ON analysis_reports(status)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_events_workflow_run_id ON workflow_events(workflow_run_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_events_project_id ON workflow_events(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_events_created_at ON workflow_events(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_bases_project_id ON knowledge_bases(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_user_id ON system_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at)"
        ]
        
        # 执行索引创建
        for query in index_queries:
            try:
                db.session.execute(db.text(query))
            except Exception as e:
                # MySQL中索引已存在会报错，但可以忽略
                if "Duplicate key name" not in str(e):
                    print(f"创建索引时出现警告: {e}")

        db.session.commit()
        print("数据库索引创建完成")

    except Exception as e:
        print(f"创建索引时出错: {e}")
        db.session.rollback()

def drop_tables(app):
    """删除所有数据库表"""
    with app.app_context():
        db.drop_all()
        print("数据库表删除完成")

def reset_database(app):
    """重置数据库"""
    drop_tables(app)
    create_tables(app)
    print("数据库重置完成")
