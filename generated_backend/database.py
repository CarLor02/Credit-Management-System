"""
数据库初始化和配置
"""

import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

# 创建数据库实例
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """初始化数据库"""
    db.init_app(app)
    migrate.init_app(app, db)
    
    # SQLite外键支持
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if isinstance(dbapi_connection, sqlite3.Connection):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
    
    return db

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
    """创建数据库索引"""
    try:
        # 用户表索引
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"))
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"))
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)"))

        # 项目表索引
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_projects_type ON projects(type)"))
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)"))
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_projects_created_by ON projects(created_by)"))
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at)"))

        # 文档表索引
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id)"))
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)"))
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_documents_upload_by ON documents(upload_by)"))

        # 项目成员表索引
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON project_members(project_id)"))
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_project_members_user_id ON project_members(user_id)"))

        # 分析报告表索引
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_analysis_reports_project_id ON analysis_reports(project_id)"))
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_analysis_reports_status ON analysis_reports(status)"))

        # 工作流事件表索引
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_workflow_events_workflow_run_id ON workflow_events(workflow_run_id)"))
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_workflow_events_project_id ON workflow_events(project_id)"))
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_workflow_events_created_at ON workflow_events(created_at)"))

        # 知识库表索引
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_knowledge_bases_project_id ON knowledge_bases(project_id)"))

        # 系统日志表索引
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_system_logs_user_id ON system_logs(user_id)"))
        db.session.execute(db.text("CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at)"))

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
