"""
DAO工厂类
统一管理所有数据访问对象
"""

from dao.user_dao import UserDAO
from dao.project_dao import ProjectDAO
from dao.document_dao import DocumentDAO

class DAOFactory:
    """DAO工厂类"""
    
    _instances = {}
    
    @classmethod
    def get_user_dao(cls) -> UserDAO:
        """获取用户DAO"""
        if 'user' not in cls._instances:
            cls._instances['user'] = UserDAO()
        return cls._instances['user']
    
    @classmethod
    def get_project_dao(cls) -> ProjectDAO:
        """获取项目DAO"""
        if 'project' not in cls._instances:
            cls._instances['project'] = ProjectDAO()
        return cls._instances['project']
    
    @classmethod
    def get_document_dao(cls) -> DocumentDAO:
        """获取文档DAO"""
        if 'document' not in cls._instances:
            cls._instances['document'] = DocumentDAO()
        return cls._instances['document']
    
    @classmethod
    def clear_cache(cls):
        """清除DAO缓存"""
        cls._instances.clear()

# 便捷的全局访问方法
def get_user_dao() -> UserDAO:
    """获取用户DAO"""
    return DAOFactory.get_user_dao()

def get_project_dao() -> ProjectDAO:
    """获取项目DAO"""
    return DAOFactory.get_project_dao()

def get_document_dao() -> DocumentDAO:
    """获取文档DAO"""
    return DAOFactory.get_document_dao()
