"""
自动生成的数据模型
基于前端接口和表单分析
"""

from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


@dataclass
class CreateProjectModalProps:
    """数据模型 - 来源: CreateProjectModal"""
    
    isOpen: bool
    
    onClose: str
    
    editData: str
    
    id: int
    
    name: str
    
    type: str
    
    description: str
    
    category: str
    
    priority: str
    
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CreateProjectModalProps':
        """从字典创建实例"""
        return cls(**data)
    
    def validate(self) -> List[str]:
        """验证数据"""
        errors = []
        
        
        if not self.isOpen:
            errors.append("isOpen 是必需的")
        
        
        
        if not self.onClose:
            errors.append("onClose 是必需的")
        
        
        
        if not self.id:
            errors.append("id 是必需的")
        
        
        
        if not self.name:
            errors.append("name 是必需的")
        
        
        
        if not self.type:
            errors.append("type 是必需的")
        
        
        
        if not self.description:
            errors.append("description 是必需的")
        
        
        
        if not self.category:
            errors.append("category 是必需的")
        
        
        
        if not self.priority:
            errors.append("priority 是必需的")
        
        
        return errors


@dataclass
class Project:
    """数据模型 - 来源: ProjectCard"""
    
    id: int
    
    name: str
    
    type: str
    
    status: str
    
    score: int
    
    riskLevel: str
    
    lastUpdate: str
    
    documents: int
    
    progress: int
    
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """从字典创建实例"""
        return cls(**data)
    
    def validate(self) -> List[str]:
        """验证数据"""
        errors = []
        
        
        if not self.id:
            errors.append("id 是必需的")
        
        
        
        if not self.name:
            errors.append("name 是必需的")
        
        
        
        if not self.type:
            errors.append("type 是必需的")
        
        
        
        if not self.status:
            errors.append("status 是必需的")
        
        
        
        if not self.score:
            errors.append("score 是必需的")
        
        
        
        if not self.riskLevel:
            errors.append("riskLevel 是必需的")
        
        
        
        if not self.lastUpdate:
            errors.append("lastUpdate 是必需的")
        
        
        
        if not self.documents:
            errors.append("documents 是必需的")
        
        
        
        if not self.progress:
            errors.append("progress 是必需的")
        
        
        return errors


@dataclass
class ProjectCardProps:
    """数据模型 - 来源: ProjectCard"""
    
    project: str
    
    onDelete: str
    
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectCardProps':
        """从字典创建实例"""
        return cls(**data)
    
    def validate(self) -> List[str]:
        """验证数据"""
        errors = []
        
        
        if not self.project:
            errors.append("project 是必需的")
        
        
        return errors


@dataclass
class StatsCardProps:
    """数据模型 - 来源: StatsCard"""
    
    title: str
    
    value: str
    
    change: str
    
    trend: str
    
    icon: str
    
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatsCardProps':
        """从字典创建实例"""
        return cls(**data)
    
    def validate(self) -> List[str]:
        """验证数据"""
        errors = []
        
        
        if not self.title:
            errors.append("title 是必需的")
        
        
        
        if not self.value:
            errors.append("value 是必需的")
        
        
        
        if not self.change:
            errors.append("change 是必需的")
        
        
        
        if not self.trend:
            errors.append("trend 是必需的")
        
        
        
        if not self.icon:
            errors.append("icon 是必需的")
        
        
        return errors


@dataclass
class DocumentListProps:
    """数据模型 - 来源: DocumentList"""
    
    activeTab: str
    
    searchQuery: str
    
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentListProps':
        """从字典创建实例"""
        return cls(**data)
    
    def validate(self) -> List[str]:
        """验证数据"""
        errors = []
        
        
        if not self.activeTab:
            errors.append("activeTab 是必需的")
        
        
        
        if not self.searchQuery:
            errors.append("searchQuery 是必需的")
        
        
        return errors


@dataclass
class ProjectDetailProps:
    """数据模型 - 来源: ProjectDetail"""
    
    projectId: str
    
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectDetailProps':
        """从字典创建实例"""
        return cls(**data)
    
    def validate(self) -> List[str]:
        """验证数据"""
        errors = []
        
        
        if not self.projectId:
            errors.append("projectId 是必需的")
        
        
        return errors



# 通用响应模型
@dataclass
class APIResponse:
    """API响应模型"""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# 分页响应模型
@dataclass
class PaginatedResponse:
    """分页响应模型"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)