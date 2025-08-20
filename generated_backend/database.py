"""
数据库初始化和配置
专为MySQL数据库设计，包含自动初始化功能
"""

import os
import re
from urllib.parse import quote_plus
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

# 创建数据库实例
db = SQLAlchemy()
migrate = Migrate()

def get_database_uri():
    """获取MySQL数据库连接URI"""
    # 检查是否设置了完整的数据库URL
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        return database_url

    # MySQL配置
    host = os.environ.get('MYSQL_HOST', 'localhost')
    port = int(os.environ.get('MYSQL_PORT', 3306))
    username = os.environ.get('MYSQL_USER', 'root')
    password = os.environ.get('MYSQL_PASSWORD', 'RootPass123!')
    database = os.environ.get('MYSQL_DATABASE', 'credit_db')
    charset = os.environ.get('MYSQL_CHARSET', 'utf8mb4')

    # URL编码密码以处理特殊字符
    encoded_password = quote_plus(password)
    return f'mysql+pymysql://{username}:{encoded_password}@{host}:{port}/{database}?charset={charset}'

def create_database_if_not_exists():
    """创建MySQL数据库（如果不存在）"""
    db_uri = get_database_uri()

    try:
        # 解析连接参数
        pattern = r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)'
        match = re.match(pattern, db_uri)

        if match:
            username, encoded_password, host, port, database = match.groups()

            # 连接到MySQL服务器（不指定数据库）
            server_uri = f'mysql+pymysql://{username}:{encoded_password}@{host}:{port}/'
            temp_engine = create_engine(server_uri)

            with temp_engine.connect() as conn:
                # 检查数据库是否存在
                result = conn.execute(text(f"SHOW DATABASES LIKE '{database}'"))

                if not result.fetchone():
                    # 创建数据库
                    conn.execute(text(f"CREATE DATABASE {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                    print(f"✓ 创建数据库: {database}")
                else:
                    print(f"✓ 数据库已存在: {database}")

            temp_engine.dispose()

    except Exception as e:
        print(f"✗ 创建数据库失败: {e}")
        print("应用将继续启动，请确保数据库配置正确")

def init_db(app):
    """初始化数据库"""
    # 自动创建数据库（如果不存在）
    create_database_if_not_exists()

    # 获取数据库URI和配置
    db_uri = get_database_uri()
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 配置引擎选项
    engine_options = {
        'poolclass': QueuePool,
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'echo': os.environ.get('SQLALCHEMY_ECHO', 'False').lower() == 'true'
    }
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options

    # 初始化SQLAlchemy
    db.init_app(app)
    migrate.init_app(app, db)

    # MySQL连接配置
    @event.listens_for(Engine, "connect")
    def set_mysql_charset(dbapi_connection, connection_record):
        # 设置MySQL连接字符集
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET NAMES utf8mb4")
            cursor.execute("SET CHARACTER SET utf8mb4")
            cursor.execute("SET character_set_connection=utf8mb4")

    # 自动创建表和初始数据
    with app.app_context():
        create_tables_if_not_exists()

    print(f"✓ 数据库连接配置完成: {_mask_password(db_uri)}")
    return db

def _mask_password(uri):
    """隐藏URI中的密码"""
    return re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', uri)

def create_tables_if_not_exists():
    """创建数据库表（如果不存在）"""
    try:
        # 导入所有模型以确保它们被注册
        from db_models import (User, Project, Document, ProjectMember,
                             AnalysisReport, SystemLog, SystemSetting)

        # 检查是否已有表
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if not existing_tables:
            print("正在创建数据库表...")
            # 创建所有表
            db.create_all()

            # 创建索引
            create_indexes()

            print("✓ 数据库表创建完成")

            # 创建种子数据
            create_initial_data()
        else:
            print(f"✓ 数据库表已存在 ({len(existing_tables)} 个表)")

    except Exception as e:
        print(f"✗ 创建数据库表失败: {e}")
        print("应用将继续启动，请手动检查数据库表结构")

def create_initial_data():
    """创建初始数据"""
    try:
        from db_models import User

        # 检查是否已有用户数据
        user_count = User.query.count()
        if user_count == 0:
            # 如果没有用户，使用种子数据创建完整的初始数据
            print("正在创建种子数据...")
            from seed_data import create_seed_data
            create_seed_data()
            print("✓ 种子数据创建完成")
        else:
            print(f"✓ 数据库中已有 {user_count} 个用户，跳过种子数据创建")

    except Exception as e:
        print(f"✗ 创建初始数据失败: {e}")
        db.session.rollback()

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
    with app.app_context():
        drop_tables(app)
        create_tables_if_not_exists()
    print("数据库重置完成")
