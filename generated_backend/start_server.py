#!/usr/bin/env python3
"""
启动后端服务器
"""

import os
import sys
import subprocess
import time
import requests

def check_server_running(port=5001):
    """检查服务器是否正在运行"""
    try:
        response = requests.get(f"http://localhost:{port}/api/projects", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_server():
    """启动服务器"""
    print("检查服务器状态...")
    
    if check_server_running():
        print("✅ 服务器已经在运行")
        return True
    
    print("启动后端服务器...")
    try:
        # 启动服务器
        process = subprocess.Popen([
            sys.executable, "app.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服务器启动
        for i in range(10):
            time.sleep(1)
            if check_server_running():
                print("✅ 服务器启动成功")
                return True
            print(f"等待服务器启动... ({i+1}/10)")
        
        print("❌ 服务器启动超时")
        return False
        
    except Exception as e:
        print(f"❌ 启动服务器失败: {e}")
        return False

if __name__ == "__main__":
    if start_server():
        print("\n服务器信息:")
        print("- 地址: http://localhost:5001")
        print("- API文档: http://localhost:5001/api/projects")
        print("- 生成报告API: http://localhost:5001/api/generate_report")
    else:
        print("\n请手动启动服务器:")
        print("cd generated_backend")
        print("python app.py")
