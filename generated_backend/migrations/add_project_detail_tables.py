#!/usr/bin/env python3
"""
添加项目详情相关表的数据库迁移脚本
包括：财务分析表、经营状况表、项目时间轴表
"""

import os
import sys
from datetime import datetime, date

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from config import Config
from database import init_db, db
import enum

# 定义枚举类型
class BusinessLicenseStatus(enum.Enum):
    """营业执照状态"""
    NORMAL = 'normal'
    EXPIRING = 'expiring'
    EXPIRED = 'expired'

class TaxRegistrationStatus(enum.Enum):
    """税务登记状态"""
    NORMAL = 'normal'
    ABNORMAL = 'abnormal'

class ComplianceStatus(enum.Enum):
    """合规状态"""
    COMPLIANT = 'compliant'
    WARNING = 'warning'
    VIOLATION = 'violation'

class EventType(enum.Enum):
    """事件类型"""
    MILESTONE = 'milestone'
    DOCUMENT = 'document'
    ANALYSIS = 'analysis'
    REVIEW = 'review'
    REPORT = 'report'
    OTHER = 'other'

class EventStatus(enum.Enum):
    """事件状态"""
    COMPLETED = 'completed'
    IN_PROGRESS = 'in_progress'
    PENDING = 'pending'
    CANCELLED = 'cancelled'

class Priority(enum.Enum):
    """优先级"""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'

class RiskLevel(enum.Enum):
    """风险等级"""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)
    return app

def create_financial_analysis_table():
    """创建财务分析表"""
    sql = """
    CREATE TABLE IF NOT EXISTS financial_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        
        -- 基础财务指标
        total_assets DECIMAL(15,2),
        annual_revenue DECIMAL(15,2),
        net_profit DECIMAL(15,2),
        debt_ratio DECIMAL(5,2),
        
        -- 流动性指标
        current_ratio DECIMAL(8,2),
        quick_ratio DECIMAL(8,2),
        cash_ratio DECIMAL(8,2),
        
        -- 盈利能力指标
        gross_profit_margin DECIMAL(5,2),
        net_profit_margin DECIMAL(5,2),
        roe DECIMAL(5,2),
        roa DECIMAL(5,2),
        
        -- 运营能力指标
        inventory_turnover DECIMAL(8,2),
        receivables_turnover DECIMAL(8,2),
        total_asset_turnover DECIMAL(8,2),
        
        -- 发展能力指标
        revenue_growth_rate DECIMAL(5,2),
        profit_growth_rate DECIMAL(5,2),
        
        -- 分析期间
        analysis_year INTEGER NOT NULL,
        analysis_quarter INTEGER,
        
        -- 元数据
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        UNIQUE(project_id, analysis_year, analysis_quarter)
    );
    """
    
    db.session.execute(sql)
    print("✅ 财务分析表创建成功")

def create_business_status_table():
    """创建经营状况表"""
    sql = """
    CREATE TABLE IF NOT EXISTS business_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        
        -- 经营资质状态
        business_license_status VARCHAR(20) DEFAULT 'normal',
        business_license_expiry DATE,
        tax_registration_status VARCHAR(20) DEFAULT 'normal',
        organization_code_status VARCHAR(20) DEFAULT 'normal',
        
        -- 合规状态
        legal_violations INTEGER DEFAULT 0,
        tax_compliance_status VARCHAR(20) DEFAULT 'normal',
        environmental_compliance VARCHAR(20) DEFAULT 'compliant',
        labor_compliance VARCHAR(20) DEFAULT 'compliant',
        
        -- 经营风险
        market_risk_level VARCHAR(20) DEFAULT 'low',
        financial_risk_level VARCHAR(20) DEFAULT 'low',
        operational_risk_level VARCHAR(20) DEFAULT 'low',
        
        -- 行业地位
        industry_ranking INTEGER,
        market_share DECIMAL(5,2),
        competitive_advantage TEXT,
        
        -- 经营状况评分
        overall_score INTEGER DEFAULT 0,
        qualification_score INTEGER DEFAULT 0,
        compliance_score INTEGER DEFAULT 0,
        risk_score INTEGER DEFAULT 0,
        
        -- 备注信息
        risk_factors TEXT,
        improvement_suggestions TEXT,
        
        -- 元数据
        evaluation_date DATE NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """
    
    db.session.execute(sql)
    print("✅ 经营状况表创建成功")

def create_project_timeline_table():
    """创建项目时间轴表"""
    sql = """
    CREATE TABLE IF NOT EXISTS project_timeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        
        -- 事件信息
        event_title VARCHAR(200) NOT NULL,
        event_description TEXT,
        event_type VARCHAR(20) DEFAULT 'other',
        
        -- 事件状态
        status VARCHAR(20) DEFAULT 'pending',
        priority VARCHAR(20) DEFAULT 'medium',
        
        -- 时间信息
        event_date DATE NOT NULL,
        planned_date DATE,
        completed_date DATE,
        
        -- 关联信息
        related_document_id INTEGER,
        related_user_id INTEGER,
        
        -- 进度信息
        progress INTEGER DEFAULT 0,
        
        -- 元数据
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (related_document_id) REFERENCES documents(id) ON DELETE SET NULL,
        FOREIGN KEY (related_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
    );
    """
    
    db.session.execute(sql)
    print("✅ 项目时间轴表创建成功")

def create_indexes():
    """创建索引"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_financial_analysis_project_id ON financial_analysis(project_id);",
        "CREATE INDEX IF NOT EXISTS idx_financial_analysis_year ON financial_analysis(analysis_year);",
        "CREATE INDEX IF NOT EXISTS idx_business_status_project_id ON business_status(project_id);",
        "CREATE INDEX IF NOT EXISTS idx_business_status_evaluation_date ON business_status(evaluation_date);",
        "CREATE INDEX IF NOT EXISTS idx_project_timeline_project_id ON project_timeline(project_id);",
        "CREATE INDEX IF NOT EXISTS idx_project_timeline_event_date ON project_timeline(event_date);",
        "CREATE INDEX IF NOT EXISTS idx_project_timeline_status ON project_timeline(status);",
    ]
    
    for index_sql in indexes:
        db.session.execute(index_sql)
    
    print("✅ 索引创建成功")

def run_migration():
    """运行迁移"""
    app = create_app()
    
    with app.app_context():
        print("开始创建项目详情相关表...")
        
        try:
            # 创建表
            create_financial_analysis_table()
            create_business_status_table()
            create_project_timeline_table()
            
            # 创建索引
            create_indexes()
            
            # 提交事务
            db.session.commit()
            
            print("✅ 所有表和索引创建完成")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 迁移失败: {e}")
            raise

def main():
    """主函数"""
    print("项目详情表迁移脚本")
    print("=" * 50)
    
    try:
        run_migration()
        print("\n🎉 迁移成功完成！")
        print("\n创建的表:")
        print("- financial_analysis (财务分析表)")
        print("- business_status (经营状况表)")
        print("- project_timeline (项目时间轴表)")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
