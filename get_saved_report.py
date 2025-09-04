#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取已保存的报告内容进行分析
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5001"
PROJECT_ID = 5

def get_saved_report():
    """获取已保存的报告内容"""
    print(f"📄 获取项目 {PROJECT_ID} 的已保存报告")
    
    try:
        # 直接调用获取报告接口（不需要token）
        response = requests.get(f"{BASE_URL}/api/projects/{PROJECT_ID}/report", timeout=10)
        
        print(f"响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                content = result.get('content', '')
                file_path = result.get('file_path', '')
                company_name = result.get('company_name', '')
                
                print(f"✅ 获取报告成功!")
                print(f"公司名称: {company_name}")
                print(f"文件路径: {file_path}")
                print(f"内容长度: {len(content)}")
                
                # 保存到本地进行分析
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"saved_report_analysis_{timestamp}.md"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("# 已保存报告内容分析\n\n")
                    f.write(f"获取时间: {datetime.now()}\n")
                    f.write(f"项目ID: {PROJECT_ID}\n")
                    f.write(f"公司名称: {company_name}\n")
                    f.write(f"原始文件路径: {file_path}\n")
                    f.write(f"内容长度: {len(content)}\n\n")
                    f.write("## 格式分析\n\n")
                    
                    # 格式分析
                    lines = content.split('\n')
                    f.write(f"总行数: {len(lines)}\n")
                    f.write(f"换行符数量: {content.count(chr(10))}\n")
                    f.write(f"空格数量: {content.count(' ')}\n")
                    f.write(f"制表符数量: {content.count(chr(9))}\n\n")
                    
                    # 表格分析
                    table_lines = [(i+1, line) for i, line in enumerate(lines) if '|' in line.strip()]
                    f.write(f"表格行数: {len(table_lines)}\n")
                    if table_lines:
                        f.write("表格行示例:\n")
                        for line_num, line in table_lines[:5]:
                            f.write(f"  第{line_num}行: {repr(line)}\n")
                    f.write("\n")
                    
                    # 标题分析
                    title_lines = [(i+1, line) for i, line in enumerate(lines) if line.strip().startswith('#')]
                    f.write(f"标题行数: {len(title_lines)}\n")
                    if title_lines:
                        f.write("标题行示例:\n")
                        for line_num, line in title_lines[:5]:
                            f.write(f"  第{line_num}行: {repr(line)}\n")
                    f.write("\n")
                    
                    # 问题检查
                    f.write("## 问题检查\n\n")
                    
                    # 检查表格行之间的空行
                    if len(table_lines) > 1:
                        f.write("### 表格行间空行检查\n")
                        table_indices = [line_num-1 for line_num, _ in table_lines]
                        
                        for i in range(len(table_indices) - 1):
                            current = table_indices[i]
                            next_idx = table_indices[i + 1]
                            if next_idx - current > 1:
                                between_lines = lines[current + 1:next_idx]
                                empty_count = sum(1 for line in between_lines if line.strip() == '')
                                if empty_count > 0:
                                    f.write(f"⚠️ 表格行 {current+1} 和 {next_idx+1} 之间有 {empty_count} 个空行\n")
                        f.write("\n")
                    
                    # 检查标题和表格在同一行
                    f.write("### 标题表格混合检查\n")
                    for line_num, line in title_lines:
                        if '|' in line:
                            f.write(f"⚠️ 第{line_num}行标题和表格在同一行: {repr(line)}\n")
                    f.write("\n")
                    
                    # 原始内容
                    f.write("## 原始内容\n\n")
                    f.write("```markdown\n")
                    f.write(content)
                    f.write("\n```\n")
                
                print(f"📁 分析结果已保存到: {output_file}")
                
                # 控制台快速分析
                print(f"\n📊 快速分析:")
                print(f"总行数: {len(lines)}")
                print(f"换行符: {content.count(chr(10))}")
                print(f"空格: {content.count(' ')}")
                print(f"表格行: {len(table_lines)}")
                print(f"标题行: {len(title_lines)}")
                
                # 检查常见问题
                print(f"\n🔍 问题检查:")
                
                # 表格行间空行
                if len(table_lines) > 1:
                    table_indices = [line_num-1 for line_num, _ in table_lines]
                    empty_between_tables = 0
                    
                    for i in range(len(table_indices) - 1):
                        current = table_indices[i]
                        next_idx = table_indices[i + 1]
                        if next_idx - current > 1:
                            between_lines = lines[current + 1:next_idx]
                            empty_count = sum(1 for line in between_lines if line.strip() == '')
                            empty_between_tables += empty_count
                    
                    if empty_between_tables > 0:
                        print(f"⚠️ 发现表格行之间有 {empty_between_tables} 个空行")
                    else:
                        print(f"✅ 表格行之间没有多余空行")
                
                # 标题表格混合
                mixed_lines = [line for line_num, line in title_lines if '|' in line]
                if mixed_lines:
                    print(f"⚠️ 发现 {len(mixed_lines)} 行标题和表格混合")
                else:
                    print(f"✅ 标题和表格没有混合")
                
                return content
                
            else:
                print(f"❌ 获取失败: {result.get('error')}")
        
        elif response.status_code == 404:
            print("❌ 报告不存在，可能尚未生成")
        else:
            print(f"❌ HTTP错误 {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    return None

def main():
    """主函数"""
    print("📄 获取已保存的报告内容")
    print(f"目标: {BASE_URL}/api/projects/{PROJECT_ID}/report")
    
    content = get_saved_report()
    
    if content:
        print(f"\n🎯 获取成功! 这就是流式输出累积的最终结果")
        print(f"你可以分析这个内容来检查格式问题")
    else:
        print(f"\n❌ 获取失败")
        print(f"💡 建议:")
        print(f"1. 先生成一个报告")
        print(f"2. 检查项目ID是否正确")
        print(f"3. 检查后端服务是否正常")

if __name__ == "__main__":
    main()
