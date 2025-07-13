"""
数据库迁移脚本 - 为项目添加文件夹UUID字段
"""

import uuid
import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from database import db
from db_models import Project
from sqlalchemy import text

def migrate_add_project_folder_uuid():
    """为项目表添加folder_uuid字段并为现有项目生成UUID"""
    
    try:
        # 检查列是否已存在
        result = db.session.execute(text("PRAGMA table_info(projects);"))
        columns = [row[1] for row in result]
        
        if 'folder_uuid' not in columns:
            print("添加folder_uuid列到projects表...")
            # 添加列
            db.session.execute(text("ALTER TABLE projects ADD COLUMN folder_uuid VARCHAR(36);"))
            db.session.commit()
            print("✓ folder_uuid列添加成功")
        else:
            print("folder_uuid列已存在")
        
        # 为现有项目生成UUID
        projects_without_uuid = Project.query.filter(
            (Project.folder_uuid == None) | (Project.folder_uuid == '')
        ).all()
        
        if projects_without_uuid:
            print(f"为 {len(projects_without_uuid)} 个项目生成folder_uuid...")
            
            for project in projects_without_uuid:
                project.folder_uuid = str(uuid.uuid4())
                print(f"  项目 '{project.name}' -> {project.folder_uuid}")
            
            db.session.commit()
            print("✓ 所有项目的folder_uuid生成完成")
        else:
            print("所有项目都已有folder_uuid")
            
        # 创建唯一索引（如果不存在）
        try:
            db.session.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_folder_uuid ON projects(folder_uuid);"))
            db.session.commit()
            print("✓ 唯一索引创建成功")
        except Exception as e:
            print(f"索引创建失败（可能已存在）: {e}")
        
        print("✅ 迁移完成！")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 迁移失败: {e}")
        raise

if __name__ == '__main__':
    from app import app
    
    with app.app_context():
        migrate_add_project_folder_uuid()
