#!/usr/bin/env python3
"""
数据库初始化脚本
"""

import os
import sys
from flask import Flask

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database import init_db, create_tables, drop_tables, reset_database
from seed_data import create_seed_data

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化数据库
    init_db(app)
    
    return app

def init_database():
    """初始化数据库"""
    app = create_app()
    
    with app.app_context():
        print("正在初始化数据库...")
        
        # 创建数据库表
        create_tables(app)
        
        # 创建种子数据
        create_seed_data()
        
        print("数据库初始化完成!")

def reset_db():
    """重置数据库"""
    app = create_app()
    
    with app.app_context():
        print("正在重置数据库...")
        
        # 重置数据库
        reset_database(app)
        
        # 创建种子数据
        create_seed_data()
        
        print("数据库重置完成!")

def drop_db():
    """删除数据库"""
    app = create_app()
    
    with app.app_context():
        print("正在删除数据库...")
        drop_tables(app)
        print("数据库删除完成!")

def show_help():
    """显示帮助信息"""
    print("数据库管理工具")
    print("")
    print("用法:")
    print("  python init_db.py [命令]")
    print("")
    print("命令:")
    print("  init     初始化数据库（默认）")
    print("  reset    重置数据库")
    print("  drop     删除数据库")
    print("  seed     只创建种子数据")
    print("  help     显示帮助信息")
    print("")
    print("示例:")
    print("  python init_db.py init    # 初始化数据库")
    print("  python init_db.py reset   # 重置数据库")
    print("  python init_db.py drop    # 删除数据库")

def create_seed_only():
    """只创建种子数据"""
    app = create_app()
    
    with app.app_context():
        print("正在创建种子数据...")
        create_seed_data()
        print("种子数据创建完成!")

if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) > 1 else 'init'
    
    if command == 'init':
        init_database()
    elif command == 'reset':
        reset_db()
    elif command == 'drop':
        drop_db()
    elif command == 'seed':
        create_seed_only()
    elif command == 'help' or command == '--help' or command == '-h':
        show_help()
    else:
        print(f"未知命令: {command}")
        print("使用 'help' 查看可用命令")
        sys.exit(1)
