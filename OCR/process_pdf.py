#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PDF文档批处理脚本
"""

import os
import logging
from pathlib import Path
from document_utils import PdfProcessor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # 设置输入和输出文件夹
    input_folder = "/Users/bytedance/Documents/ai-platform/System/generated_backend/uploads/c24c92b7-1338-4317-94dc-5fabf094c940"  # 修改为你的输入文件夹
    output_folder = "/Users/bytedance/Documents/ai-platform/System/generated_backend/processed/c24c92b7-1338-4317-94dc-5fabf094c940"    # 修改为你的输出文件夹
    
    # 是否保存中间文件
    save_intermediate = True
    
    # 检查云雾API密钥
    api_key = os.environ.get("YUNWU_API_KEY")
    if not api_key:
        logger.warning("未设置YUNWU_API_KEY环境变量，扫描文档处理将不可用")
        logger.warning("请设置环境变量: export YUNWU_API_KEY='your-api-key'")
    
    # 创建PDF处理器
    try:
        pdf_processor = PdfProcessor(
            input_path=input_folder,
            output_path=output_folder,
            save_intermediate=save_intermediate,
            api_key=api_key
        )
        
        # 执行批处理
        results = pdf_processor.process_folder(extensions=['.pdf'])
        
        logger.info("=" * 50)
        logger.info("PDF处理完成")
        logger.info(f"成功: {results['success']}/{results['total']}")
        logger.info(f"失败: {results['fail']}/{results['total']}")
        logger.info(f"输出文件保存在: {output_folder}")
        
    except ImportError as e:
        logger.error(f"无法初始化PDF处理器: {e}")
        logger.error("请确保已安装所有必要的依赖项")

if __name__ == "__main__":
    main()