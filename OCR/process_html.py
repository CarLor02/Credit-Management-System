#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HTML文档批处理脚本
将HTML文件转换为Markdown格式
"""

import os
import argparse
import logging
from pathlib import Path
from document_utils import HTMLProcessor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # 设置输入和输出文件夹
    input_folder = "./pdf_files"  # 修改为你的输入文件夹
    output_folder = "./output"    # 修改为你的输出文件夹
    
    # 创建HTML处理器
    try:
        html_processor = HTMLProcessor(
            input_path=input_folder,
            output_path=output_folder
        )
        
        # 执行批处理
        results = html_processor.process_folder(
            extensions=['.html', '.htm'],
            recursive=False
        )
        
        logger.info("=" * 50)
        logger.info("HTML处理完成")
        logger.info(f"成功: {results['success']}/{results['total']}")
        logger.info(f"失败: {results['fail']}/{results['total']}")
        logger.info(f"输出文件保存在: {output_folder}")
        
    except ImportError as e:
        logger.error(f"无法初始化HTML处理器: {e}")
        logger.error("请确保已安装所有必要的依赖项 (pip install beautifulsoup4 html2text requests)")
    except Exception as e:
        logger.error(f"处理HTML时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()