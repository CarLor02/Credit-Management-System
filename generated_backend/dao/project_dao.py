"""
项目数据访问对象
"""

from typing import List, Optional
from datetime import datetime
from dao.base_dao import BaseDAO
from db_models import Project, ProjectStatus, ProjectType, User

class ProjectDAO(BaseDAO):
    """项目数据访问对象"""
    
    def __init__(self):
        super().__init__(Project)
    
    def get_by_user(self, user_id: int) -> List[Project]:
        """获取用户相关的项目"""
        return self.get_by_filter(created_by=user_id)
    
    def get_by_status(self, status: ProjectStatus) -> List[Project]:
        """根据状态获取项目"""
        return self.get_by_filter(status=status)
    
    def get_by_type(self, project_type: ProjectType) -> List[Project]:
        """根据类型获取项目"""
        return self.get_by_filter(type=project_type)
    
    def create_project(self, name: str, project_type: ProjectType, 
                      created_by: int, description: str = None) -> Optional[Project]:
        """创建项目"""
        return self.create(
            name=name,
            type=project_type,
            created_by=created_by,
            description=description,
            status=ProjectStatus.COLLECTING
        )
    
    def update_status(self, project_id: int, status: ProjectStatus) -> Optional[Project]:
        """更新项目状态"""
        return self.update(project_id, status=status)
    
    def get_recent_projects(self, user_id: int, limit: int = 10) -> List[Project]:
        """获取用户最近的项目"""
        try:
            return self.session.query(Project)\
                .filter_by(created_by=user_id)\
                .order_by(Project.created_at.desc())\
                .limit(limit)\
                .all()
        except Exception as e:
            return []
    
    def search_projects(self, keyword: str, user_id: int = None) -> List[Project]:
        """搜索项目"""
        try:
            query = self.session.query(Project)
            
            if user_id:
                query = query.filter_by(created_by=user_id)
            
            query = query.filter(
                Project.name.contains(keyword) | 
                Project.description.contains(keyword)
            )
            
            return query.all()
        except Exception as e:
            return []
