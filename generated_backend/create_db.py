#!/usr/bin/env python3
"""
简单的数据库创建脚本
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database import db
from db_models import User, Project, Document, ProjectType, ProjectStatus, Priority, RiskLevel, DocumentStatus, UserRole
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_database():
    """创建数据库和表"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化数据库
    db.init_app(app)
    
    with app.app_context():
        # 删除所有表（如果存在）
        db.drop_all()
        print("已删除所有现有表")
        
        # 创建所有表
        db.create_all()
        print("已创建所有数据库表")
        
        # 创建基础用户
        admin_user = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            phone='13800138000',
            role=UserRole.ADMIN,
            is_active=True,
            last_login=datetime.now(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.session.add(admin_user)
        db.session.commit()
        print("已创建管理员用户")
        
        # 创建示例项目
        projects_data = [
            {
                'name': '阿里巴巴集团征信评估',
                'type': ProjectType.ENTERPRISE,
                'status': ProjectStatus.PROCESSING,
                'description': '对阿里巴巴集团进行全面的征信评估分析',
                'category': '大型企业',
                'priority': Priority.HIGH,
                'score': 85,
                'risk_level': RiskLevel.LOW,
                'progress': 75,
                'created_by': admin_user.id
            },
            {
                'name': '腾讯控股征信分析',
                'type': ProjectType.ENTERPRISE,
                'status': ProjectStatus.COMPLETED,
                'description': '腾讯控股有限公司征信状况分析',
                'category': '互联网企业',
                'priority': Priority.HIGH,
                'score': 92,
                'risk_level': RiskLevel.LOW,
                'progress': 100,
                'created_by': admin_user.id
            },
            {
                'name': '张三个人征信评估',
                'type': ProjectType.INDIVIDUAL,
                'status': ProjectStatus.COLLECTING,
                'description': '个人客户张三的征信评估',
                'category': '个人客户',
                'priority': Priority.MEDIUM,
                'score': 0,
                'risk_level': RiskLevel.MEDIUM,
                'progress': 25,
                'created_by': admin_user.id
            }
        ]
        
        created_projects = []
        for project_data in projects_data:
            project = Project(**project_data)
            db.session.add(project)
            created_projects.append(project)
        
        db.session.commit()
        print(f"已创建 {len(created_projects)} 个示例项目")
        
        # 创建示例文档
        documents_data = [
            {
                'name': '营业执照.pdf',
                'original_filename': '营业执照.pdf',
                'file_path': '/uploads/business_license.pdf',
                'file_size': 1024000,
                'file_type': 'pdf',
                'mime_type': 'application/pdf',
                'project_id': created_projects[0].id,
                'status': DocumentStatus.COMPLETED,
                'progress': 100,
                'upload_by': admin_user.id
            },
            {
                'name': '财务报表.xlsx',
                'original_filename': '财务报表.xlsx',
                'file_path': '/uploads/financial_report.xlsx',
                'file_size': 2048000,
                'file_type': 'xlsx',
                'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'project_id': created_projects[0].id,
                'status': DocumentStatus.PROCESSING,
                'progress': 60,
                'upload_by': admin_user.id
            },
            {
                'name': '身份证.jpg',
                'original_filename': '身份证.jpg',
                'file_path': '/uploads/id_card.jpg',
                'file_size': 512000,
                'file_type': 'jpg',
                'mime_type': 'image/jpeg',
                'project_id': created_projects[2].id,
                'status': DocumentStatus.COMPLETED,
                'progress': 100,
                'upload_by': admin_user.id
            },
            {
                'name': '银行流水.pdf',
                'original_filename': '银行流水.pdf',
                'file_path': '/uploads/bank_statement.pdf',
                'file_size': 1536000,
                'file_type': 'pdf',
                'mime_type': 'application/pdf',
                'project_id': created_projects[2].id,
                'status': DocumentStatus.FAILED,
                'progress': 0,
                'upload_by': admin_user.id,
                'error_message': '文件格式不支持'
            }
        ]
        
        for doc_data in documents_data:
            document = Document(**doc_data)
            db.session.add(document)
        
        db.session.commit()
        print(f"已创建 {len(documents_data)} 个示例文档")
        
        print("数据库初始化完成！")

if __name__ == '__main__':
    create_database()
