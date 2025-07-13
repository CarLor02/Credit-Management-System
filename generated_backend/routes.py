"""
API路由注册
"""

import os
import json
import asyncio
from flask import request, jsonify, Response
from functools import wraps
from typing import Dict, List, Any

from models import *
from utils import validate_request, handle_async_route
from api.projects import register_project_routes
from api.documents import register_document_routes
from api.auth import register_auth_routes
from api.project_details import register_project_detail_routes
from api.stats import register_stats_routes as register_new_stats_routes

def register_routes(app):
    """注册所有API路由"""

    # 注册认证路由
    register_auth_routes(app)

    # 注册项目管理路由
    register_project_routes(app)

    # 注册文档管理路由
    register_document_routes(app)

    # 注册项目详情路由
    register_project_detail_routes(app)

    # 注册统计信息路由
    register_new_stats_routes(app)

# 旧的统计路由已移动到 api/stats.py

# 辅助函数
def generate_id():
    """生成唯一ID"""
    import uuid
    return str(uuid.uuid4())

def get_current_time():
    """获取当前时间"""
    from datetime import datetime
    return datetime.now().isoformat()