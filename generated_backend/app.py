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
    """检查MySQL数据库连接"""
    try:
        # 获取数据库URI
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        print("数据库类型: MySQL")
        
        # MySQL数据库连接测试
        print("MySQL数据库模式，检查连接状态")
        
        # 仅测试连接
        try:
            from database import db
            with db.engine.connect() as conn:
                conn.execute(db.text("SELECT 1"))
            print("✓ MySQL数据库连接正常")
        except Exception as e:
            print(f"⚠ MySQL连接测试: {e}")
            print("应用将继续启动，请确保数据库配置正确")
            
    except Exception as e:
        print(f"数据库连接检查失败: {e}")
        print("应用将继续启动，如有问题请手动检查数据库配置")

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 启用CORS支持 - 允许所有来源
CORS(app, origins="*")

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
