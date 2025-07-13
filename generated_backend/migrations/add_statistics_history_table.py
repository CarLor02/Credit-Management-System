#!/usr/bin/env python3
"""
创建统计历史表
用于保存每日/每月的统计快照，支持趋势分析
"""

import os
import sys
from datetime import datetime, date

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from config import Config
from database import init_db, db

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)
    return app

def create_statistics_history_table():
    """创建统计历史表"""
    sql = """
    CREATE TABLE IF NOT EXISTS statistics_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        
        -- 统计时间信息
        stat_date DATE NOT NULL,
        stat_type VARCHAR(20) NOT NULL DEFAULT 'daily',  -- daily, weekly, monthly
        
        -- 项目统计
        total_projects INTEGER DEFAULT 0,
        enterprise_projects INTEGER DEFAULT 0,
        individual_projects INTEGER DEFAULT 0,
        
        -- 项目状态统计
        collecting_projects INTEGER DEFAULT 0,
        processing_projects INTEGER DEFAULT 0,
        completed_projects INTEGER DEFAULT 0,
        archived_projects INTEGER DEFAULT 0,
        
        -- 风险统计
        high_risk_projects INTEGER DEFAULT 0,
        medium_risk_projects INTEGER DEFAULT 0,
        low_risk_projects INTEGER DEFAULT 0,
        
        -- 评分统计
        average_score DECIMAL(5,2) DEFAULT 0,
        min_score INTEGER DEFAULT 0,
        max_score INTEGER DEFAULT 0,
        
        -- 文档统计
        total_documents INTEGER DEFAULT 0,
        completed_documents INTEGER DEFAULT 0,
        processing_documents INTEGER DEFAULT 0,
        failed_documents INTEGER DEFAULT 0,
        
        -- 用户统计
        total_users INTEGER DEFAULT 0,
        active_users INTEGER DEFAULT 0,
        
        -- 业务指标
        completion_rate DECIMAL(5,2) DEFAULT 0,
        doc_completion_rate DECIMAL(5,2) DEFAULT 0,
        
        -- 新增统计（相比上一期）
        new_projects INTEGER DEFAULT 0,
        new_documents INTEGER DEFAULT 0,
        new_users INTEGER DEFAULT 0,
        
        -- 元数据
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        -- 唯一约束：每天每种类型只能有一条记录
        UNIQUE(stat_date, stat_type)
    );
    """
    
    db.session.execute(sql)
    print("✅ 统计历史表创建成功")

def create_indexes():
    """创建索引"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_statistics_history_date ON statistics_history(stat_date);",
        "CREATE INDEX IF NOT EXISTS idx_statistics_history_type ON statistics_history(stat_type);",
        "CREATE INDEX IF NOT EXISTS idx_statistics_history_date_type ON statistics_history(stat_date, stat_type);",
    ]
    
    for index_sql in indexes:
        db.session.execute(index_sql)
    
    print("✅ 统计历史表索引创建成功")

def run_migration():
    """运行迁移"""
    app = create_app()
    
    with app.app_context():
        print("开始创建统计历史表...")
        
        try:
            # 创建表
            create_statistics_history_table()
            
            # 创建索引
            create_indexes()
            
            # 提交事务
            db.session.commit()
            
            print("✅ 统计历史表和索引创建完成")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 迁移失败: {e}")
            raise

def main():
    """主函数"""
    print("统计历史表迁移脚本")
    print("=" * 50)
    
    try:
        run_migration()
        print("\n🎉 迁移成功完成！")
        print("\n创建的表:")
        print("- statistics_history (统计历史表)")
        print("\n下一步:")
        print("1. 运行 generate_historical_stats.py 生成历史数据")
        print("2. 设置定时任务每日更新统计数据")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
