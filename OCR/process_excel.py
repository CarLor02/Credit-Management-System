#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Excel文档批处理脚本
"""

import logging
from document_utils import ExcelProcessor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # 设置输入和输出文件夹
    input_folder = "./pdf_files"  # Excel文件所在文件夹
    output_folder = "./output"    # Markdown输出文件夹
    
    # 创建Excel处理器
    try:
        excel_processor = ExcelProcessor(
            input_path=input_folder,
            output_path=output_folder
        )
        
        # 执行批处理
        results = excel_processor.process_folder(extensions=['.xlsx', '.xls'])
        
        logger.info("=" * 50)
        logger.info("Excel处理完成")
        logger.info(f"成功: {results['success']}/{results['total']}")
        logger.info(f"失败: {results['fail']}/{results['total']}")
        logger.info(f"输出文件保存在: {output_folder}")
        
    except ImportError as e:
        logger.error(f"无法初始化Excel处理器: {e}")
        logger.error("请确保已安装所有必要的依赖项")

if __name__ == "__main__":
    main()