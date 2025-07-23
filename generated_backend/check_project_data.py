#!/usr/bin/env python3
"""
检查项目数据库中的knowledge_base_name字段
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from db_models import Project
from database import db

def check_project_data():
    """检查项目数据"""
    app = create_app()
    
    with app.app_context():
        try:
            # 获取所有项目
            projects = Project.query.all()
            
            print(f"数据库中共有 {len(projects)} 个项目:")
            print("=" * 80)
            
            for project in projects:
                print(f"项目ID: {project.id}")
                print(f"项目名称: {project.name}")
                print(f"dataset_id: {project.dataset_id}")
                print(f"knowledge_base_name: {project.knowledge_base_name}")
                print(f"创建时间: {project.created_at}")
                print(f"更新时间: {project.updated_at}")
                print("-" * 40)
            
            # 统计有knowledge_base_name的项目
            projects_with_kb = [p for p in projects if p.knowledge_base_name]
            projects_with_dataset = [p for p in projects if p.dataset_id]
            
            print(f"\n统计信息:")
            print(f"总项目数: {len(projects)}")
            print(f"有knowledge_base_name的项目: {len(projects_with_kb)}")
            print(f"有dataset_id的项目: {len(projects_with_dataset)}")
            
            if not projects_with_kb:
                print("\n⚠️ 没有项目设置了knowledge_base_name字段")
                print("这可能是因为:")
                print("1. 项目还没有上传过文档")
                print("2. 知识库创建功能还没有被触发")
                print("3. 需要手动设置一些测试数据")
                
                # 为第一个项目设置测试数据
                if projects:
                    import uuid
                    first_project = projects[0]
                    print(f"\n为项目 '{first_project.name}' 设置测试数据...")

                    kb_uuid = str(uuid.uuid4())
                    first_project.dataset_id = f"test-dataset-{first_project.id}"
                    first_project.knowledge_base_name = f"admin_{first_project.name}_{kb_uuid}"
                    
                    db.session.commit()
                    print("✅ 测试数据设置完成")
                    
                    print(f"更新后的数据:")
                    print(f"- dataset_id: {first_project.dataset_id}")
                    print(f"- knowledge_base_name: {first_project.knowledge_base_name}")
            
        except Exception as e:
            print(f"❌ 检查数据失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    check_project_data()
