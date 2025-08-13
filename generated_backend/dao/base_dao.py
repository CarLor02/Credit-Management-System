"""
数据访问对象基类
提供通用的数据库操作方法
"""

from typing import List, Optional, Dict, Any, Type, TypeVar
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Query
from flask import current_app
from database import db

# 定义泛型类型
T = TypeVar('T', bound=db.Model)

class BaseDAO:
    """基础数据访问对象"""
    
    def __init__(self, model_class: Type[T]):
        """
        初始化DAO
        
        Args:
            model_class: SQLAlchemy模型类
        """
        self.model_class = model_class
        self.session = db.session
    
    def get_by_id(self, id: int) -> Optional[T]:
        """
        根据ID获取记录
        
        Args:
            id: 记录ID
            
        Returns:
            模型实例或None
        """
        try:
            return self.session.get(self.model_class, id)
        except SQLAlchemyError as e:
            current_app.logger.error(f"获取记录失败 (ID: {id}): {e}")
            return None
    
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """
        获取所有记录
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            模型实例列表
        """
        try:
            query = self.session.query(self.model_class)
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
                
            return query.all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"获取所有记录失败: {e}")
            return []
    
    def get_by_filter(self, **filters) -> List[T]:
        """
        根据条件筛选记录
        
        Args:
            **filters: 筛选条件
            
        Returns:
            模型实例列表
        """
        try:
            query = self.session.query(self.model_class)
            
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
            
            return query.all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"筛选记录失败: {e}")
            return []
    
    def get_one_by_filter(self, **filters) -> Optional[T]:
        """
        根据条件获取单条记录
        
        Args:
            **filters: 筛选条件
            
        Returns:
            模型实例或None
        """
        try:
            records = self.get_by_filter(**filters)
            return records[0] if records else None
        except Exception as e:
            current_app.logger.error(f"获取单条记录失败: {e}")
            return None
    
    def create(self, **data) -> Optional[T]:
        """
        创建新记录
        
        Args:
            **data: 记录数据
            
        Returns:
            创建的模型实例或None
        """
        try:
            instance = self.model_class(**data)
            self.session.add(instance)
            self.session.commit()
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            current_app.logger.error(f"创建记录失败: {e}")
            return None
    
    def update(self, id: int, **data) -> Optional[T]:
        """
        更新记录
        
        Args:
            id: 记录ID
            **data: 更新数据
            
        Returns:
            更新的模型实例或None
        """
        try:
            instance = self.get_by_id(id)
            if not instance:
                return None
            
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            self.session.commit()
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            current_app.logger.error(f"更新记录失败 (ID: {id}): {e}")
            return None
    
    def delete(self, id: int) -> bool:
        """
        删除记录
        
        Args:
            id: 记录ID
            
        Returns:
            是否删除成功
        """
        try:
            instance = self.get_by_id(id)
            if not instance:
                return False
            
            self.session.delete(instance)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            current_app.logger.error(f"删除记录失败 (ID: {id}): {e}")
            return False
    
    def count(self, **filters) -> int:
        """
        统计记录数量
        
        Args:
            **filters: 筛选条件
            
        Returns:
            记录数量
        """
        try:
            query = self.session.query(self.model_class)
            
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
            
            return query.count()
        except SQLAlchemyError as e:
            current_app.logger.error(f"统计记录数量失败: {e}")
            return 0
    
    def exists(self, **filters) -> bool:
        """
        检查记录是否存在
        
        Args:
            **filters: 筛选条件
            
        Returns:
            是否存在
        """
        return self.count(**filters) > 0
    
    def paginate(self, page: int = 1, per_page: int = 20, **filters) -> Dict[str, Any]:
        """
        分页查询
        
        Args:
            page: 页码
            per_page: 每页数量
            **filters: 筛选条件
            
        Returns:
            分页结果字典
        """
        try:
            query = self.session.query(self.model_class)
            
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
            
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return {
                'items': pagination.items,
                'total': pagination.total,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'prev_num': pagination.prev_num,
                'next_num': pagination.next_num
            }
        except SQLAlchemyError as e:
            current_app.logger.error(f"分页查询失败: {e}")
            return {
                'items': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'pages': 0,
                'has_prev': False,
                'has_next': False,
                'prev_num': None,
                'next_num': None
            }
    
    def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[T]:
        """
        批量创建记录
        
        Args:
            data_list: 数据列表
            
        Returns:
            创建的模型实例列表
        """
        try:
            instances = [self.model_class(**data) for data in data_list]
            self.session.add_all(instances)
            self.session.commit()
            return instances
        except SQLAlchemyError as e:
            self.session.rollback()
            current_app.logger.error(f"批量创建记录失败: {e}")
            return []
    
    def execute_raw_sql(self, sql: str, params: Optional[Dict] = None) -> Any:
        """
        执行原生SQL
        
        Args:
            sql: SQL语句
            params: 参数字典
            
        Returns:
            查询结果
        """
        try:
            result = self.session.execute(db.text(sql), params or {})
            self.session.commit()
            return result
        except SQLAlchemyError as e:
            self.session.rollback()
            current_app.logger.error(f"执行SQL失败: {e}")
            return None

class TransactionManager:
    """事务管理器"""
    
    def __init__(self):
        self.session = db.session
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
    
    def rollback(self):
        """回滚事务"""
        self.session.rollback()
    
    def commit(self):
        """提交事务"""
        self.session.commit()

# 使用示例：
# with TransactionManager() as tm:
#     user_dao.create(username='test', email='test@example.com')
#     project_dao.create(name='test project', created_by=1)
#     # 如果任何操作失败，整个事务都会回滚
