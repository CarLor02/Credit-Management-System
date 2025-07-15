#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
图像文本提取脚本
使用云雾AI的Gemini Flash模型提取图像中的文本内容
"""

import argparse
import base64
import os
import time
from openai import OpenAI
import sys

def encode_image(image_path):
    """将图像编码为base64格式"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_text_from_image(image_path, api_key, model="gemini-2.0-flash", output_file=None, prompt=None):
    """
    从图像中提取文本
    
    参数:
        image_path: 图像文件路径
        api_key: 云雾AI API密钥
        model: 使用的模型名称
        output_file: 输出文件路径，如果为None则输出到控制台
        prompt: 自定义提示词，如果为None则使用默认提示词
    
    返回:
        提取的文本内容
    """
    # 检查文件是否存在
    if not os.path.exists(image_path):
        print(f"错误: 文件 '{image_path}' 不存在")
        return None
    
    # 获取文件扩展名
    _, ext = os.path.splitext(image_path)
    ext = ext.lower().lstrip('.')
    
    # 确定MIME类型
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'bmp': 'image/bmp',
        'tiff': 'image/tiff',
        'tif': 'image/tiff'
    }
    
    mime_type = mime_types.get(ext, 'image/jpeg')  # 默认为jpeg
    
    # 编码图像
    try:
        base64_image = encode_image(image_path)
    except Exception as e:
        print(f"错误: 无法读取或编码图像: {e}")
        return None
    
    # 创建OpenAI客户端
    client = OpenAI(
        base_url="https://yunwu.ai/v1",
        api_key=api_key
    )
    
    # 默认提示词
    if prompt is None:
        prompt = "请提取这个图像中的所有文本内容，并以Markdown格式返回。忽略水印和章，保留原始格式和表格结构。"
    
    # 调用API
    try:
        print(f"正在处理图像: {image_path}")
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1  # 使用较低的温度以获得更确定性的结果
        )
        
        processing_time = time.time() - start_time
        print(f"处理完成，耗时: {processing_time:.2f}秒")
        
        # 提取内容
        content = response.choices[0].message.content
        
        # 输出结果
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"结果已保存到: {output_file}")
        else:
            print("\n--- 提取结果 ---\n")
            print(content)
            print("\n--- 结果结束 ---\n")
        
        return content
        
    except Exception as e:
        print(f"错误: 调用API时出错: {e}")
        return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='从图像中提取文本内容')
    parser.add_argument('image_path', help='图像文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径，如果不指定则输出到控制台')
    parser.add_argument('-m', '--model', default='gemini-2.5-pro-preview-05-06', 
                        help='使用的模型名称 (默认: gemini-2.5-pro-preview-05-06)')
    parser.add_argument('-p', '--prompt', 
                        help='自定义提示词，如果不指定则使用默认提示词')
    parser.add_argument('-k', '--key', help='云雾AI API密钥，如果不指定则从环境变量YUNWU_API_KEY中获取')
    
    args = parser.parse_args()
    
    # 获取API密钥
    api_key = args.key or os.environ.get('YUNWU_API_KEY')
    if not api_key:
        print("错误: 未提供API密钥，请使用-k参数指定或设置YUNWU_API_KEY环境变量")
        sys.exit(1)
    
    # 提取文本
    extract_text_from_image(
        args.image_path, 
        api_key, 
        model=args.model, 
        output_file=args.output,
        prompt=args.prompt
    )

if __name__ == "__main__":
    main()