#!/usr/bin/env python3
"""
为项目详情表创建种子数据
包括财务分析、经营状况、时间轴数据
"""

import os
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from database import init_db, db
from db_models import (
    Project, FinancialAnalysis, BusinessStatus, ProjectTimeline,
    BusinessLicenseStatus, TaxRegistrationStatus, ComplianceStatus,
    EventType, EventStatus, Priority, RiskLevel, ProjectType
)

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)
    return app

def create_financial_analysis_data():
    """创建财务分析数据"""
    print("创建财务分析数据...")
    
    # 获取所有企业项目
    enterprise_projects = Project.query.filter_by(type=ProjectType.ENTERPRISE).all()
    
    for project in enterprise_projects:
        # 为每个项目创建2023年和2024年的财务数据
        for year in [2023, 2024]:
            # 生成模拟财务数据
            base_revenue = random.uniform(50000000, 500000000)  # 5千万到5亿
            base_assets = base_revenue * random.uniform(1.2, 2.5)
            
            financial_data = FinancialAnalysis(
                project_id=project.id,
                analysis_year=year,
                analysis_quarter=None,  # 年度数据
                
                # 基础财务指标
                total_assets=Decimal(str(round(base_assets, 2))),
                annual_revenue=Decimal(str(round(base_revenue, 2))),
                net_profit=Decimal(str(round(base_revenue * random.uniform(0.05, 0.15), 2))),
                debt_ratio=Decimal(str(round(random.uniform(25, 65), 2))),
                
                # 流动性指标
                current_ratio=Decimal(str(round(random.uniform(1.0, 3.0), 2))),
                quick_ratio=Decimal(str(round(random.uniform(0.8, 2.5), 2))),
                cash_ratio=Decimal(str(round(random.uniform(0.3, 1.5), 2))),
                
                # 盈利能力指标
                gross_profit_margin=Decimal(str(round(random.uniform(15, 35), 2))),
                net_profit_margin=Decimal(str(round(random.uniform(5, 15), 2))),
                roe=Decimal(str(round(random.uniform(8, 20), 2))),
                roa=Decimal(str(round(random.uniform(3, 12), 2))),
                
                # 运营能力指标
                inventory_turnover=Decimal(str(round(random.uniform(2, 8), 2))),
                receivables_turnover=Decimal(str(round(random.uniform(4, 12), 2))),
                total_asset_turnover=Decimal(str(round(random.uniform(0.5, 2.0), 2))),
                
                # 发展能力指标
                revenue_growth_rate=Decimal(str(round(random.uniform(-5, 25), 2))),
                profit_growth_rate=Decimal(str(round(random.uniform(-10, 30), 2)))
            )
            
            db.session.add(financial_data)
    
    print(f"✅ 为 {len(enterprise_projects)} 个企业项目创建了财务分析数据")

def create_business_status_data():
    """创建经营状况数据"""
    print("创建经营状况数据...")
    
    # 获取所有企业项目
    enterprise_projects = Project.query.filter_by(type=ProjectType.ENTERPRISE).all()
    
    for project in enterprise_projects:
        # 随机生成经营状况数据
        business_status = BusinessStatus(
            project_id=project.id,
            evaluation_date=date.today() - timedelta(days=random.randint(1, 30)),
            
            # 经营资质状态
            business_license_status=random.choice(list(BusinessLicenseStatus)),
            business_license_expiry=date.today() + timedelta(days=random.randint(30, 1095)),
            tax_registration_status=random.choice(list(TaxRegistrationStatus)),
            organization_code_status=random.choice(list(BusinessLicenseStatus)),
            
            # 合规状态
            legal_violations=random.randint(0, 3),
            tax_compliance_status=random.choice(list(ComplianceStatus)),
            environmental_compliance=random.choice(list(ComplianceStatus)),
            labor_compliance=random.choice(list(ComplianceStatus)),
            
            # 经营风险
            market_risk_level=random.choice(list(RiskLevel)),
            financial_risk_level=random.choice(list(RiskLevel)),
            operational_risk_level=random.choice(list(RiskLevel)),
            
            # 行业地位
            industry_ranking=random.randint(1, 100),
            market_share=Decimal(str(round(random.uniform(0.1, 15.0), 2))),
            competitive_advantage="技术领先、品牌优势、成本控制能力强",
            
            # 经营状况评分
            overall_score=random.randint(60, 95),
            qualification_score=random.randint(70, 100),
            compliance_score=random.randint(65, 98),
            risk_score=random.randint(55, 90),
            
            # 备注信息
            risk_factors="市场竞争激烈，原材料价格波动",
            improvement_suggestions="加强技术创新，优化成本结构，拓展新市场"
        )
        
        db.session.add(business_status)
    
    print(f"✅ 为 {len(enterprise_projects)} 个企业项目创建了经营状况数据")

def create_timeline_data():
    """创建时间轴数据"""
    print("创建时间轴数据...")
    
    # 获取所有项目
    all_projects = Project.query.all()
    
    # 预定义的时间轴事件模板
    event_templates = [
        {"title": "项目启动", "type": EventType.MILESTONE, "status": EventStatus.COMPLETED, "days_ago": 30},
        {"title": "文档收集完成", "type": EventType.DOCUMENT, "status": EventStatus.COMPLETED, "days_ago": 25},
        {"title": "初步风险评估", "type": EventType.ANALYSIS, "status": EventStatus.COMPLETED, "days_ago": 20},
        {"title": "财务数据分析", "type": EventType.ANALYSIS, "status": EventStatus.COMPLETED, "days_ago": 15},
        {"title": "合规性审查", "type": EventType.REVIEW, "status": EventStatus.COMPLETED, "days_ago": 10},
        {"title": "综合评估报告", "type": EventType.REPORT, "status": EventStatus.IN_PROGRESS, "days_ago": 5},
        {"title": "最终报告提交", "type": EventType.REPORT, "status": EventStatus.PENDING, "days_ago": -3},
    ]
    
    for project in all_projects:
        # 为每个项目创建时间轴事件
        for i, template in enumerate(event_templates):
            event_date = date.today() - timedelta(days=template["days_ago"])
            
            timeline_event = ProjectTimeline(
                project_id=project.id,
                event_title=template["title"],
                event_description=f"项目 {project.name} 的{template['title']}阶段",
                event_type=template["type"],
                status=template["status"],
                priority=Priority.MEDIUM if i < 3 else Priority.HIGH,
                event_date=event_date,
                planned_date=event_date - timedelta(days=2),
                completed_date=event_date if template["status"] == EventStatus.COMPLETED else None,
                progress=100 if template["status"] == EventStatus.COMPLETED else (50 if template["status"] == EventStatus.IN_PROGRESS else 0),
                created_by=1  # 假设管理员用户ID为1
            )
            
            db.session.add(timeline_event)
    
    print(f"✅ 为 {len(all_projects)} 个项目创建了时间轴数据")

def main():
    """主函数"""
    print("项目详情数据种子脚本")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 检查是否已有数据
            existing_financial = FinancialAnalysis.query.count()
            existing_business = BusinessStatus.query.count()
            existing_timeline = ProjectTimeline.query.count()
            
            if existing_financial > 0 or existing_business > 0 or existing_timeline > 0:
                print(f"发现现有数据:")
                print(f"  财务分析记录: {existing_financial}")
                print(f"  经营状况记录: {existing_business}")
                print(f"  时间轴记录: {existing_timeline}")
                
                choice = input("是否清除现有数据并重新创建? (y/N): ").lower()
                if choice == 'y':
                    print("清除现有数据...")
                    ProjectTimeline.query.delete()
                    BusinessStatus.query.delete()
                    FinancialAnalysis.query.delete()
                    db.session.commit()
                    print("✅ 现有数据已清除")
                else:
                    print("保留现有数据，退出脚本")
                    return
            
            # 创建种子数据
            create_financial_analysis_data()
            create_business_status_data()
            create_timeline_data()
            
            # 提交事务
            db.session.commit()
            
            print("\n🎉 种子数据创建完成！")
            
            # 显示统计信息
            financial_count = FinancialAnalysis.query.count()
            business_count = BusinessStatus.query.count()
            timeline_count = ProjectTimeline.query.count()
            
            print(f"\n创建的数据统计:")
            print(f"  财务分析记录: {financial_count}")
            print(f"  经营状况记录: {business_count}")
            print(f"  时间轴记录: {timeline_count}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 创建种子数据失败: {e}")
            raise

if __name__ == '__main__':
    main()
