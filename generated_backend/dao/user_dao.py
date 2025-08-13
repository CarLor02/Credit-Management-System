"""
用户数据访问对象
"""

from typing import List, Optional
from dao.base_dao import BaseDAO
from db_models import User, UserRole

class UserDAO(BaseDAO):
    """用户数据访问对象"""
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.get_one_by_filter(username=username)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.get_one_by_filter(email=email)
    
    def create_user(self, username: str, email: str, password: str, 
                   role: UserRole = UserRole.USER, phone: str = None) -> Optional[User]:
        """创建用户"""
        user = User(
            username=username,
            email=email,
            role=role,
            phone=phone
        )
        user.set_password(password)
        
        try:
            self.session.add(user)
            self.session.commit()
            return user
        except Exception as e:
            self.session.rollback()
            return None
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """用户认证"""
        user = self.get_by_username(username)
        if user and user.check_password(password) and user.is_active:
            return user
        return None
    
    def get_admins(self) -> List[User]:
        """获取管理员用户"""
        return self.get_by_filter(role=UserRole.ADMIN)
    
    def activate_user(self, user_id: int) -> bool:
        """激活用户"""
        return self.update(user_id, is_active=True) is not None
    
    def deactivate_user(self, user_id: int) -> bool:
        """停用用户"""
        return self.update(user_id, is_active=False) is not None
