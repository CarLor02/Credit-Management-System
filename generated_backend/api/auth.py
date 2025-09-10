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
    try:
        expiry_seconds = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expiry_seconds),
            'iat': datetime.utcnow()  # 添加签发时间
        }
        secret_key = current_app.config.get('JWT_SECRET_KEY')
        if not secret_key:
            current_app.logger.error("JWT_SECRET_KEY未配置")
            raise ValueError("JWT_SECRET_KEY未配置")
        
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        current_app.logger.debug(f"生成Token成功 - user_id: {user_id}, expires_in: {expiry_seconds}秒")
        return token
    except Exception as e:
        current_app.logger.error(f"生成Token失败: {e}")
        raise

def verify_token(token):
    """验证JWT token"""
    try:
        payload = jwt.decode(token, current_app.config.get('JWT_SECRET_KEY'), algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        current_app.logger.info(f"Token已过期: {token[:20]}...")
        return None
    except jwt.InvalidTokenError as e:
        current_app.logger.info(f"无效Token: {e}")
        return None
    except Exception as e:
        current_app.logger.error(f"Token验证异常: {e}")
        return None

def token_required(f):
    """JWT token验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # 对于OPTIONS预检请求，直接放行
        if request.method == 'OPTIONS':
            return jsonify({'success': True}), 200

        token = request.headers.get('Authorization')

        if not token:
            current_app.logger.info(f"缺少认证token - IP: {request.remote_addr}, URL: {request.url}")
            return jsonify({'success': False, 'error': '缺少认证token'}), 401

        if token.startswith('Bearer '):
            token = token[7:]

        user_id = verify_token(token)
        if not user_id:
            current_app.logger.info(f"无效token - IP: {request.remote_addr}, URL: {request.url}, Token: {token[:20]}...")
            return jsonify({'success': False, 'error': '无效的token'}), 401

        # 获取用户信息
        user = User.query.get(user_id)
        if not user or not user.is_active:
            current_app.logger.warning(f"用户不存在或已禁用 - user_id: {user_id}, IP: {request.remote_addr}")
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
                current_app.logger.info(f"登录失败：用户名或密码为空 - IP: {request.remote_addr}")
                return jsonify({'success': False, 'error': '用户名和密码不能为空'}), 400
            
            # 查找用户
            user = User.query.filter_by(username=data['username']).first()
            
            # 详细的错误检查和提示
            if not user:
                current_app.logger.info(f"登录失败：用户不存在 - 用户名: {data['username']}, IP: {request.remote_addr}")
                return jsonify({'success': False, 'error': '用户名错误，用户不存在'}), 401
            
            if not user.check_password(data['password']):
                current_app.logger.info(f"登录失败：密码错误 - 用户名: {data['username']}, IP: {request.remote_addr}")
                return jsonify({'success': False, 'error': '密码错误'}), 401
            
            if not user.is_active:
                current_app.logger.warning(f"登录失败：用户已被禁用 - 用户名: {data['username']}, IP: {request.remote_addr}")
                return jsonify({'success': False, 'error': '账户已被禁用，请联系管理员'}), 401
            
            # 更新最后登录时间
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # 生成token
            token = generate_token(user.id)
            
            # 记录登录成功日志
            current_app.logger.info(f"用户登录成功 - 用户名: {user.username}, 用户ID: {user.id}, IP: {request.remote_addr}")
            
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
                ActivityLogger.log_user_login(user.id, user.username)
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
            current_app.logger.error(f"用户登录异常: {e}, IP: {request.remote_addr}")
            return jsonify({'success': False, 'error': '登录失败'}), 500

    @app.route('/api/auth/register', methods=['POST'])
    def register():
        """用户注册"""
        try:
            data = request.get_json()

            # 验证必填字段
            required_fields = {
                'username': '用户名',
                'email': '邮箱',
                'password': '密码'
            }
            for field, name in required_fields.items():
                if not data or not data.get(field):
                    return jsonify({'success': False, 'error': f'{name}不能为空'}), 400

            # 验证邮箱格式
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data['email']):
                return jsonify({'success': False, 'error': '邮箱格式不正确'}), 400

            # 检查用户名是否已存在
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user:
                return jsonify({'success': False, 'error': '用户名已被注册，请选择其他用户名'}), 400

            # 检查邮箱是否已存在
            existing_email = User.query.filter_by(email=data['email']).first()
            if existing_email:
                return jsonify({'success': False, 'error': '邮箱已被注册，请使用其他邮箱'}), 400

            # 验证密码长度
            if len(data['password']) < 6:
                return jsonify({'success': False, 'error': '密码长度至少6位字符'}), 400

            # 创建新用户
            new_user = User(
                username=data['username'],
                email=data['email'],
                phone=data.get('phone'),  # 可选的手机号
                role=UserRole.USER  # 默认角色为普通用户
            )
            new_user.set_password(data['password'])

            # 保存到数据库
            db.session.add(new_user)
            db.session.commit()

            # 生成token
            token = generate_token(new_user.id)

            # 记录注册日志
            log_action(
                user_id=new_user.id,
                action='user_register',
                details=f'用户 {new_user.username} 注册成功',
                ip_address=request.remote_addr
            )

            # 记录活动日志
            try:
                from services.stats_service import ActivityLogger
                ActivityLogger.log_user_register(new_user.id, new_user.username)
            except Exception as e:
                current_app.logger.warning(f"记录活动日志失败: {e}")

            return jsonify({
                'success': True,
                'data': {
                    'token': token,
                    'user': new_user.to_dict()
                },
                'message': '注册成功'
            })

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"用户注册失败: {e}")
            return jsonify({'success': False, 'error': '注册失败'}), 500

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
            if 'email' in data:
                # 检查邮箱是否已存在
                existing_user = User.query.filter_by(email=data['email']).first()
                if existing_user and existing_user.id != user.id:
                    return jsonify({'success': False, 'error': '邮箱已被使用'}), 400
                user.email = data['email']
            if 'phone' in data:
                user.phone = data['phone']
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
    
    @app.route('/api/auth/reset-password', methods=['POST'])
    def reset_password():
        """重置密码（通过用户名和邮箱验证）"""
        try:
            data = request.get_json()
            
            # 验证必填字段
            required_fields = {
                'username': '用户名',
                'email': '邮箱',
                'new_password': '新密码'
            }
            for field, name in required_fields.items():
                if not data.get(field):
                    return jsonify({'success': False, 'error': f'{name}不能为空'}), 400

            # 验证邮箱格式
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data['email']):
                return jsonify({'success': False, 'error': '邮箱格式不正确'}), 400

            # 验证新密码长度
            if len(data['new_password']) < 6:
                return jsonify({'success': False, 'error': '新密码长度至少6位字符'}), 400
            
            # 首先检查用户名是否存在
            user_by_username = User.query.filter_by(username=data['username']).first()
            if not user_by_username:
                current_app.logger.info(f"重置密码失败：用户名不存在 - 用户名: {data['username']}, IP: {request.remote_addr}")
                return jsonify({'success': False, 'error': '用户名错误，用户不存在'}), 404

            # 检查邮箱是否匹配
            if user_by_username.email != data['email']:
                current_app.logger.info(f"重置密码失败：邮箱不匹配 - 用户名: {data['username']}, 输入邮箱: {data['email']}, 实际邮箱: {user_by_username.email}, IP: {request.remote_addr}")
                return jsonify({'success': False, 'error': '邮箱错误，与用户名不匹配'}), 404

            # 用户名和邮箱都正确
            user = user_by_username
            
            if not user.is_active:
                current_app.logger.warning(f"重置密码失败：用户已被禁用 - 用户名: {data['username']}, IP: {request.remote_addr}")
                return jsonify({'success': False, 'error': '账户已被禁用，请联系管理员'}), 403
            
            # 设置新密码
            user.set_password(data['new_password'])
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            # 记录日志
            current_app.logger.info(f"密码重置成功 - 用户名: {user.username}, 用户ID: {user.id}, IP: {request.remote_addr}")
            log_action(
                user_id=user.id,
                action='password_reset',
                details=f'用户 {user.username} 通过用户名邮箱验证重置密码',
                ip_address=request.remote_addr
            )
            
            return jsonify({
                'success': True,
                'message': '密码重置成功，请使用新密码登录'
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"重置密码异常: {e}, IP: {request.remote_addr}")
            return jsonify({'success': False, 'error': '重置密码失败，请稍后重试'}), 500
    
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
