#!/usr/bin/env python3
"""
数据库初始化脚本
用于新用户快速初始化数据库
"""

import os
import sys
import subprocess

def main():
    """主函数"""
    print("=" * 50)
    print("征信管理系统 - 数据库初始化脚本")
    print("=" * 50)
    
    # 检查Python环境
    if sys.version_info < (3, 7):
        print("❌ 错误: 需要Python 3.7或更高版本")
        sys.exit(1)
    
    print(f"✅ Python版本: {sys.version}")
    
    # 切换到后端目录
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated_backend')
    if not os.path.exists(backend_dir):
        print(f"❌ 错误: 后端目录不存在: {backend_dir}")
        sys.exit(1)
    
    os.chdir(backend_dir)
    print(f"📁 切换到后端目录: {backend_dir}")
    
    # 检查requirements.txt
    requirements_file = os.path.join(backend_dir, 'requirements.txt')
    if not os.path.exists(requirements_file):
        print("❌ 错误: 找不到requirements.txt文件")
        sys.exit(1)
    
    # 安装依赖
    print("📦 正在安装Python依赖...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True, text=True)
        print("✅ 依赖安装成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        print("请手动运行: pip install -r requirements.txt")
        sys.exit(1)
    
    # 运行数据库初始化
    print("🗄️  正在初始化数据库...")
    try:
        subprocess.run([sys.executable, 'init_db.py'], check=True)
        print("✅ 数据库初始化成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 数据库初始化完成!")
    print("=" * 50)
    print("现在可以运行以下命令启动系统:")
    print("  ./start.sh")
    print("或者分别启动前端和后端:")
    print("  后端: cd generated_backend && python3 app.py")
    print("  前端: cd frontend && npm run dev")
    print("=" * 50)

if __name__ == '__main__':
    main()
