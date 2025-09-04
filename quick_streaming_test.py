#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速流式API测试脚本
专门检查格式问题
"""

import requests
import json
import time
from datetime import datetime

# 配置
BASE_URL = "http://localhost:5001"
PROJECT_ID = 5
COMPANY_NAME = "西安市新希望医疗器械有限公司"
KNOWLEDGE_NAME = "user1_西安市新希望医疗器械有限公司_3ce0d547-c9ed-4c73-85a5-9a11f068ced8"

# 登录配置 - 请根据实际情况修改
LOGIN_CONFIGS = [
    {"username": "admin", "password": "admin123"},
    {"username": "admin", "password": "123456"},
    {"username": "root", "password": "root"},
    {"username": "test", "password": "test"},
    # 添加更多可能的登录组合
]

def try_login():
    """尝试多种登录配置"""
    print("� 尝试登录...")

    for i, config in enumerate(LOGIN_CONFIGS):
        print(f"  尝试配置 {i+1}: {config['username']}")

        try:
            response = requests.post(f"{BASE_URL}/api/login", json=config, timeout=10)
            print(f"    响应状态: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"    响应内容: {result}")

                if result.get('success'):
                    token = result.get('token')
                    if token:
                        print(f"✅ 登录成功! 用户: {config['username']}")
                        return token
                    else:
                        print("    ❌ 响应中没有token")
                else:
                    print(f"    ❌ 登录失败: {result.get('error', '未知错误')}")
            else:
                print(f"    ❌ HTTP错误: {response.text}")

        except Exception as e:
            print(f"    ❌ 请求异常: {e}")

    print("❌ 所有登录配置都失败了")
    print("💡 请检查:")
    print("  1. 后端服务是否在 http://localhost:5001 运行")
    print("  2. 用户名密码是否正确")
    print("  3. 网络连接是否正常")
    return None

def quick_test():
    """快速测试"""
    print("🚀 快速流式API测试")
    print(f"🎯 目标服务器: {BASE_URL}")

    # 1. 登录
    token = try_login()
    if not token:
        return
    
    # 2. 调用流式API
    print("\n2. 调用流式API...")
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
        response = requests.post(
            f"{BASE_URL}/api/generate_report_streaming",
            headers=headers,
            json=data,
            stream=True,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ API调用失败: {response.text}")
            return
        
        print("✅ 开始接收流式数据...")
        
        # 3. 处理响应
        content_chunks = []
        final_content = ""
        chunk_count = 0
        
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                data_str = line[6:]
                
                if data_str.strip() == '[DONE]':
                    break
                
                try:
                    data = json.loads(data_str)
                    content = data.get('content') or data.get('answer') or data.get('message')
                    
                    if content:
                        chunk_count += 1
                        content_chunks.append(content)
                        final_content += content
                        
                        # 实时分析
                        print(f"块 {chunk_count}: 长度={len(content)}")
                        print(f"  repr: {repr(content[:50])}")
                        print(f"  包含\\n: {'是' if '\\n' in content else '否'}")
                        print(f"  包含空格: {'是' if ' ' in content else '否'}")
                        
                        # 检查表格相关内容
                        if '|' in content:
                            print(f"  🔍 包含表格符号: {repr(content)}")
                        
                        # 检查标题相关内容
                        if '#' in content:
                            print(f"  📝 包含标题符号: {repr(content)}")
                        
                        print()
                        
                except json.JSONDecodeError:
                    pass
        
        # 4. 最终分析
        print(f"\n📊 最终分析:")
        print(f"总块数: {chunk_count}")
        print(f"最终内容长度: {len(final_content)}")
        print(f"换行符数量: {final_content.count(chr(10))}")
        print(f"空格数量: {final_content.count(' ')}")
        
        # 保存到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quick_test_{timestamp}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# 快速测试结果\n\n")
            f.write(f"测试时间: {datetime.now()}\n")
            f.write(f"总块数: {chunk_count}\n")
            f.write(f"最终长度: {len(final_content)}\n\n")
            f.write("## 原始内容\n\n")
            f.write(final_content)
            f.write("\n\n## 内容分析\n\n")
            f.write(f"换行符: {final_content.count(chr(10))}\n")
            f.write(f"空格: {final_content.count(' ')}\n")
            f.write(f"制表符: {final_content.count(chr(9))}\n")
            
            # 表格分析
            table_lines = [line for line in final_content.split('\n') if '|' in line]
            f.write(f"\n表格行数: {len(table_lines)}\n")
            if table_lines:
                f.write("表格行示例:\n")
                for i, line in enumerate(table_lines[:3]):
                    f.write(f"{i+1}. {repr(line)}\n")
        
        print(f"✅ 结果已保存到: {filename}")
        
        # 检查常见问题
        print(f"\n🔍 问题检查:")
        
        # 检查表格行之间是否有空行
        lines = final_content.split('\n')
        table_line_indices = [i for i, line in enumerate(lines) if '|' in line.strip()]
        
        if len(table_line_indices) > 1:
            for i in range(len(table_line_indices) - 1):
                current = table_line_indices[i]
                next_idx = table_line_indices[i + 1]
                if next_idx - current > 1:
                    between_lines = lines[current + 1:next_idx]
                    empty_lines = [line for line in between_lines if line.strip() == '']
                    if empty_lines:
                        print(f"⚠️ 表格行 {current+1} 和 {next_idx+1} 之间有 {len(empty_lines)} 个空行")
        
        # 检查标题和内容是否在同一行
        for i, line in enumerate(lines):
            if line.strip().startswith('#') and '|' in line:
                print(f"⚠️ 第 {i+1} 行标题和表格在同一行: {repr(line)}")
        
        print("\n🎯 测试完成!")
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")

if __name__ == "__main__":
    quick_test()
