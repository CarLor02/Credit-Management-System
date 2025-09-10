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

def check_database_exists():
    """检查MySQL数据库是否存在"""
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
                    print(f"✗ 数据库不存在: {database}, 请先执行SQL脚本初始化数据库后再运行后端！")
                else:
                    print(f"✓ 数据库已存在: {database}")

            temp_engine.dispose()

    except Exception as e:
        print(f"✗ 创建数据库失败: {e}")
        print("应用将继续启动，请确保数据库配置正确")

def init_db(app):
    """初始化数据库"""
    # 检查数据库是否存在
    check_database_exists()

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

    # 检查数据库表
    with app.app_context():
        check_tables_exists()

    print(f"✓ 数据库连接配置完成: {_mask_password(db_uri)}")
    return db

def _mask_password(uri):
    """隐藏URI中的密码"""
    return re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', uri)

def check_tables_exists():
    """创建数据库表（如果不存在）"""
    try:
        # 导入所有模型以确保它们被注册
        from db_models import (User, Project, Document, ProjectMember,
                             AnalysisReport, SystemLog, SystemSetting,
                             DashboardStats, ActivityLog, FinancialAnalysis,
                             BusinessStatus, ProjectTimeline, StatisticsHistory)

        # 检查数据库是否存在
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if not existing_tables:
            print("✗ 数据库中表不存在，请先执行SQL脚本初始化数据库后再运行后端！")
            exit(1)

        # 检查所有表是否存在
        required_tables = [
            'users', 'projects', 'documents', 'project_members',
            'analysis_reports', 'system_logs', 'system_settings',
            'dashboard_stats', 'activity_logs', 'financial_analysis',
            'business_status', 'project_timeline', 'statistics_history'
        ]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"✗ 数据库中缺少以下表: {', '.join(missing_tables)}")
            print("请先执行SQL脚本初始化数据库后再运行后端！")
            exit(1)
        
        print(f"✓ 数据库表检查通过 ({len(existing_tables)} 个表)")

    except Exception as e:
        print(f"✗ 数据库检查失败: {e}")
        print("应用将继续启动，请手动检查数据库配置")
