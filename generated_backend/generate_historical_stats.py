#!/usr/bin/env python3
"""
生成历史统计数据
为趋势分析创建模拟的历史数据
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
    Project, Document, User, StatisticsHistory, StatType,
    ProjectType, ProjectStatus, RiskLevel
)

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)
    return app

def calculate_current_stats():
    """计算当前真实统计数据"""
    stats = {}
    
    # 项目统计
    stats['total_projects'] = Project.query.count()
    stats['enterprise_projects'] = Project.query.filter_by(type=ProjectType.ENTERPRISE).count()
    stats['individual_projects'] = Project.query.filter_by(type=ProjectType.INDIVIDUAL).count()
    
    # 项目状态统计
    stats['collecting_projects'] = Project.query.filter_by(status=ProjectStatus.COLLECTING).count()
    stats['processing_projects'] = Project.query.filter_by(status=ProjectStatus.PROCESSING).count()
    stats['completed_projects'] = Project.query.filter_by(status=ProjectStatus.COMPLETED).count()
    stats['archived_projects'] = Project.query.filter_by(status=ProjectStatus.ARCHIVED).count()
    
    # 风险统计
    stats['high_risk_projects'] = Project.query.filter_by(risk_level=RiskLevel.HIGH).count()
    stats['medium_risk_projects'] = Project.query.filter_by(risk_level=RiskLevel.MEDIUM).count()
    stats['low_risk_projects'] = Project.query.filter_by(risk_level=RiskLevel.LOW).count()
    
    # 评分统计
    projects = Project.query.all()
    if projects:
        scores = [p.score for p in projects]
        stats['average_score'] = sum(scores) / len(scores)
        stats['min_score'] = min(scores)
        stats['max_score'] = max(scores)
    else:
        stats['average_score'] = 0
        stats['min_score'] = 0
        stats['max_score'] = 0
    
    # 文档统计
    stats['total_documents'] = Document.query.count()
    stats['completed_documents'] = Document.query.filter_by(status='completed').count()
    stats['processing_documents'] = Document.query.filter_by(status='processing').count()
    stats['failed_documents'] = Document.query.filter_by(status='failed').count()
    
    # 用户统计
    stats['total_users'] = User.query.count()
    # 假设最近30天内有活动的用户为活跃用户
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    stats['active_users'] = User.query.filter(User.last_login >= thirty_days_ago).count()
    
    # 业务指标
    stats['completion_rate'] = (stats['completed_projects'] / stats['total_projects'] * 100) if stats['total_projects'] > 0 else 0
    stats['doc_completion_rate'] = (stats['completed_documents'] / stats['total_documents'] * 100) if stats['total_documents'] > 0 else 0
    
    return stats

def generate_historical_data(months=6):
    """生成历史统计数据"""
    print(f"生成最近 {months} 个月的历史统计数据...")
    
    # 获取当前真实统计数据作为基准
    current_stats = calculate_current_stats()
    
    # 生成历史数据
    end_date = date.today()
    start_date = end_date - timedelta(days=30 * months)
    
    current_date = start_date
    created_count = 0
    
    while current_date <= end_date:
        # 检查是否已存在该日期的统计记录
        existing = StatisticsHistory.query.filter_by(
            stat_date=current_date,
            stat_type=StatType.DAILY
        ).first()
        
        if existing:
            print(f"跳过已存在的统计记录: {current_date}")
            current_date += timedelta(days=1)
            continue
        
        # 计算该日期的模拟数据（基于当前数据加上随机变化）
        days_from_now = (end_date - current_date).days
        
        # 项目数量随时间递减（越早项目越少）
        project_factor = max(0.3, 1 - days_from_now * 0.01)
        
        # 生成该日期的统计数据
        daily_stats = StatisticsHistory(
            stat_date=current_date,
            stat_type=StatType.DAILY,
            
            # 项目统计（随时间变化）
            total_projects=max(1, int(current_stats['total_projects'] * project_factor)),
            enterprise_projects=max(0, int(current_stats['enterprise_projects'] * project_factor)),
            individual_projects=max(0, int(current_stats['individual_projects'] * project_factor)),
            
            # 项目状态统计
            collecting_projects=max(0, int(current_stats['collecting_projects'] * project_factor * random.uniform(0.8, 1.2))),
            processing_projects=max(0, int(current_stats['processing_projects'] * project_factor * random.uniform(0.8, 1.2))),
            completed_projects=max(0, int(current_stats['completed_projects'] * project_factor * random.uniform(0.9, 1.1))),
            archived_projects=max(0, int(current_stats['archived_projects'] * project_factor * random.uniform(0.9, 1.1))),
            
            # 风险统计（添加随机波动）
            high_risk_projects=max(0, int(current_stats['high_risk_projects'] * project_factor * random.uniform(0.5, 1.5))),
            medium_risk_projects=max(0, int(current_stats['medium_risk_projects'] * project_factor * random.uniform(0.8, 1.2))),
            low_risk_projects=max(0, int(current_stats['low_risk_projects'] * project_factor * random.uniform(0.9, 1.1))),
            
            # 评分统计（添加小幅波动）
            average_score=Decimal(str(round(current_stats['average_score'] + random.uniform(-5, 5), 1))),
            min_score=max(0, current_stats['min_score'] + random.randint(-10, 5)),
            max_score=min(100, current_stats['max_score'] + random.randint(-5, 5)),
            
            # 文档统计
            total_documents=max(0, int(current_stats['total_documents'] * project_factor * random.uniform(0.8, 1.2))),
            completed_documents=max(0, int(current_stats['completed_documents'] * project_factor * random.uniform(0.8, 1.2))),
            processing_documents=max(0, int(current_stats['processing_documents'] * project_factor * random.uniform(0.5, 1.5))),
            failed_documents=max(0, int(current_stats['failed_documents'] * project_factor * random.uniform(0.3, 1.0))),
            
            # 用户统计
            total_users=max(1, int(current_stats['total_users'] * random.uniform(0.9, 1.0))),
            active_users=max(1, int(current_stats['active_users'] * random.uniform(0.7, 1.0))),
            
            # 业务指标
            completion_rate=Decimal(str(round(current_stats['completion_rate'] + random.uniform(-10, 10), 1))),
            doc_completion_rate=Decimal(str(round(current_stats['doc_completion_rate'] + random.uniform(-15, 15), 1))),
            
            # 新增统计（模拟每日新增）
            new_projects=random.randint(0, 3),
            new_documents=random.randint(0, 8),
            new_users=random.randint(0, 2)
        )
        
        db.session.add(daily_stats)
        created_count += 1
        
        # 每10条记录提交一次
        if created_count % 10 == 0:
            db.session.commit()
            print(f"已创建 {created_count} 条统计记录...")
        
        current_date += timedelta(days=1)
    
    # 最终提交
    db.session.commit()
    print(f"✅ 成功创建 {created_count} 条历史统计记录")
    
    return created_count

def generate_monthly_stats():
    """生成月度统计汇总"""
    print("生成月度统计汇总...")
    
    # 获取所有日统计数据，按月分组
    daily_stats = StatisticsHistory.query.filter_by(stat_type=StatType.DAILY).all()
    
    # 按月分组
    monthly_data = {}
    for stat in daily_stats:
        month_key = stat.stat_date.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = []
        monthly_data[month_key].append(stat)
    
    created_count = 0
    
    for month_key, month_stats in monthly_data.items():
        if not month_stats:
            continue
        
        # 计算月度汇总
        month_date = datetime.strptime(month_key + '-01', '%Y-%m-%d').date()
        
        # 检查是否已存在
        existing = StatisticsHistory.query.filter_by(
            stat_date=month_date,
            stat_type=StatType.MONTHLY
        ).first()
        
        if existing:
            continue
        
        # 计算月度平均值和总计
        total_days = len(month_stats)
        
        monthly_summary = StatisticsHistory(
            stat_date=month_date,
            stat_type=StatType.MONTHLY,
            
            # 使用月末数据作为月度数据
            total_projects=month_stats[-1].total_projects,
            enterprise_projects=month_stats[-1].enterprise_projects,
            individual_projects=month_stats[-1].individual_projects,
            
            # 状态统计使用平均值
            collecting_projects=int(sum(s.collecting_projects for s in month_stats) / total_days),
            processing_projects=int(sum(s.processing_projects for s in month_stats) / total_days),
            completed_projects=int(sum(s.completed_projects for s in month_stats) / total_days),
            archived_projects=int(sum(s.archived_projects for s in month_stats) / total_days),
            
            # 风险统计使用平均值
            high_risk_projects=int(sum(s.high_risk_projects for s in month_stats) / total_days),
            medium_risk_projects=int(sum(s.medium_risk_projects for s in month_stats) / total_days),
            low_risk_projects=int(sum(s.low_risk_projects for s in month_stats) / total_days),
            
            # 评分使用平均值
            average_score=Decimal(str(round(sum(float(s.average_score) for s in month_stats) / total_days, 1))),
            min_score=min(s.min_score for s in month_stats),
            max_score=max(s.max_score for s in month_stats),
            
            # 文档统计使用月末数据
            total_documents=month_stats[-1].total_documents,
            completed_documents=month_stats[-1].completed_documents,
            processing_documents=month_stats[-1].processing_documents,
            failed_documents=month_stats[-1].failed_documents,
            
            # 用户统计使用月末数据
            total_users=month_stats[-1].total_users,
            active_users=month_stats[-1].active_users,
            
            # 业务指标使用平均值
            completion_rate=Decimal(str(round(sum(float(s.completion_rate) for s in month_stats) / total_days, 1))),
            doc_completion_rate=Decimal(str(round(sum(float(s.doc_completion_rate) for s in month_stats) / total_days, 1))),
            
            # 新增统计使用总和
            new_projects=sum(s.new_projects for s in month_stats),
            new_documents=sum(s.new_documents for s in month_stats),
            new_users=sum(s.new_users for s in month_stats)
        )
        
        db.session.add(monthly_summary)
        created_count += 1
    
    db.session.commit()
    print(f"✅ 成功创建 {created_count} 条月度统计记录")
    
    return created_count

def main():
    """主函数"""
    print("历史统计数据生成脚本")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. 生成日统计数据
            daily_count = generate_historical_data(months=6)
            
            # 2. 生成月度统计汇总
            monthly_count = generate_monthly_stats()
            
            print(f"\n🎉 历史统计数据生成完成！")
            print(f"  日统计记录: {daily_count} 条")
            print(f"  月统计记录: {monthly_count} 条")
            
            # 3. 显示统计信息
            total_records = StatisticsHistory.query.count()
            daily_records = StatisticsHistory.query.filter_by(stat_type=StatType.DAILY).count()
            monthly_records = StatisticsHistory.query.filter_by(stat_type=StatType.MONTHLY).count()
            
            print(f"\n📊 数据库统计记录总览:")
            print(f"  总记录数: {total_records}")
            print(f"  日统计: {daily_records} 条")
            print(f"  月统计: {monthly_records} 条")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 生成历史数据失败: {e}")
            raise

if __name__ == '__main__':
    main()
