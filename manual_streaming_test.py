#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动输入登录信息的流式API测试脚本
"""

import requests
import json
import getpass
from datetime import datetime

# 配置
BASE_URL = "http://localhost:5001"
PROJECT_ID = 5
COMPANY_NAME = "西安市新希望医疗器械有限公司"
KNOWLEDGE_NAME = "user1_西安市新希望医疗器械有限公司_3ce0d547-c9ed-4c73-85a5-9a11f068ced8"

def check_available_endpoints():
    """检查可用的API端点"""
    print("🔍 检查可用的API端点...")

    # 常见的登录端点
    login_endpoints = [
        "/api/login",
        "/login",
        "/auth/login",
        "/api/auth/login",
        "/api/v1/login"
    ]

    for endpoint in login_endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            print(f"  检查: {url}")

            # 先用GET检查端点是否存在
            response = requests.get(url, timeout=5)
            print(f"    GET {response.status_code}: {response.text[:100]}")

            # 如果GET返回405 (Method Not Allowed)，说明端点存在但不支持GET
            if response.status_code == 405:
                print(f"    ✅ 端点存在，尝试POST...")
                return endpoint
            elif response.status_code == 200:
                print(f"    ✅ 端点可用")
                return endpoint

        except Exception as e:
            print(f"    ❌ 连接失败: {e}")

    print("❌ 未找到可用的登录端点")
    return None

def manual_login():
    """手动输入登录信息"""
    print("🔐 请输入登录信息")

    # 先检查可用的登录端点
    login_endpoint = check_available_endpoints()
    if not login_endpoint:
        print("❌ 无法找到登录端点")
        return None

    print(f"✅ 使用登录端点: {login_endpoint}")

    # 提供一些常见的默认选项
    print("\n常见用户名选项:")
    print("1. admin")
    print("2. root")
    print("3. test")
    print("4. 手动输入")

    choice = input("请选择 (1-4): ").strip()

    if choice == "1":
        username = "admin"
    elif choice == "2":
        username = "root"
    elif choice == "3":
        username = "test"
    else:
        username = input("请输入用户名: ").strip()

    # 密码输入
    print(f"\n用户名: {username}")
    print("常见密码选项:")
    print("1. admin123")
    print("2. 123456")
    print("3. admin")
    print("4. root")
    print("5. test")
    print("6. 手动输入")

    pwd_choice = input("请选择密码 (1-6): ").strip()

    if pwd_choice == "1":
        password = "admin123"
    elif pwd_choice == "2":
        password = "123456"
    elif pwd_choice == "3":
        password = "admin"
    elif pwd_choice == "4":
        password = "root"
    elif pwd_choice == "5":
        password = "test"
    else:
        password = getpass.getpass("请输入密码: ")

    print(f"\n🔄 尝试登录: {username}")

    try:
        response = requests.post(f"{BASE_URL}{login_endpoint}", json={
            "username": username,
            "password": password
        }, timeout=10)

        print(f"响应状态: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"响应内容: {result}")

            if result.get('success'):
                token = result.get('token')
                if token:
                    print(f"✅ 登录成功!")
                    return token
                else:
                    print("❌ 响应中没有token")
            else:
                print(f"❌ 登录失败: {result.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP错误 {response.status_code}: {response.text}")

    except Exception as e:
        print(f"❌ 请求异常: {e}")

    return None

def test_streaming_with_token(token):
    """使用token测试流式API"""
    print(f"\n📡 测试流式API")
    print(f"公司: {COMPANY_NAME}")
    print(f"知识库: {KNOWLEDGE_NAME}")
    print(f"项目ID: {PROJECT_ID}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "company_name": COMPANY_NAME,
        "project_id": PROJECT_ID,
        "knowledge_name": KNOWLEDGE_NAME
    }
    
    try:
        print(f"\n🚀 发送请求到: {BASE_URL}/api/generate_report_streaming")
        response = requests.post(
            f"{BASE_URL}/api/generate_report_streaming",
            headers=headers,
            json=data,
            stream=True,
            timeout=120
        )
        
        print(f"响应状态: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"❌ API调用失败: {response.text}")
            return
        
        print("✅ 开始接收流式数据...\n")
        
        # 处理流式响应
        content_chunks = []
        final_content = ""
        chunk_count = 0
        
        # 创建输出文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"streaming_output_{timestamp}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"流式API测试结果\n")
            f.write(f"时间: {datetime.now()}\n")
            f.write(f"公司: {COMPANY_NAME}\n")
            f.write(f"知识库: {KNOWLEDGE_NAME}\n")
            f.write("="*80 + "\n\n")
            
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    f.write(f"原始行: {line}\n")
                    
                    if line.startswith('data: '):
                        data_str = line[6:]
                        
                        if data_str.strip() == '[DONE]':
                            print("✅ 流式响应完成")
                            f.write("流式响应完成\n")
                            break
                        
                        try:
                            data = json.loads(data_str)
                            content = data.get('content') or data.get('answer') or data.get('message')
                            
                            if content:
                                chunk_count += 1
                                content_chunks.append(content)
                                final_content += content
                                
                                # 控制台输出
                                print(f"📦 块 {chunk_count}: 长度={len(content)}")
                                
                                # 显示内容的repr形式，便于查看格式
                                content_repr = repr(content)
                                if len(content_repr) > 100:
                                    content_repr = content_repr[:100] + "..."
                                print(f"   内容: {content_repr}")
                                
                                # 格式检查
                                has_newline = '\n' in content
                                has_space = ' ' in content
                                has_pipe = '|' in content
                                has_hash = '#' in content
                                
                                print(f"   格式: 换行={has_newline}, 空格={has_space}, 表格={has_pipe}, 标题={has_hash}")
                                
                                # 文件输出
                                f.write(f"\n--- 块 {chunk_count} ---\n")
                                f.write(f"长度: {len(content)}\n")
                                f.write(f"repr: {repr(content)}\n")
                                f.write(f"原始内容:\n{content}\n")
                                f.write(f"格式检查: 换行={has_newline}, 空格={has_space}, 表格={has_pipe}, 标题={has_hash}\n")
                                
                                print()
                                
                        except json.JSONDecodeError as e:
                            print(f"⚠️ JSON解析失败: {e}")
                            f.write(f"JSON解析失败: {e}\n")
        
        # 最终分析
        print(f"\n📊 最终统计:")
        print(f"总块数: {chunk_count}")
        print(f"最终内容长度: {len(final_content)}")
        print(f"换行符数量: {final_content.count(chr(10))}")
        print(f"空格数量: {final_content.count(' ')}")
        print(f"制表符数量: {final_content.count(chr(9))}")
        
        # 保存最终内容
        final_file = f"final_content_{timestamp}.md"
        with open(final_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        print(f"\n📁 文件已保存:")
        print(f"  详细日志: {output_file}")
        print(f"  最终内容: {final_file}")
        
        # 快速问题检查
        print(f"\n🔍 快速问题检查:")
        lines = final_content.split('\n')
        
        # 检查表格问题
        table_lines = [(i, line) for i, line in enumerate(lines) if '|' in line.strip()]
        if table_lines:
            print(f"发现 {len(table_lines)} 行表格")
            
            # 检查表格行之间的空行
            for i in range(len(table_lines) - 1):
                current_idx = table_lines[i][0]
                next_idx = table_lines[i + 1][0]
                if next_idx - current_idx > 1:
                    between_lines = lines[current_idx + 1:next_idx]
                    empty_count = sum(1 for line in between_lines if line.strip() == '')
                    if empty_count > 0:
                        print(f"⚠️ 表格行 {current_idx+1} 和 {next_idx+1} 之间有 {empty_count} 个空行")
        
        # 检查标题问题
        title_lines = [(i, line) for i, line in enumerate(lines) if line.strip().startswith('#')]
        if title_lines:
            print(f"发现 {len(title_lines)} 行标题")
            
            # 检查标题和表格在同一行
            for i, line in title_lines:
                if '|' in line:
                    print(f"⚠️ 第 {i+1} 行标题和表格在同一行: {repr(line)}")
        
        print(f"\n🎯 测试完成!")
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")

def main():
    """主函数"""
    print("🧪 手动流式API测试")
    print(f"目标服务器: {BASE_URL}")
    
    # 检查服务器连接
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ 服务器连接正常")
    except:
        print(f"⚠️ 无法连接到服务器，但继续尝试...")
    
    # 登录
    token = manual_login()
    if not token:
        print("❌ 登录失败，测试终止")
        return
    
    # 测试流式API
    test_streaming_with_token(token)

if __name__ == "__main__":
    main()
