"""
应用配置
"""

import os
from dotenv import load_dotenv

# 根据环境加载对应的.env文件
def load_environment_config():
    """根据FLASK_ENV环境变量加载对应的配置文件"""
    flask_env = os.environ.get('FLASK_ENV', 'development')

    # 获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

    if flask_env == 'production':
        # 生产环境：加载.env.production
        env_file = os.path.join(current_dir, '.env.production')
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"✓ 已加载生产环境配置文件: {env_file}")
        else:
            print(f"⚠ 生产环境配置文件不存在: {env_file}")
            # 尝试加载默认的.env文件
            default_env = os.path.join(current_dir, '.env')
            if os.path.exists(default_env):
                load_dotenv(default_env)
                print(f"✓ 已加载默认配置文件: {default_env}")
    else:
        # 开发环境：加载.env或.env.local
        env_files = [
            os.path.join(current_dir, '.env.local'),
            os.path.join(current_dir, '.env')
        ]

        for env_file in env_files:
            if os.path.exists(env_file):
                load_dotenv(env_file)
                print(f"✓ 已加载开发环境配置文件: {env_file}")
                break
        else:
            print("⚠ 未找到环境配置文件，使用默认配置")

# 加载环境配置
load_environment_config()

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5001))

    # 数据库配置
    # 获取当前目录的绝对路径
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'instance', 'credit_system.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', 'False').lower() == 'true'

    # 文件上传配置
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls','csv', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'md'}

    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 86400))  # 1天 (24小时 * 60分钟 * 60秒)

    # RAG API配置
    RAG_API_BASE_URL = os.environ.get('RAG_API_BASE_URL', 'http://172.16.18.156:17080')
    RAG_API_KEY = os.environ.get('RAG_API_KEY', 'ragflow-VmMWVkNGUwNjhmYTExZjBhNTgzNzYwNT')

    # 报告生成API配置
    REPORT_API_URL = os.environ.get('REPORT_API_URL', 'http://172.16.18.157:18080/v1/workflows/run')
    REPORT_API_KEY = os.environ.get('REPORT_API_KEY', 'app-TPm1UnL2LeXaMnZI4c03frYN')

    # 文档处理服务API配置
    DOCUMENT_PROCESS_API_URL = os.environ.get('DOCUMENT_PROCESS_API_URL', 'http://localhost:7860/api/process')

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:password@localhost/credit_system'


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
