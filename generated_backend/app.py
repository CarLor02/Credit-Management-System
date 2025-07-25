"""
自动生成的Flask应用主文件
基于前端分析结果生成
"""

import os
import asyncio
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO
from concurrent.futures import ThreadPoolExecutor

from routes import register_routes
from config import Config
from utils import setup_logging
from database import init_db, create_tables
from websocket_handlers import register_websocket_handlers

def init_database_if_needed(app):
    """检查数据库是否存在，如果不存在则自动初始化"""
    try:
        # 获取数据库文件路径
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
        else:
            print("非SQLite数据库，跳过自动初始化")
            return
            
        print(f"检查数据库文件: {db_path}")
        
        if not os.path.exists(db_path):
            print(f"数据库文件不存在: {db_path}")
            print("正在自动初始化数据库...")
            
            # 确保instance目录存在
            instance_dir = os.path.dirname(db_path)
            if not os.path.exists(instance_dir):
                os.makedirs(instance_dir)
                print(f"创建instance目录: {instance_dir}")
            
            # 创建数据库表
            create_tables(app)
            
            # 创建种子数据
            from seed_data import create_seed_data
            create_seed_data()
            
            print("数据库初始化完成!")
        else:
            print(f"数据库文件已存在: {db_path}")
            
    except Exception as e:
        print(f"数据库初始化检查失败: {e}")
        print("请手动运行 python init_db.py 来初始化数据库")

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 启用CORS支持
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000","http://115.190.121.59:3000"])

# 创建SocketIO实例
socketio = SocketIO(
    app,
    cors_allowed_origins="*",  # 临时允许所有来源，用于调试
    async_mode='threading',
    logger=True,
    engineio_logger=True
)

# 初始化数据库
db = init_db(app)

# 检查并初始化数据库（如果需要）
with app.app_context():
    init_database_if_needed(app)

# 设置日志
setup_logging(app)

# 注册路由
register_routes(app)

# 注册WebSocket处理器
register_websocket_handlers(socketio)

# 将socketio实例设置为全局变量，供其他模块使用
app.socketio = socketio

# 全局错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "API端点未找到"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "服务器内部错误"}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "请求参数错误"}), 400

# 健康检查端点
@app.route('/health', methods=['GET'])
def health_check():
    try:
        # 检查数据库连接
        from db_models import User
        user_count = User.query.count()

        return jsonify({
            "status": "healthy",
            "message": "征信管理系统后端服务运行正常",
            "database": "connected",
            "users": user_count
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "message": "数据库连接失败",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    # 创建上传目录
    import os
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    app.logger.info("征信管理系统后端启动")
    # 开发环境运行，使用SocketIO
    socketio.run(
        app,
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 5001),
        debug=app.config.get('DEBUG', True),
        allow_unsafe_werkzeug=True  # 允许在开发环境使用Werkzeug
    )
