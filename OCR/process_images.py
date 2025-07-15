#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
图像文本提取批处理脚本
使用云雾AI的Gemini模型提取图像中的文本内容
"""

import os
import argparse
import logging
from pathlib import Path
from document_utils import ImageProcessor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # 设置输入和输出文件夹
    input_folder = "./pdf_files"  # 修改为你的输入文件夹
    output_folder = "./output"  # 修改为你的输出文件夹
    
    # 要处理的文件扩展名
    extensions = ['.jpg', '.jpeg', '.png']
    
    # 是否递归处理子文件夹
    recursive = False
    
    # 使用的模型
    model = "gemini-2.0-flash-exp"
    
    # 检查云雾API密钥
    api_key = os.environ.get("YUNWU_API_KEY")
    if not api_key:
        logger.error("未设置YUNWU_API_KEY环境变量，图像文本提取将不可用")
        logger.error("请设置环境变量: export YUNWU_API_KEY='your-api-key'")
        return
    
    # 创建图像处理器
    try:
        image_processor = ImageProcessor(
            input_path=input_folder,
            output_path=output_folder,
            api_key=api_key,
            model=model
        )
        
        # 执行批处理
        results = image_processor.process_folder(
            extensions=extensions,
            recursive=recursive
        )
        
        logger.info("=" * 50)
        logger.info("图像处理完成")
        logger.info(f"成功: {results['success']}/{results['total']}")
        logger.info(f"失败: {results['fail']}/{results['total']}")
        logger.info(f"输出文件保存在: {output_folder}")
        
    except ImportError as e:
        logger.error(f"无法初始化图像处理器: {e}")
        logger.error("请确保已安装所有必要的依赖项")
    except Exception as e:
        logger.error(f"处理图像时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
