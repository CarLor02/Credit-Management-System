#!/usr/bin/env python3
"""
数据库迁移脚本：添加文档处理相关字段
"""

import os
import sys
from flask import Flask

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from config import Config
from database import db
from db_models import Document, DocumentStatus

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化数据库
    db.init_app(app)
    
    return app

def add_document_processing_fields():
    """添加文档处理相关字段"""
    app = create_app()
    
    with app.app_context():
        try:
            print("正在添加文档处理相关字段...")
            
            # 添加新字段的SQL
            db.session.execute(db.text("""
                ALTER TABLE documents ADD COLUMN processed_file_path VARCHAR(500);
            """))
            
            db.session.execute(db.text("""
                ALTER TABLE documents ADD COLUMN processed_at DATETIME;
            """))
            
            db.session.execute(db.text("""
                ALTER TABLE documents ADD COLUMN processing_started_at DATETIME;
            """))
            
            db.session.commit()
            print("文档处理字段添加成功!")
            
        except Exception as e:
            print(f"添加字段失败: {e}")
            db.session.rollback()
            
            # 检查字段是否已存在
            try:
                # 尝试查询字段，如果不报错说明字段已存在
                db.session.execute(db.text("SELECT processed_file_path FROM documents LIMIT 1"))
                print("字段已存在，无需重复添加")
            except:
                print("字段添加确实失败了")
                return False
        
        return True

def update_document_status_enum():
    """更新文档状态枚举值"""
    app = create_app()
    
    with app.app_context():
        try:
            print("正在更新文档状态...")
            
            # 将状态为 'completed' 的文档更新为 'uploaded'，因为这些文档实际上只是上传完成
            # 需要重新处理
            result = db.session.execute(db.text("""
                UPDATE documents 
                SET status = 'uploaded' 
                WHERE status = 'completed' AND processed_file_path IS NULL
            """))
            
            print(f"更新了 {result.rowcount} 个文档的状态")
            
            db.session.commit()
            print("文档状态更新成功!")
            
        except Exception as e:
            print(f"更新状态失败: {e}")
            db.session.rollback()
            return False
        
        return True

def main():
    """主函数"""
    print("=" * 50)
    print("文档处理功能数据库迁移")
    print("=" * 50)
    
    # 添加字段
    if add_document_processing_fields():
        print("✓ 字段添加成功")
    else:
        print("✗ 字段添加失败")
        return
    
    # 更新状态
    if update_document_status_enum():
        print("✓ 状态更新成功")
    else:
        print("✗ 状态更新失败")
        return
    
    print("=" * 50)
    print("数据库迁移完成！")
    print("=" * 50)

if __name__ == '__main__':
    main()
