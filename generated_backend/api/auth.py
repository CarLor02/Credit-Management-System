"""
用户认证和权限管理API
"""

import jwt
from datetime import datetime, timedelta
from flask import request, jsonify, current_app
from functools import wraps

from database import db
from db_models import User, SystemLog, UserRole
from utils import log_action

def generate_token(user_id):
    """生成JWT token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    }
    return jwt.encode(payload, current_app.config.get('JWT_SECRET_KEY'), algorithm='HS256')

def verify_token(token):
    """验证JWT token"""
    try:
        payload = jwt.decode(token, current_app.config.get('JWT_SECRET_KEY'), algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """JWT token验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'success': False, 'error': '缺少认证token'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        user_id = verify_token(token)
        if not user_id:
            return jsonify({'success': False, 'error': '无效的token'}), 401
        
        # 获取用户信息
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({'success': False, 'error': '用户不存在或已禁用'}), 401
        
        # 将用户信息添加到请求上下文
        request.current_user = user
        
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.current_user.role != UserRole.ADMIN:
            return jsonify({'success': False, 'error': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    
    return decorated

def register_auth_routes(app):
    """注册认证相关路由"""
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        """用户登录"""
        try:
            data = request.get_json()
            
            if not data or not data.get('username') or not data.get('password'):
                return jsonify({'success': False, 'error': '用户名和密码不能为空'}), 400
            
            # 查找用户
            user = User.query.filter_by(username=data['username']).first()
            
            if not user or not user.check_password(data['password']):
                return jsonify({'success': False, 'error': '用户名或密码错误'}), 401
            
            if not user.is_active:
                return jsonify({'success': False, 'error': '用户已被禁用'}), 401
            
            # 更新最后登录时间
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # 生成token
            token = generate_token(user.id)
            
            # 记录登录日志
            log_action(
                user_id=user.id,
                action='user_login',
                details=f'用户 {user.username} 登录系统',
                ip_address=request.remote_addr
            )

            # 记录活动日志
            try:
                from services.stats_service import ActivityLogger
                ActivityLogger.log_user_login(user.id, user.full_name or user.username)
            except Exception as e:
                current_app.logger.warning(f"记录活动日志失败: {e}")
            
            return jsonify({
                'success': True,
                'data': {
                    'token': token,
                    'user': user.to_dict()
                },
                'message': '登录成功'
            })
            
        except Exception as e:
            current_app.logger.error(f"用户登录失败: {e}")
            return jsonify({'success': False, 'error': '登录失败'}), 500
    
    @app.route('/api/auth/logout', methods=['POST'])
    @token_required
    def logout():
        """用户登出"""
        try:
            # 记录登出日志
            log_action(
                user_id=request.current_user.id,
                action='user_logout',
                details=f'用户 {request.current_user.username} 登出系统',
                ip_address=request.remote_addr
            )
            
            return jsonify({
                'success': True,
                'message': '登出成功'
            })
            
        except Exception as e:
            current_app.logger.error(f"用户登出失败: {e}")
            return jsonify({'success': False, 'error': '登出失败'}), 500
    
    @app.route('/api/auth/profile', methods=['GET'])
    @token_required
    def get_profile():
        """获取用户信息"""
        try:
            return jsonify({
                'success': True,
                'data': request.current_user.to_dict()
            })
            
        except Exception as e:
            current_app.logger.error(f"获取用户信息失败: {e}")
            return jsonify({'success': False, 'error': '获取用户信息失败'}), 500
    
    @app.route('/api/auth/profile', methods=['PUT'])
    @token_required
    def update_profile():
        """更新用户信息"""
        try:
            data = request.get_json()
            user = request.current_user
            
            # 更新允许的字段
            if 'full_name' in data:
                user.full_name = data['full_name']
            if 'email' in data:
                # 检查邮箱是否已存在
                existing_user = User.query.filter_by(email=data['email']).first()
                if existing_user and existing_user.id != user.id:
                    return jsonify({'success': False, 'error': '邮箱已被使用'}), 400
                user.email = data['email']
            if 'avatar_url' in data:
                user.avatar_url = data['avatar_url']
            
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            # 记录日志
            log_action(
                user_id=user.id,
                action='profile_update',
                details=f'用户 {user.username} 更新个人信息'
            )
            
            return jsonify({
                'success': True,
                'data': user.to_dict(),
                'message': '个人信息更新成功'
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新用户信息失败: {e}")
            return jsonify({'success': False, 'error': '更新用户信息失败'}), 500
    
    @app.route('/api/auth/change-password', methods=['POST'])
    @token_required
    def change_password():
        """修改密码"""
        try:
            data = request.get_json()
            user = request.current_user
            
            if not data.get('old_password') or not data.get('new_password'):
                return jsonify({'success': False, 'error': '旧密码和新密码不能为空'}), 400
            
            # 验证旧密码
            if not user.check_password(data['old_password']):
                return jsonify({'success': False, 'error': '旧密码错误'}), 400
            
            # 设置新密码
            user.set_password(data['new_password'])
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            # 记录日志
            log_action(
                user_id=user.id,
                action='password_change',
                details=f'用户 {user.username} 修改密码'
            )
            
            return jsonify({
                'success': True,
                'message': '密码修改成功'
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"修改密码失败: {e}")
            return jsonify({'success': False, 'error': '修改密码失败'}), 500
    
    @app.route('/api/users', methods=['GET'])
    @admin_required
    def get_users():
        """获取用户列表（管理员）"""
        try:
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 20, type=int)
            search = request.args.get('search', '')
            
            query = User.query
            
            if search:
                query = query.filter(
                    User.username.contains(search) |
                    User.full_name.contains(search) |
                    User.email.contains(search)
                )
            
            total = query.count()
            users = query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
            
            users_data = [user.to_dict() for user in users]
            
            return jsonify({
                'success': True,
                'data': users_data,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': (total + limit - 1) // limit
                }
            })
            
        except Exception as e:
            current_app.logger.error(f"获取用户列表失败: {e}")
            return jsonify({'success': False, 'error': '获取用户列表失败'}), 500
