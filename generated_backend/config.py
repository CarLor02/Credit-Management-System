"""
应用配置
"""

import os
from dotenv import load_dotenv

load_dotenv()

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
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1小时

    # RAG API配置
    RAG_API_BASE_URL = os.environ.get('RAG_API_BASE_URL', 'http://172.16.76.183')
    RAG_API_KEY = os.environ.get('RAG_API_KEY', 'ragflow-U4OWM2Njc2NDVjNTExZjA5NDUzMDI0Mm')

    # 报告生成API配置
    REPORT_API_URL = os.environ.get('REPORT_API_URL', 'http://172.16.76.203/v1/workflows/run')
    REPORT_API_KEY = os.environ.get('REPORT_API_KEY', 'app-zLDrndvfJ81HaTWD3gXXVJaq')

    # Mock API配置
    USE_MOCK_API = os.environ.get('USE_MOCK_API', 'True').lower() == 'true'

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
