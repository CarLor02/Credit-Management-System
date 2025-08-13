"""
数据库连接配置和工厂类
专为MySQL数据库设计
"""

import os
import pymysql
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from flask_sqlalchemy import SQLAlchemy

class DatabaseConfig:
    """数据库配置类"""
    
    @staticmethod
    def get_mysql_uri(host='localhost', port=3306, username='root', 
                     password='RootPass123!', database='credit_db', charset='utf8mb4'):
        """
        生成MySQL数据库连接URI
        
        Args:
            host: 主机地址
            port: 端口号
            username: 用户名
            password: 密码
            database: 数据库名
            charset: 字符集
            
        Returns:
            str: MySQL连接URI
        """
        # URL编码密码以处理特殊字符
        encoded_password = quote_plus(password)
        return f'mysql+pymysql://{username}:{encoded_password}@{host}:{port}/{database}?charset={charset}'
    
    @staticmethod
    def get_database_uri():
        """
        根据环境变量获取MySQL数据库连接URI
        
        Returns:
            str: 数据库连接URI
        """
        # 检查是否设置了完整的数据库URL
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            return database_url
        
        # MySQL配置
        mysql_config = {
            'host': os.environ.get('MYSQL_HOST', 'localhost'),
            'port': int(os.environ.get('MYSQL_PORT', 3306)),
            'username': os.environ.get('MYSQL_USER', 'root'),
            'password': os.environ.get('MYSQL_PASSWORD', 'RootPass123!'),
            'database': os.environ.get('MYSQL_DATABASE', 'credit_db'),
            'charset': os.environ.get('MYSQL_CHARSET', 'utf8mb4')
        }
        return DatabaseConfig.get_mysql_uri(**mysql_config)
    
    @staticmethod
    def get_engine_options(db_uri):
        """
        获取MySQL SQLAlchemy引擎选项
        
        Args:
            db_uri: 数据库连接URI
            
        Returns:
            dict: 引擎选项
        """
        return {
            'poolclass': QueuePool,
            'pool_size': 10,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'echo': os.environ.get('SQLALCHEMY_ECHO', 'False').lower() == 'true'
        }

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.db = None
        self.engine = None
        
    def init_app(self, app):
        """初始化数据库"""
        # 获取数据库URI
        db_uri = DatabaseConfig.get_database_uri()
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # 获取引擎选项
        engine_options = DatabaseConfig.get_engine_options(db_uri)
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options
        
        # 初始化SQLAlchemy
        from database import db, migrate
        db.init_app(app)
        migrate.init_app(app, db)
        
        self.db = db
        
        print(f"✓ 数据库连接配置完成: {self._mask_password(db_uri)}")
        
        return db
    
    def _mask_password(self, uri):
        """隐藏URI中的密码"""
        import re
        return re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', uri)
    
    def test_connection(self):
        """测试数据库连接"""
        try:
            with self.db.engine.connect() as conn:
                conn.execute(self.db.text("SELECT 1"))
            print("✓ 数据库连接测试成功")
            return True
        except Exception as e:
            print(f"✗ 数据库连接测试失败: {e}")
            return False
    
    def create_database_if_not_exists(self):
        """创建数据库（仅适用于MySQL）"""
        db_uri = DatabaseConfig.get_database_uri()
        
        if 'mysql' in db_uri:
            try:
                # 解析连接参数
                import re
                pattern = r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)'
                match = re.match(pattern, db_uri)
                
                if match:
                    username, password, host, port, database = match.groups()
                    password = quote_plus(password)  # URL解码
                    
                    # 连接到MySQL服务器（不指定数据库）
                    server_uri = f'mysql+pymysql://{username}:{password}@{host}:{port}/'
                    temp_engine = create_engine(server_uri)
                    
                    with temp_engine.connect() as conn:
                        # 检查数据库是否存在
                        result = conn.execute(
                            self.db.text(f"SHOW DATABASES LIKE '{database}'")
                        )
                        
                        if not result.fetchone():
                            # 创建数据库
                            conn.execute(self.db.text(f"CREATE DATABASE {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                            print(f"✓ 创建数据库: {database}")
                        else:
                            print(f"✓ 数据库已存在: {database}")
                    
                    temp_engine.dispose()
                    
            except Exception as e:
                print(f"✗ 创建数据库失败: {e}")
                raise

# 创建全局数据库管理器实例
db_manager = DatabaseManager()
