"""
数据库模型定义
使用SQLAlchemy ORM
"""

import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import JSON
import enum

from database import db

class UserRole(enum.Enum):
    """用户角色枚举"""
    ADMIN = 'admin'
    USER = 'user'

class ProjectType(enum.Enum):
    """项目类型枚举"""
    ENTERPRISE = 'enterprise'
    INDIVIDUAL = 'individual'

class ProjectStatus(enum.Enum):
    """项目状态枚举"""
    COLLECTING = 'collecting'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    ARCHIVED = 'archived'

class Priority(enum.Enum):
    """优先级枚举"""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'

class RiskLevel(enum.Enum):
    """风险等级枚举"""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'

class DocumentStatus(enum.Enum):
    """文档状态枚举"""
    UPLOADING = 'uploading'                    # 本地上传中
    PROCESSING = 'processing'                  # 处理文件中
    UPLOADING_TO_KB = 'uploading_to_kb'       # 上传知识库中
    PARSING_KB = 'parsing_kb'                  # 知识库解析中
    COMPLETED = 'completed'                    # 知识库解析成功
    FAILED = 'failed'                          # 失败
    KB_PARSE_FAILED = 'kb_parse_failed'        # 知识库解析失败

class ReportStatus(enum.Enum):
    """报告状态枚举"""
    NOT_GENERATED = 'not_generated'            # 未生成
    GENERATING = 'generating'                  # 正在生成
    GENERATED = 'generated'                    # 已生成

class ProjectMemberRole(enum.Enum):
    """项目成员角色枚举"""
    OWNER = 'owner'
    MANAGER = 'manager'
    ANALYST = 'analyst'
    VIEWER = 'viewer'

class ReportType(enum.Enum):
    """报告类型枚举"""
    CREDIT_ANALYSIS = 'credit_analysis'
    RISK_ASSESSMENT = 'risk_assessment'
    SUMMARY = 'summary'



class BusinessLicenseStatus(enum.Enum):
    """营业执照状态枚举"""
    NORMAL = 'normal'
    EXPIRING = 'expiring'
    EXPIRED = 'expired'

class TaxRegistrationStatus(enum.Enum):
    """税务登记状态枚举"""
    NORMAL = 'normal'
    ABNORMAL = 'abnormal'

class ComplianceStatus(enum.Enum):
    """合规状态枚举"""
    COMPLIANT = 'compliant'
    WARNING = 'warning'
    VIOLATION = 'violation'

class EventType(enum.Enum):
    """事件类型枚举"""
    MILESTONE = 'milestone'
    DOCUMENT = 'document'
    ANALYSIS = 'analysis'
    REVIEW = 'review'
    REPORT = 'report'
    OTHER = 'other'

class EventStatus(enum.Enum):
    """事件状态枚举"""
    COMPLETED = 'completed'
    IN_PROGRESS = 'in_progress'
    PENDING = 'pending'
    CANCELLED = 'cancelled'

class StatType(enum.Enum):
    """统计类型枚举"""
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))  # 手机号字段
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    avatar_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    created_projects = db.relationship('Project', foreign_keys='Project.created_by', backref='creator', lazy='dynamic')
    assigned_projects = db.relationship('Project', foreign_keys='Project.assigned_to', backref='assignee', lazy='dynamic')
    uploaded_documents = db.relationship('Document', backref='uploader', lazy='dynamic')
    project_memberships = db.relationship('ProjectMember', backref='user', lazy='dynamic')
    generated_reports = db.relationship('AnalysisReport', backref='generator', lazy='dynamic')
    system_logs = db.relationship('SystemLog', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """检查密码"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'role': self.role.value,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class Project(db.Model):
    """项目模型"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    folder_uuid = db.Column(db.String(36), nullable=False, unique=True)  # 用于文件夹命名的UUID
    type = db.Column(db.Enum(ProjectType), nullable=False)
    status = db.Column(db.Enum(ProjectStatus), default=ProjectStatus.COLLECTING, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    priority = db.Column(db.Enum(Priority), default=Priority.MEDIUM, nullable=False)
    score = db.Column(db.Integer, default=0)
    risk_level = db.Column(db.Enum(RiskLevel), default=RiskLevel.LOW, nullable=False)
    progress = db.Column(db.Integer, default=0)

    # 扩展信息字段 - 使用JSON存储灵活的结构化数据
    company_info = db.Column(JSON)  # 企业信息
    personal_info = db.Column(JSON)  # 个人信息
    financial_data = db.Column(JSON)  # 财务数据

    # 知识库相关字段
    dataset_id = db.Column(db.String(100))  # RAG知识库的dataset_id
    knowledge_base_name = db.Column(db.String(200))  # 知识库名称

    # 报告相关字段
    report_path = db.Column(db.String(500))  # 征信报告文件路径
    report_status = db.Column(db.Enum(ReportStatus), default=ReportStatus.NOT_GENERATED, nullable=False)  # 报告状态

    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    documents = db.relationship('Document', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    members = db.relationship('ProjectMember', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    reports = db.relationship('AnalysisReport', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value.lower(),  # 转换为小写
            'status': self.status.value.lower(),  # 转换为小写
            'description': self.description,
            'category': self.category,
            'priority': self.priority.value.lower(),  # 转换为小写
            'score': self.score,
            'riskLevel': self.risk_level.value.lower(),  # 转换为小写
            'progress': self.progress,
            'created_by': self.created_by,
            'assigned_to': self.assigned_to,
            'documents': len(list(self.documents)),
            'lastUpdate': self.updated_at.strftime('%Y-%m-%d'),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            # 报告相关
            'dataset_id': self.dataset_id,
            'knowledge_base_name': self.knowledge_base_name,
            'report_path': self.report_path,
            'report_status': self.report_status.value.lower(),  # 转换为小写
            # 扩展信息
            'companyInfo': self.company_info,
            'personalInfo': self.personal_info,
            'financialData': self.financial_data
        }
    
    def __repr__(self):
        return f'<Project {self.name}>'

class Document(db.Model):
    """文档模型"""
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    mime_type = db.Column(db.String(100))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    status = db.Column(db.Enum(DocumentStatus), default=DocumentStatus.UPLOADING, nullable=False)
    progress = db.Column(db.Integer, default=0)
    upload_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    processing_result = db.Column(db.Text)
    error_message = db.Column(db.Text)
    
    # 新增的文档处理相关字段
    processed_file_path = db.Column(db.String(500))  # 处理后的文件路径
    processing_started_at = db.Column(db.DateTime)   # 处理开始时间
    processed_at = db.Column(db.DateTime)            # 处理完成时间
    
    # 知识库相关字段
    rag_document_id = db.Column(db.String(100))      # RAG系统中的文档ID
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @property
    def filename(self):
        """文件名属性，返回原始文件名"""
        return self.original_filename

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'project': self.project.name if self.project else '',
            'type': self.get_frontend_file_type(),
            'size': self.format_file_size(),
            'status': self.status.value.lower(),  # 转换为小写
            'progress': self.progress,
            'uploadTime': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'upload_by': self.upload_by,
            'error_message': self.error_message,
            # 新增处理相关信息
            'processing_started_at': self.processing_started_at.isoformat() if self.processing_started_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'processed_file_path': self.processed_file_path,
            'has_processed_file': bool(self.processed_file_path and os.path.exists(self.processed_file_path)) if self.processed_file_path else False
        }

    def get_frontend_file_type(self):
        """获取前端期望的文件类型"""
        extension = self.file_type.lower()
        if extension in ['pdf']:
            return 'pdf'
        elif extension in ['xls', 'xlsx']:
            return 'excel'
        elif extension in ['doc', 'docx']:
            return 'word'
        elif extension in ['jpg', 'jpeg', 'png', 'gif']:
            return 'image'
        elif extension in ['markdown']:
            return 'markdown'
        else:
            return 'pdf'  # 默认返回pdf

    def format_file_size(self):
        """格式化文件大小"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"

    def __repr__(self):
        return f'<Document {self.name}>'

class ProjectMember(db.Model):
    """项目成员模型"""
    __tablename__ = 'project_members'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.Enum(ProjectMemberRole), default=ProjectMemberRole.VIEWER, nullable=False)
    permissions = db.Column(JSON)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (db.UniqueConstraint('project_id', 'user_id'),)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else '',
            'role': self.role.value,
            'permissions': self.permissions,
            'joined_at': self.joined_at.isoformat()
        }

    def __repr__(self):
        return f'<ProjectMember {self.user_id}@{self.project_id}>'

class AnalysisReport(db.Model):
    """分析报告模型"""
    __tablename__ = 'analysis_reports'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    report_type = db.Column(db.Enum(ReportType), nullable=False)
    status = db.Column(db.Enum(ReportStatus), default=ReportStatus.GENERATING, nullable=False)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    workflow_run_id = db.Column(db.String(100))
    report_metadata = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)



    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'title': self.title,
            'content': self.content,
            'report_type': self.report_type.value,
            'status': self.status.value,
            'generated_by': self.generated_by,
            'workflow_run_id': self.workflow_run_id,
            'metadata': self.report_metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<AnalysisReport {self.title}>'

class SystemLog(db.Model):
    """系统日志模型"""
    __tablename__ = 'system_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else 'System',
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<SystemLog {self.action}>'

class SystemSetting(db.Model):
    """系统设置模型"""
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default='general')
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'category': self.category,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<SystemSetting {self.key}>'

class DashboardStats(db.Model):
    """仪表板统计数据模型"""
    __tablename__ = 'dashboard_stats'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)  # 统计日期
    total_projects = db.Column(db.Integer, default=0)
    completed_projects = db.Column(db.Integer, default=0)
    processing_projects = db.Column(db.Integer, default=0)
    collecting_projects = db.Column(db.Integer, default=0)
    archived_projects = db.Column(db.Integer, default=0)
    total_documents = db.Column(db.Integer, default=0)
    completed_documents = db.Column(db.Integer, default=0)
    processing_documents = db.Column(db.Integer, default=0)
    failed_documents = db.Column(db.Integer, default=0)
    total_users = db.Column(db.Integer, default=0)
    active_users = db.Column(db.Integer, default=0)
    average_score = db.Column(db.Float, default=0.0)
    high_risk_projects = db.Column(db.Integer, default=0)
    medium_risk_projects = db.Column(db.Integer, default=0)
    low_risk_projects = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'total_projects': self.total_projects,
            'completed_projects': self.completed_projects,
            'processing_projects': self.processing_projects,
            'collecting_projects': self.collecting_projects,
            'archived_projects': self.archived_projects,
            'total_documents': self.total_documents,
            'completed_documents': self.completed_documents,
            'processing_documents': self.processing_documents,
            'failed_documents': self.failed_documents,
            'total_users': self.total_users,
            'active_users': self.active_users,
            'average_score': self.average_score,
            'high_risk_projects': self.high_risk_projects,
            'medium_risk_projects': self.medium_risk_projects,
            'low_risk_projects': self.low_risk_projects,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<DashboardStats {self.date}>'

class ActivityLog(db.Model):
    """活动日志模型 - 用于最近活动展示"""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # 活动类型
    title = db.Column(db.String(255), nullable=False)  # 活动标题
    description = db.Column(db.Text)  # 活动描述
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    resource_type = db.Column(db.String(50))  # 资源类型 (project, document, report等)
    resource_id = db.Column(db.Integer)  # 资源ID
    activity_metadata = db.Column(JSON)  # 额外的元数据
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    user = db.relationship('User', backref='activity_logs', lazy='select')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'description': self.description,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else 'System',
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'metadata': self.activity_metadata,
            'created_at': self.created_at.isoformat(),
            'relative_time': self.get_relative_time()
        }

    def get_relative_time(self):
        """获取相对时间"""
        now = datetime.utcnow()
        diff = now - self.created_at

        if diff.days > 0:
            return f"{diff.days}天前"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}小时前"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}分钟前"
        else:
            return "刚刚"

    def __repr__(self):
        return f'<ActivityLog {self.type}: {self.title}>'

class FinancialAnalysis(db.Model):
    """财务分析模型"""
    __tablename__ = 'financial_analysis'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)

    # 基础财务指标
    total_assets = db.Column(db.Numeric(15, 2))  # 资产总额
    annual_revenue = db.Column(db.Numeric(15, 2))  # 年营业收入
    net_profit = db.Column(db.Numeric(15, 2))  # 净利润
    debt_ratio = db.Column(db.Numeric(5, 2))  # 负债率(%)

    # 流动性指标
    current_ratio = db.Column(db.Numeric(8, 2))  # 流动比率
    quick_ratio = db.Column(db.Numeric(8, 2))  # 速动比率
    cash_ratio = db.Column(db.Numeric(8, 2))  # 现金比率

    # 盈利能力指标
    gross_profit_margin = db.Column(db.Numeric(5, 2))  # 毛利率(%)
    net_profit_margin = db.Column(db.Numeric(5, 2))  # 净利率(%)
    roe = db.Column(db.Numeric(5, 2))  # 净资产收益率(%)
    roa = db.Column(db.Numeric(5, 2))  # 总资产收益率(%)

    # 运营能力指标
    inventory_turnover = db.Column(db.Numeric(8, 2))  # 存货周转率
    receivables_turnover = db.Column(db.Numeric(8, 2))  # 应收账款周转率
    total_asset_turnover = db.Column(db.Numeric(8, 2))  # 总资产周转率

    # 发展能力指标
    revenue_growth_rate = db.Column(db.Numeric(5, 2))  # 营收增长率(%)
    profit_growth_rate = db.Column(db.Numeric(5, 2))  # 利润增长率(%)

    # 分析期间
    analysis_year = db.Column(db.Integer, nullable=False)  # 分析年度
    analysis_quarter = db.Column(db.Integer)  # 分析季度(1-4)

    # 元数据
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    project = db.relationship('Project', backref=db.backref('financial_analyses', cascade='all, delete-orphan'), lazy='select')

    # 唯一约束
    __table_args__ = (db.UniqueConstraint('project_id', 'analysis_year', 'analysis_quarter'),)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'total_assets': float(self.total_assets) if self.total_assets else None,
            'annual_revenue': float(self.annual_revenue) if self.annual_revenue else None,
            'net_profit': float(self.net_profit) if self.net_profit else None,
            'debt_ratio': float(self.debt_ratio) if self.debt_ratio else None,
            'current_ratio': float(self.current_ratio) if self.current_ratio else None,
            'quick_ratio': float(self.quick_ratio) if self.quick_ratio else None,
            'cash_ratio': float(self.cash_ratio) if self.cash_ratio else None,
            'gross_profit_margin': float(self.gross_profit_margin) if self.gross_profit_margin else None,
            'net_profit_margin': float(self.net_profit_margin) if self.net_profit_margin else None,
            'roe': float(self.roe) if self.roe else None,
            'roa': float(self.roa) if self.roa else None,
            'inventory_turnover': float(self.inventory_turnover) if self.inventory_turnover else None,
            'receivables_turnover': float(self.receivables_turnover) if self.receivables_turnover else None,
            'total_asset_turnover': float(self.total_asset_turnover) if self.total_asset_turnover else None,
            'revenue_growth_rate': float(self.revenue_growth_rate) if self.revenue_growth_rate else None,
            'profit_growth_rate': float(self.profit_growth_rate) if self.profit_growth_rate else None,
            'analysis_year': self.analysis_year,
            'analysis_quarter': self.analysis_quarter,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<FinancialAnalysis {self.project_id}-{self.analysis_year}Q{self.analysis_quarter or ""}>'

class BusinessStatus(db.Model):
    """经营状况模型"""
    __tablename__ = 'business_status'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)

    # 经营资质状态
    business_license_status = db.Column(db.Enum(BusinessLicenseStatus), default=BusinessLicenseStatus.NORMAL)
    business_license_expiry = db.Column(db.Date)
    tax_registration_status = db.Column(db.Enum(TaxRegistrationStatus), default=TaxRegistrationStatus.NORMAL)
    organization_code_status = db.Column(db.Enum(BusinessLicenseStatus), default=BusinessLicenseStatus.NORMAL)

    # 合规状态
    legal_violations = db.Column(db.Integer, default=0)  # 违法记录数量
    tax_compliance_status = db.Column(db.Enum(ComplianceStatus), default=ComplianceStatus.COMPLIANT)
    environmental_compliance = db.Column(db.Enum(ComplianceStatus), default=ComplianceStatus.COMPLIANT)
    labor_compliance = db.Column(db.Enum(ComplianceStatus), default=ComplianceStatus.COMPLIANT)

    # 经营风险
    market_risk_level = db.Column(db.Enum(RiskLevel), default=RiskLevel.LOW)
    financial_risk_level = db.Column(db.Enum(RiskLevel), default=RiskLevel.LOW)
    operational_risk_level = db.Column(db.Enum(RiskLevel), default=RiskLevel.LOW)

    # 行业地位
    industry_ranking = db.Column(db.Integer)  # 行业排名
    market_share = db.Column(db.Numeric(5, 2))  # 市场份额(%)
    competitive_advantage = db.Column(db.Text)  # 竞争优势描述

    # 经营状况评分
    overall_score = db.Column(db.Integer, default=0)  # 总体评分(0-100)
    qualification_score = db.Column(db.Integer, default=0)  # 资质评分
    compliance_score = db.Column(db.Integer, default=0)  # 合规评分
    risk_score = db.Column(db.Integer, default=0)  # 风险评分

    # 备注信息
    risk_factors = db.Column(db.Text)  # 风险因素描述
    improvement_suggestions = db.Column(db.Text)  # 改进建议

    # 元数据
    evaluation_date = db.Column(db.Date, nullable=False)  # 评估日期
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    project = db.relationship('Project', backref=db.backref('business_statuses', cascade='all, delete-orphan'), lazy='select')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'business_license_status': self.business_license_status.value if self.business_license_status else None,
            'business_license_expiry': self.business_license_expiry.isoformat() if self.business_license_expiry else None,
            'tax_registration_status': self.tax_registration_status.value if self.tax_registration_status else None,
            'organization_code_status': self.organization_code_status.value if self.organization_code_status else None,
            'legal_violations': self.legal_violations,
            'tax_compliance_status': self.tax_compliance_status.value if self.tax_compliance_status else None,
            'environmental_compliance': self.environmental_compliance.value if self.environmental_compliance else None,
            'labor_compliance': self.labor_compliance.value if self.labor_compliance else None,
            'market_risk_level': self.market_risk_level.value if self.market_risk_level else None,
            'financial_risk_level': self.financial_risk_level.value if self.financial_risk_level else None,
            'operational_risk_level': self.operational_risk_level.value if self.operational_risk_level else None,
            'industry_ranking': self.industry_ranking,
            'market_share': float(self.market_share) if self.market_share else None,
            'competitive_advantage': self.competitive_advantage,
            'overall_score': self.overall_score,
            'qualification_score': self.qualification_score,
            'compliance_score': self.compliance_score,
            'risk_score': self.risk_score,
            'risk_factors': self.risk_factors,
            'improvement_suggestions': self.improvement_suggestions,
            'evaluation_date': self.evaluation_date.isoformat(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<BusinessStatus {self.project_id}-{self.evaluation_date}>'

class ProjectTimeline(db.Model):
    """项目时间轴模型"""
    __tablename__ = 'project_timeline'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)

    # 事件信息
    event_title = db.Column(db.String(200), nullable=False)  # 事件标题
    event_description = db.Column(db.Text)  # 事件描述
    event_type = db.Column(db.Enum(EventType), default=EventType.OTHER)  # 事件类型

    # 事件状态
    status = db.Column(db.Enum(EventStatus), default=EventStatus.PENDING)  # 事件状态
    priority = db.Column(db.Enum(Priority), default=Priority.MEDIUM)  # 优先级

    # 时间信息
    event_date = db.Column(db.Date, nullable=False)  # 事件日期
    planned_date = db.Column(db.Date)  # 计划日期
    completed_date = db.Column(db.Date)  # 完成日期

    # 关联信息
    related_document_id = db.Column(db.Integer, db.ForeignKey('documents.id'))  # 关联文档ID
    related_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 关联用户ID

    # 进度信息
    progress = db.Column(db.Integer, default=0)  # 进度百分比(0-100)

    # 元数据
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    project = db.relationship('Project', backref=db.backref('timeline_events', cascade='all, delete-orphan'), lazy='select')
    related_document = db.relationship('Document', backref='timeline_events', lazy='select')
    related_user = db.relationship('User', foreign_keys=[related_user_id], backref='related_timeline_events', lazy='select')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_timeline_events', lazy='select')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'event_title': self.event_title,
            'event_description': self.event_description,
            'event_type': self.event_type.value if self.event_type else None,
            'status': self.status.value if self.status else None,
            'priority': self.priority.value if self.priority else None,
            'event_date': self.event_date.isoformat(),
            'planned_date': self.planned_date.isoformat() if self.planned_date else None,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'related_document_id': self.related_document_id,
            'related_document_name': self.related_document.name if self.related_document else None,
            'related_user_id': self.related_user_id,
            'related_user_name': self.related_user.username if self.related_user else None,
            'progress': self.progress,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<ProjectTimeline {self.project_id}: {self.event_title}>'

class StatisticsHistory(db.Model):
    """统计历史模型"""
    __tablename__ = 'statistics_history'

    id = db.Column(db.Integer, primary_key=True)

    # 统计时间信息
    stat_date = db.Column(db.Date, nullable=False)  # 统计日期
    stat_type = db.Column(db.Enum(StatType), default=StatType.DAILY)  # 统计类型

    # 项目统计
    total_projects = db.Column(db.Integer, default=0)
    enterprise_projects = db.Column(db.Integer, default=0)
    individual_projects = db.Column(db.Integer, default=0)

    # 项目状态统计
    collecting_projects = db.Column(db.Integer, default=0)
    processing_projects = db.Column(db.Integer, default=0)
    completed_projects = db.Column(db.Integer, default=0)
    archived_projects = db.Column(db.Integer, default=0)

    # 风险统计
    high_risk_projects = db.Column(db.Integer, default=0)
    medium_risk_projects = db.Column(db.Integer, default=0)
    low_risk_projects = db.Column(db.Integer, default=0)

    # 评分统计
    average_score = db.Column(db.Numeric(5, 2), default=0)
    min_score = db.Column(db.Integer, default=0)
    max_score = db.Column(db.Integer, default=0)

    # 文档统计
    total_documents = db.Column(db.Integer, default=0)
    completed_documents = db.Column(db.Integer, default=0)
    processing_documents = db.Column(db.Integer, default=0)
    failed_documents = db.Column(db.Integer, default=0)

    # 用户统计
    total_users = db.Column(db.Integer, default=0)
    active_users = db.Column(db.Integer, default=0)

    # 业务指标
    completion_rate = db.Column(db.Numeric(5, 2), default=0)
    doc_completion_rate = db.Column(db.Numeric(5, 2), default=0)

    # 新增统计（相比上一期）
    new_projects = db.Column(db.Integer, default=0)
    new_documents = db.Column(db.Integer, default=0)
    new_users = db.Column(db.Integer, default=0)

    # 元数据
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 唯一约束
    __table_args__ = (db.UniqueConstraint('stat_date', 'stat_type'),)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'stat_date': self.stat_date.isoformat(),
            'stat_type': self.stat_type.value if self.stat_type else None,
            'total_projects': self.total_projects,
            'enterprise_projects': self.enterprise_projects,
            'individual_projects': self.individual_projects,
            'collecting_projects': self.collecting_projects,
            'processing_projects': self.processing_projects,
            'completed_projects': self.completed_projects,
            'archived_projects': self.archived_projects,
            'high_risk_projects': self.high_risk_projects,
            'medium_risk_projects': self.medium_risk_projects,
            'low_risk_projects': self.low_risk_projects,
            'average_score': float(self.average_score) if self.average_score else 0,
            'min_score': self.min_score,
            'max_score': self.max_score,
            'total_documents': self.total_documents,
            'completed_documents': self.completed_documents,
            'processing_documents': self.processing_documents,
            'failed_documents': self.failed_documents,
            'total_users': self.total_users,
            'active_users': self.active_users,
            'completion_rate': float(self.completion_rate) if self.completion_rate else 0,
            'doc_completion_rate': float(self.doc_completion_rate) if self.doc_completion_rate else 0,
            'new_projects': self.new_projects,
            'new_documents': self.new_documents,
            'new_users': self.new_users,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<StatisticsHistory {self.stat_date}-{self.stat_type.value if self.stat_type else ""}>'
