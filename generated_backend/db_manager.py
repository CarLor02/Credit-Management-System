#!/usr/bin/env python3
"""
数据库管理工具
提供数据库初始化、连接测试、表管理等功能
"""

import os
import sys
import argparse
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_connection():
    """测试数据库连接"""
    try:
        from app import app
        with app.app_context():
            from db_config import db_manager
            if db_manager.test_connection():
                print("✓ 数据库连接测试成功")
                return True
            else:
                print("✗ 数据库连接测试失败")
                return False
    except Exception as e:
        print(f"✗ 数据库连接测试失败: {e}")
        return False

def init_database():
    """初始化数据库"""
    try:
        from app import app
        with app.app_context():
            from database import create_tables
            from seed_data import create_seed_data
            
            # 创建表
            print("正在创建数据库表...")
            create_tables(app)
            
            # 创建种子数据
            print("正在创建种子数据...")
            create_seed_data()
            
        print("✓ 数据库初始化完成")
        return True
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        return False

def show_tables():
    """显示数据库表信息"""
    try:
        from app import app
        with app.app_context():
            from database import db
            
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if not tables:
                print("数据库中没有表")
                return
            
            print(f"数据库中共有 {len(tables)} 个表:")
            for table in sorted(tables):
                try:
                    # 获取表的记录数
                    result = db.session.execute(db.text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"  - {table}: {count} 条记录")
                except Exception as e:
                    print(f"  - {table}: 无法获取记录数 ({e})")
            
    except Exception as e:
        print(f"✗ 获取表信息失败: {e}")

def show_config():
    """显示当前数据库配置"""
    try:
        from app import app
        with app.app_context():
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            
            # 隐藏密码
            import re
            masked_uri = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', db_uri)
            
            print("当前数据库配置:")
            print(f"  数据库URI: {masked_uri}")
            print(f"  数据库类型: MySQL")
            print(f"  调试模式: {app.config.get('SQLALCHEMY_ECHO', False)}")
            
            # 显示环境变量
            env_vars = [
                'MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_USER', 
                'MYSQL_DATABASE', 'DATABASE_URL'
            ]
            
            print("\n环境变量:")
            for var in env_vars:
                value = os.environ.get(var, '未设置')
                if 'PASSWORD' in var and value != '未设置':
                    value = '***'
                print(f"  {var}: {value}")
                
    except Exception as e:
        print(f"✗ 获取配置信息失败: {e}")

def backup_database():
    """备份数据库"""
    try:
        from migrate_database import backup_mysql_data
        
        backup_file = backup_mysql_data()
        
        if backup_file:
            print(f"✓ 数据库备份完成: {backup_file}")
            return True
        else:
            print("✗ 数据库备份失败")
            return False
            
    except Exception as e:
        print(f"✗ 数据库备份失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='征信管理系统数据库管理工具')
    parser.add_argument('command', choices=[
        'test', 'init', 'tables', 'config', 'backup'
    ], help='要执行的命令')
    
    args = parser.parse_args()
    
    print("=== 征信管理系统数据库管理工具 ===\n")
    
    if args.command == 'test':
        test_connection()
    elif args.command == 'init':
        print("注意: 此操作将创建数据库表和种子数据")
        confirm = input("是否继续? (y/N): ").strip().lower()
        if confirm == 'y':
            init_database()
        else:
            print("操作已取消")
    elif args.command == 'tables':
        show_tables()
    elif args.command == 'config':
        show_config()
    elif args.command == 'backup':
        backup_database()

if __name__ == '__main__':
    main()
