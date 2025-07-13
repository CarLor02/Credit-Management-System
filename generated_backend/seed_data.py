"""
数据库种子数据
用于初始化测试数据
"""

import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from database import db
from db_models import (
    User, Project, Document, ProjectMember, AnalysisReport, 
    KnowledgeBase, SystemLog, SystemSetting,
    UserRole, ProjectType, ProjectStatus, Priority, RiskLevel,
    DocumentStatus, ProjectMemberRole, ReportType, ReportStatus,
    KnowledgeBaseStatus
)

def create_seed_data():
    """创建种子数据"""
    print("开始创建种子数据...")
    
    # 创建用户
    users = create_users()
    
    # 创建项目
    projects = create_projects(users)
    
    # 创建项目成员
    create_project_members(projects, users)
    
    # 创建文档
    create_documents(projects, users)
    
    # 创建知识库
    create_knowledge_bases(projects)
    
    # 创建分析报告
    create_analysis_reports(projects, users)
    
    # 创建系统设置
    create_system_settings()
    
    # 创建系统日志
    create_system_logs(users)
    
    db.session.commit()
    print("种子数据创建完成!")

def create_users():
    """创建用户数据"""
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@example.com',
            'password': 'admin123',
            'full_name': '系统管理员',
            'role': UserRole.ADMIN
        },
        {
            'username': 'manager1',
            'email': 'manager1@example.com',
            'password': 'manager123',
            'full_name': '项目经理张三',
            'role': UserRole.MANAGER
        },
        {
            'username': 'analyst1',
            'email': 'analyst1@example.com',
            'password': 'analyst123',
            'full_name': '分析师李四',
            'role': UserRole.ANALYST
        },
        {
            'username': 'user1',
            'email': 'user1@example.com',
            'password': 'user123',
            'full_name': '普通用户王五',
            'role': UserRole.USER
        },
        {
            'username': 'user2',
            'email': 'user2@example.com',
            'password': 'user123',
            'full_name': '普通用户赵六',
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
            full_name=user_data['full_name'],
            role=user_data['role'],
            is_active=True,
            last_login=datetime.utcnow() - timedelta(days=1)
        )
        user.set_password(user_data['password'])
        db.session.add(user)
        users.append(user)
        created_count += 1

    db.session.flush()  # 获取ID
    print(f"创建了 {created_count} 个新用户，跳过了 {len(users_data) - created_count} 个已存在的用户")
    return users

def create_projects(users):
    """创建项目数据"""
    projects_data = [
        {
            'name': '腾讯科技有限公司',
            'type': ProjectType.ENTERPRISE,
            'status': ProjectStatus.COMPLETED,
            'description': '腾讯科技有限公司征信分析项目',
            'category': 'technology',
            'priority': Priority.HIGH,
            'score': 85,
            'risk_level': RiskLevel.LOW,
            'progress': 100,
            'created_by': users[1].id,  # manager1
            'assigned_to': users[2].id  # analyst1
        },
        {
            'name': '阿里巴巴集团',
            'type': ProjectType.ENTERPRISE,
            'status': ProjectStatus.PROCESSING,
            'description': '阿里巴巴集团征信评估项目',
            'category': 'technology',
            'priority': Priority.HIGH,
            'score': 78,
            'risk_level': RiskLevel.MEDIUM,
            'progress': 75,
            'created_by': users[1].id,
            'assigned_to': users[2].id
        },
        {
            'name': '张三个人征信',
            'type': ProjectType.INDIVIDUAL,
            'status': ProjectStatus.COLLECTING,
            'description': '张三个人征信分析',
            'category': 'individual',
            'priority': Priority.MEDIUM,
            'score': 92,
            'risk_level': RiskLevel.LOW,
            'progress': 45,
            'created_by': users[3].id,  # user1
            'assigned_to': users[2].id
        },
        {
            'name': '字节跳动科技',
            'type': ProjectType.ENTERPRISE,
            'status': ProjectStatus.COMPLETED,
            'description': '字节跳动科技征信分析',
            'category': 'technology',
            'priority': Priority.MEDIUM,
            'score': 65,
            'risk_level': RiskLevel.HIGH,
            'progress': 100,
            'created_by': users[1].id,
            'assigned_to': users[2].id
        },
        {
            'name': '李四个人征信',
            'type': ProjectType.INDIVIDUAL,
            'status': ProjectStatus.PROCESSING,
            'description': '李四个人征信评估',
            'category': 'individual',
            'priority': Priority.LOW,
            'score': 88,
            'risk_level': RiskLevel.LOW,
            'progress': 80,
            'created_by': users[4].id,  # user2
            'assigned_to': users[2].id
        },
        {
            'name': '美团点评',
            'type': ProjectType.ENTERPRISE,
            'status': ProjectStatus.COMPLETED,
            'description': '美团点评征信分析项目',
            'category': 'retail',
            'priority': Priority.MEDIUM,
            'score': 76,
            'risk_level': RiskLevel.MEDIUM,
            'progress': 100,
            'created_by': users[1].id,
            'assigned_to': users[2].id
        }
    ]
    
    projects = []
    for project_data in projects_data:
        project = Project(**project_data)
        db.session.add(project)
        projects.append(project)
    
    db.session.flush()
    print(f"创建了 {len(projects)} 个项目")
    return projects

def create_project_members(projects, users):
    """创建项目成员数据"""
    members_data = [
        # 腾讯项目成员
        {'project_id': projects[0].id, 'user_id': users[1].id, 'role': ProjectMemberRole.OWNER},
        {'project_id': projects[0].id, 'user_id': users[2].id, 'role': ProjectMemberRole.ANALYST},
        {'project_id': projects[0].id, 'user_id': users[3].id, 'role': ProjectMemberRole.VIEWER},

        # 阿里项目成员
        {'project_id': projects[1].id, 'user_id': users[1].id, 'role': ProjectMemberRole.OWNER},
        {'project_id': projects[1].id, 'user_id': users[2].id, 'role': ProjectMemberRole.ANALYST},

        # 张三个人项目成员
        {'project_id': projects[2].id, 'user_id': users[3].id, 'role': ProjectMemberRole.OWNER},
        {'project_id': projects[2].id, 'user_id': users[2].id, 'role': ProjectMemberRole.ANALYST},

        # 字节跳动项目成员
        {'project_id': projects[3].id, 'user_id': users[1].id, 'role': ProjectMemberRole.OWNER},
        {'project_id': projects[3].id, 'user_id': users[2].id, 'role': ProjectMemberRole.ANALYST},

        # 李四个人项目成员
        {'project_id': projects[4].id, 'user_id': users[4].id, 'role': ProjectMemberRole.OWNER},
        {'project_id': projects[4].id, 'user_id': users[2].id, 'role': ProjectMemberRole.ANALYST},

        # 美团项目成员
        {'project_id': projects[5].id, 'user_id': users[1].id, 'role': ProjectMemberRole.OWNER},
        {'project_id': projects[5].id, 'user_id': users[2].id, 'role': ProjectMemberRole.ANALYST},
    ]

    for member_data in members_data:
        member = ProjectMember(**member_data)
        db.session.add(member)

    print(f"创建了 {len(members_data)} 个项目成员关系")

def create_documents(projects, users):
    """创建文档数据"""
    documents_data = [
        {
            'name': '财务报表2023.pdf',
            'original_filename': '财务报表2023.pdf',
            'file_path': '/uploads/documents/financial_report_2023.pdf',
            'file_size': 2411520,  # 2.3MB
            'file_type': 'pdf',
            'mime_type': 'application/pdf',
            'project_id': projects[0].id,
            'status': DocumentStatus.COMPLETED,
            'progress': 100,
            'upload_by': users[2].id
        },
        {
            'name': '营业执照.jpg',
            'original_filename': '营业执照.jpg',
            'file_path': '/uploads/documents/business_license.jpg',
            'file_size': 876544,  # 856KB
            'file_type': 'image',
            'mime_type': 'image/jpeg',
            'project_id': projects[1].id,
            'status': DocumentStatus.PROCESSING,
            'progress': 65,
            'upload_by': users[2].id
        },
        {
            'name': '银行流水明细.xlsx',
            'original_filename': '银行流水明细.xlsx',
            'file_path': '/uploads/documents/bank_statement.xlsx',
            'file_size': 1258291,  # 1.2MB
            'file_type': 'excel',
            'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'project_id': projects[2].id,
            'status': DocumentStatus.COMPLETED,
            'progress': 100,
            'upload_by': users[3].id
        },
        {
            'name': '信用报告.pdf',
            'original_filename': '信用报告.pdf',
            'file_path': '/uploads/documents/credit_report.pdf',
            'file_size': 3251200,  # 3.1MB
            'file_type': 'pdf',
            'mime_type': 'application/pdf',
            'project_id': projects[3].id,
            'status': DocumentStatus.FAILED,
            'progress': 0,
            'upload_by': users[2].id,
            'error_message': '文档解析失败：格式不支持'
        },
        {
            'name': '身份证明.pdf',
            'original_filename': '身份证明.pdf',
            'file_path': '/uploads/documents/id_document.pdf',
            'file_size': 1887436,  # 1.8MB
            'file_type': 'pdf',
            'mime_type': 'application/pdf',
            'project_id': projects[4].id,
            'status': DocumentStatus.PROCESSING,
            'progress': 30,
            'upload_by': users[4].id
        },
        {
            'name': '公司章程.docx',
            'original_filename': '公司章程.docx',
            'file_path': '/uploads/documents/company_charter.docx',
            'file_size': 967680,  # 945KB
            'file_type': 'word',
            'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'project_id': projects[5].id,
            'status': DocumentStatus.COMPLETED,
            'progress': 100,
            'upload_by': users[2].id
        }
    ]

    for doc_data in documents_data:
        document = Document(**doc_data)
        db.session.add(document)

    print(f"创建了 {len(documents_data)} 个文档")

def create_knowledge_bases(projects):
    """创建知识库数据"""
    for project in projects:
        kb = KnowledgeBase(
            name=f"{project.name}_知识库",
            project_id=project.id,
            dataset_id=f"dataset_{project.id}",
            status=KnowledgeBaseStatus.READY if project.status == ProjectStatus.COMPLETED else KnowledgeBaseStatus.CREATING,
            document_count=len(list(project.documents)),
            parsing_complete=project.status == ProjectStatus.COMPLETED
        )
        db.session.add(kb)

    print(f"创建了 {len(projects)} 个知识库")

def create_analysis_reports(projects, users):
    """创建分析报告数据"""
    reports_data = [
        {
            'project_id': projects[0].id,
            'title': '腾讯科技征信分析报告',
            'content': '基于提交的财务报表和相关文档，腾讯科技有限公司展现出良好的财务状况...',
            'report_type': ReportType.CREDIT_ANALYSIS,
            'status': ReportStatus.COMPLETED,
            'generated_by': users[2].id,
            'workflow_run_id': 'wf_001',
            'report_metadata': {'score': 85, 'risk_factors': ['市场竞争', '技术更新']}
        },
        {
            'project_id': projects[1].id,
            'title': '阿里巴巴风险评估报告',
            'content': '阿里巴巴集团在电商领域具有领先地位，但面临监管政策变化的风险...',
            'report_type': ReportType.RISK_ASSESSMENT,
            'status': ReportStatus.GENERATING,
            'generated_by': users[2].id,
            'workflow_run_id': 'wf_002'
        },
        {
            'project_id': projects[3].id,
            'title': '字节跳动综合分析报告',
            'content': '字节跳动在短视频和信息流领域表现突出，但国际化业务面临挑战...',
            'report_type': ReportType.SUMMARY,
            'status': ReportStatus.COMPLETED,
            'generated_by': users[2].id,
            'workflow_run_id': 'wf_003',
            'report_metadata': {'score': 65, 'recommendations': ['加强合规管理', '优化业务结构']}
        }
    ]

    for report_data in reports_data:
        report = AnalysisReport(**report_data)
        db.session.add(report)

    print(f"创建了 {len(reports_data)} 个分析报告")

def create_system_settings():
    """创建系统设置数据"""
    settings_data = [
        {
            'key': 'system_name',
            'value': '征信管理系统',
            'description': '系统名称',
            'category': 'general',
            'is_public': True
        },
        {
            'key': 'max_file_size',
            'value': '16777216',  # 16MB
            'description': '最大文件上传大小（字节）',
            'category': 'upload',
            'is_public': False
        },
        {
            'key': 'allowed_file_types',
            'value': 'pdf,doc,docx,xls,xlsx,txt,jpg,jpeg,png',
            'description': '允许上传的文件类型',
            'category': 'upload',
            'is_public': False
        },
        {
            'key': 'session_timeout',
            'value': '3600',  # 1小时
            'description': '会话超时时间（秒）',
            'category': 'security',
            'is_public': False
        },
        {
            'key': 'enable_registration',
            'value': 'false',
            'description': '是否允许用户注册',
            'category': 'security',
            'is_public': True
        }
    ]

    for setting_data in settings_data:
        setting = SystemSetting(**setting_data)
        db.session.add(setting)

    print(f"创建了 {len(settings_data)} 个系统设置")

def create_system_logs(users):
    """创建系统日志数据"""
    logs_data = [
        {
            'user_id': users[0].id,
            'action': 'user_login',
            'details': '管理员登录系统',
            'ip_address': '192.168.1.100',
            'created_at': datetime.utcnow() - timedelta(hours=2)
        },
        {
            'user_id': users[1].id,
            'action': 'project_create',
            'resource_type': 'project',
            'resource_id': 1,
            'details': '创建项目：腾讯科技有限公司',
            'ip_address': '192.168.1.101',
            'created_at': datetime.utcnow() - timedelta(hours=1)
        },
        {
            'user_id': users[2].id,
            'action': 'document_upload',
            'resource_type': 'document',
            'resource_id': 1,
            'details': '上传文档：财务报表2023.pdf',
            'ip_address': '192.168.1.102',
            'created_at': datetime.utcnow() - timedelta(minutes=30)
        }
    ]

    for log_data in logs_data:
        log = SystemLog(**log_data)
        db.session.add(log)

    print(f"创建了 {len(logs_data)} 个系统日志")
