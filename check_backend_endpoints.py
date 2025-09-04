#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查后端API端点的脚本
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def check_endpoint(endpoint, method="GET", data=None):
    """检查单个端点"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔍 检查: {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            print(f"❌ 不支持的方法: {method}")
            return
        
        print(f"  状态码: {response.status_code}")
        print(f"  响应头: {dict(response.headers)}")
        
        try:
            result = response.json()
            print(f"  响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        except:
            print(f"  响应文本: {response.text[:200]}")
            
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")

def main():
    """主函数"""
    print("🔍 后端API端点检查")
    print(f"目标服务器: {BASE_URL}")
    
    # 基础连接检查
    print("\n=== 基础连接检查 ===")
    check_endpoint("/")
    check_endpoint("/health")
    check_endpoint("/api")
    
    # 登录端点检查
    print("\n=== 登录端点检查 ===")
    login_endpoints = [
        "/api/login",
        "/login", 
        "/auth/login",
        "/api/auth/login",
        "/api/v1/login"
    ]
    
    for endpoint in login_endpoints:
        check_endpoint(endpoint, "GET")
        check_endpoint(endpoint, "POST", {"username": "test", "password": "test"})
    
    # 报告相关端点检查
    print("\n=== 报告端点检查 ===")
    report_endpoints = [
        "/api/generate_report",
        "/api/generate_report_streaming",
        "/api/stop_report_generation",
        "/api/projects/5/report"
    ]
    
    for endpoint in report_endpoints:
        check_endpoint(endpoint, "GET")
    
    # 尝试列出所有路由（如果有的话）
    print("\n=== 路由发现 ===")
    discovery_endpoints = [
        "/routes",
        "/api/routes", 
        "/endpoints",
        "/api/endpoints",
        "/_routes",
        "/debug/routes"
    ]
    
    for endpoint in discovery_endpoints:
        check_endpoint(endpoint, "GET")
    
    print("\n🎯 检查完成!")
    print("\n💡 建议:")
    print("1. 检查后端服务是否正确启动")
    print("2. 检查后端路由配置")
    print("3. 查看后端日志确认问题")

if __name__ == "__main__":
    main()
