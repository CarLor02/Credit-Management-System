"""
工具函数和装饰器
"""

import logging
import asyncio
from functools import wraps
from flask import request, jsonify
from typing import Dict, List, Any
from datetime import datetime

def setup_logging(app):
    """设置日志"""
    if not app.debug:
        logging.basicConfig(level=logging.INFO)
    app.logger.info("征信管理系统后端启动")

def validate_request(required_fields: List[str]):
    """请求验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({"error": "请求体不能为空"}), 400
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({"error": f"缺少必需字段: {', '.join(missing_fields)}"}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def handle_async_route(f):
    """异步路由处理装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return decorated_function

def paginate_results(items: List[Any], page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """分页处理"""
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

def log_action(user_id, action, resource_type=None, resource_id=None, details=None, ip_address=None):
    """记录系统日志"""
    try:
        from database import db
        from db_models import SystemLog

        log = SystemLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address or request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None
        )

        db.session.add(log)
        db.session.commit()

    except Exception as e:
        print(f"记录日志失败: {e}")

def format_response(success=True, data=None, message=None, error=None, status_code=200):
    """格式化API响应"""
    response = {
        'success': success,
        'timestamp': datetime.utcnow().isoformat()
    }

    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    if error:
        response['error'] = error

    return jsonify(response), status_code
