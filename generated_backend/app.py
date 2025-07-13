"""
自动生成的Flask应用主文件
基于前端分析结果生成
"""

import os
import asyncio
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor

from routes import register_routes
from config import Config
from utils import setup_logging
from database import init_db

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 启用CORS支持
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

# 初始化数据库
db = init_db(app)

# 设置日志
setup_logging(app)

# 注册路由
register_routes(app)

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
    # 开发环境运行
    app.run(
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 5001),
        debug=app.config.get('DEBUG', True)
    )
