"""
数据库种子数据
用于初始化用户数据
"""

from datetime import datetime, timedelta, timezone

from database import db
from db_models import User, UserRole

def create_seed_data():
    """创建种子数据"""
    print("开始创建种子数据...")

    # 创建用户
    create_users()

    db.session.commit()
    print("种子数据创建完成!")

def create_users():
    """创建用户数据"""
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@example.com',
            'password': 'admin123',
            'phone': '13800138000',
            'role': UserRole.ADMIN
        },
        {
            'username': 'user1',
            'email': 'user1@example.com',
            'password': 'user123',
            'phone': '13800138001',
            'role': UserRole.USER
        },
        {
            'username': 'user2',
            'email': 'user2@example.com',
            'password': 'user123',
            'phone': '13800138002',
            'role': UserRole.USER
        },
        {
            'username': 'user3',
            'email': 'user3@example.com',
            'password': 'user123',
            'phone': '13800138003',
            'role': UserRole.USER
        }
    ]

    users = []
    created_count = 0
    for user_data in users_data:
        # 检查用户是否已存在
        existing_user = User.query.filter_by(email=user_data['email']).first()
        if existing_user:
            print(f"用户 {user_data['email']} 已存在，跳过创建")
            users.append(existing_user)
            continue

        user = User(
            username=user_data['username'],
            email=user_data['email'],
            phone=user_data.get('phone'),
            role=user_data['role'],
            is_active=True,
            last_login=datetime.now(timezone.utc) - timedelta(days=1)
        )
        user.set_password(user_data['password'])
        db.session.add(user)
        users.append(user)
        created_count += 1

    db.session.flush()  # 获取ID
    print(f"创建了 {created_count} 个新用户，跳过了 {len(users_data) - created_count} 个已存在的用户")
    return users

