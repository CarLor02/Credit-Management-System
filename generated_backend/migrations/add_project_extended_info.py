#!/usr/bin/env python3
"""
添加项目扩展信息字段的数据库迁移脚本
"""

import os
import sys
import json
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from config import Config
from database import init_db
from db_models import Project, ProjectType

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)
    return app

def add_extended_info_columns():
    """添加扩展信息字段"""
    app = create_app()
    
    with app.app_context():
        from database import db
        
        print("开始添加项目扩展信息字段...")
        
        try:
            # 检查字段是否已存在
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('projects')]
            
            if 'company_info' not in columns:
                # 添加新字段
                db.engine.execute('ALTER TABLE projects ADD COLUMN company_info JSON')
                print("✓ 添加 company_info 字段")
            
            if 'personal_info' not in columns:
                db.engine.execute('ALTER TABLE projects ADD COLUMN personal_info JSON')
                print("✓ 添加 personal_info 字段")
                
            if 'financial_data' not in columns:
                db.engine.execute('ALTER TABLE projects ADD COLUMN financial_data JSON')
                print("✓ 添加 financial_data 字段")
            
            # 为现有项目添加示例数据
            projects = Project.query.all()
            for project in projects:
                if project.type == ProjectType.ENTERPRISE and not project.company_info:
                    # 企业项目示例数据
                    project.company_info = {
                        "registeredCapital": "1000万元",
                        "establishDate": "2015-03-15",
                        "industry": "科技服务",
                        "employees": "50-200人",
                        "legalPerson": "张总",
                        "businessScope": "软件开发、技术咨询、系统集成"
                    }
                    project.financial_data = {
                        "annualRevenue": "5000万元",
                        "totalAssets": "2500万元",
                        "liabilities": "800万元",
                        "netProfit": "500万元"
                    }
                    print(f"✓ 为企业项目 '{project.name}' 添加示例数据")
                
                elif project.type == ProjectType.INDIVIDUAL and not project.personal_info:
                    # 个人项目示例数据
                    project.personal_info = {
                        "age": 32,
                        "education": "本科",
                        "profession": "软件工程师",
                        "workYears": 8,
                        "monthlyIncome": "15000元",
                        "maritalStatus": "已婚"
                    }
                    project.financial_data = {
                        "monthlyIncome": "15000元",
                        "monthlyExpense": "8000元",
                        "savings": "50万元",
                        "debts": "80万元"
                    }
                    print(f"✓ 为个人项目 '{project.name}' 添加示例数据")
            
            db.session.commit()
            print("✅ 项目扩展信息字段添加完成！")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 迁移失败: {e}")
            return False
            
        return True

def rollback_extended_info_columns():
    """回滚扩展信息字段"""
    app = create_app()
    
    with app.app_context():
        from database import db
        
        print("开始回滚项目扩展信息字段...")
        
        try:
            # SQLite 不支持 DROP COLUMN，所以我们只清空数据
            projects = Project.query.all()
            for project in projects:
                project.company_info = None
                project.personal_info = None
                project.financial_data = None
            
            db.session.commit()
            print("✅ 扩展信息字段回滚完成！")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 回滚失败: {e}")
            return False
            
        return True

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback_extended_info_columns()
    else:
        add_extended_info_columns()
