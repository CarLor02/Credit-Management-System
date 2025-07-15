#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文档处理命令行工具
支持PDF、Excel、HTML和图像文件的批处理
支持嵌套子文件夹处理，保持原始目录结构
"""

import argparse
import logging
import os
from pathlib import Path
from document_utils import PdfProcessor, ExcelProcessor, ImageProcessor, HTMLProcessor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_nested_folders(input_root, output_root, file_type, save_intermediate, api_key, model, recursive=True):
    """
    处理嵌套的文件夹结构
    
    参数:
        input_root: 输入根目录
        output_root: 输出根目录
        file_type: 要处理的文件类型
        save_intermediate: 是否保存中间文件
        api_key: 云雾AI API密钥
        model: 使用的Gemini模型名称
        recursive: 是否递归处理子文件夹
    """
    input_path = Path(input_root)
    output_path = Path(output_root)
    
    # 确保输出根目录存在
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 如果不递归处理，只处理根目录
    if not recursive:
        process_single_folder(input_path, output_path, file_type, save_intermediate, api_key, model)
        return
    
    # 获取所有子文件夹（包括根目录）
    all_folders = [input_path]
    if recursive:
        all_folders.extend([f for f in input_path.rglob('*') if f.is_dir()])
    
    # 处理每个文件夹
    for folder in all_folders:
        # 计算相对路径
        rel_path = folder.relative_to(input_path) if folder != input_path else Path('')
        # 创建对应的输出文件夹
        current_output_folder = output_path / rel_path
        current_output_folder.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"处理文件夹: {folder}")
        logger.info(f"输出到: {current_output_folder}")
        
        # 处理当前文件夹
        process_single_folder(folder, current_output_folder, file_type, save_intermediate, api_key, model)

def process_single_folder(input_folder, output_folder, file_type, save_intermediate, api_key, model):
    """
    处理单个文件夹中的文件
    
    参数:
        input_folder: 输入文件夹路径
        output_folder: 输出文件夹路径
        file_type: 要处理的文件类型
        save_intermediate: 是否保存中间文件
        api_key: 云雾AI API密钥
        model: 使用的Gemini模型名称
    """
    # 处理PDF文件
    if file_type in ['pdf', 'all']:
        try:
            pdf_processor = PdfProcessor(
                input_path=input_folder,
                output_path=output_folder,
                save_intermediate=save_intermediate,
                api_key=api_key
            )
            pdf_results = pdf_processor.process_folder(
                extensions=['.pdf'],
                recursive=False  # 已经在外层处理递归
            )
            if pdf_results['total'] > 0:
                logger.info(f"PDF处理完成: 成功 {pdf_results['success']}, 失败 {pdf_results['fail']}")
        except ImportError as e:
            logger.error(f"无法处理PDF文件: {e}")
    
    # 处理Excel文件
    if file_type in ['excel', 'all']:
        try:
            excel_processor = ExcelProcessor(
                input_path=input_folder,
                output_path=output_folder
            )
            excel_results = excel_processor.process_folder(
                extensions=['.xlsx', '.xls'],
                recursive=False  # 已经在外层处理递归
            )
            if excel_results['total'] > 0:
                logger.info(f"Excel处理完成: 成功 {excel_results['success']}, 失败 {excel_results['fail']}")
        except ImportError as e:
            logger.error(f"无法处理Excel文件: {e}")
    
    # 处理HTML文件
    if file_type in ['html', 'all']:
        try:
            html_processor = HTMLProcessor(
                input_path=input_folder,
                output_path=output_folder
            )
            html_results = html_processor.process_folder(
                extensions=['.html', '.htm'],
                recursive=False  # 已经在外层处理递归
            )
            if html_results['total'] > 0:
                logger.info(f"HTML处理完成: 成功 {html_results['success']}, 失败 {html_results['fail']}")
        except ImportError as e:
            logger.error(f"无法处理HTML文件: {e}")
    
    # 处理图像文件
    if file_type in ['image', 'all']:
        try:
            image_processor = ImageProcessor(
                input_path=input_folder,
                output_path=output_folder,
                api_key=api_key,
                model=model
            )
            image_results = image_processor.process_folder(
                extensions=['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif'],
                recursive=False  # 已经在外层处理递归
            )
            if image_results['total'] > 0:
                logger.info(f"图像处理完成: 成功 {image_results['success']}, 失败 {image_results['fail']}")
        except ImportError as e:
            logger.error(f"无法处理图像文件: {e}")

def main():
    parser = argparse.ArgumentParser(description='文档批处理工具')
    parser.add_argument('--input', '-i', help='输入文件夹路径', default='./pdf_files')
    parser.add_argument('--output', '-o', help='输出文件夹路径', default='./output')
    parser.add_argument('--type', '-t', choices=['pdf', 'excel', 'html', 'image', 'all'], default='excel',
                        help='要处理的文件类型 (pdf, excel, html, image, all)')
    parser.add_argument('--save-intermediate', '-s', action='store_true', default=True,
                        help='是否保存中间文件')
    parser.add_argument('--api-key', '-k', help='云雾AI API密钥')
    parser.add_argument('--recursive', '-r', action='store_true', default=False,
                        help='是否递归处理子文件夹')
    parser.add_argument('--no-recursive', action='store_true', default=False,
                        help='禁用递归处理（与--recursive相反）')
    parser.add_argument('--model', '-m', default='gemini-2.0-flash-thinking-exp-01-21',
                        help='使用的Gemini模型名称（用于图像处理）')
    parser.add_argument('--preserve-structure', '-p', action='store_true', default=False,
                        help='是否保持原始目录结构')
    parser.add_argument('--no-preserve-structure', action='store_true', default=False,
                        help='禁用保持目录结构（与--preserve-structure相反）')
    
    args = parser.parse_args()
    
    # 处理互斥参数
    if args.no_recursive:
        args.recursive = False
    elif not args.recursive:
        args.recursive = True  # 默认开启递归
    
    if args.no_preserve_structure:
        args.preserve_structure = False
    elif not args.preserve_structure:
        args.preserve_structure = True  # 默认开启保持结构
    
    # 检查输入文件夹是否存在
    if not os.path.exists(args.input):
        logger.error(f"输入文件夹不存在: {args.input}")
        return
    
    # 创建输出文件夹
    os.makedirs(args.output, exist_ok=True)
    
    # 获取API密钥
    api_key = args.api_key or os.environ.get("YUNWU_API_KEY")
    
    # 如果需要保持目录结构，使用嵌套处理函数
    if args.preserve_structure:
        logger.info(f"开始处理文件夹: {args.input}，保持原始目录结构")
        process_nested_folders(
            args.input, 
            args.output, 
            args.type, 
            args.save_intermediate, 
            api_key, 
            args.model, 
            args.recursive
        )
    else:
        # 原始处理方式，不保持目录结构
        logger.info(f"开始处理文件夹: {args.input}，不保持原始目录结构")
        
        # 处理PDF文件
        if args.type in ['pdf', 'all']:
            try:
                logger.info("开始处理PDF文件...")
                pdf_processor = PdfProcessor(
                    input_path=args.input,
                    output_path=args.output,
                    save_intermediate=args.save_intermediate,
                    api_key=api_key
                )
                pdf_results = pdf_processor.process_folder(
                    extensions=['.pdf'],
                    recursive=args.recursive
                )
                logger.info(f"PDF处理完成: 成功 {pdf_results['success']}, 失败 {pdf_results['fail']}")
            except ImportError as e:
                logger.error(f"无法处理PDF文件: {e}")
        
        # 处理Excel文件
        if args.type in ['excel', 'all']:
            try:
                logger.info("开始处理Excel文件...")
                excel_processor = ExcelProcessor(
                    input_path=args.input,
                    output_path=args.output
                )
                excel_results = excel_processor.process_folder(
                    extensions=['.xlsx', '.xls'],
                    recursive=args.recursive
                )
                logger.info(f"Excel处理完成: 成功 {excel_results['success']}, 失败 {excel_results['fail']}")
            except ImportError as e:
                logger.error(f"无法处理Excel文件: {e}")
        
        # 处理HTML文件
        if args.type in ['html', 'all']:
            try:
                logger.info("开始处理HTML文件...")
                html_processor = HTMLProcessor(
                    input_path=args.input,
                    output_path=args.output
                )
                html_results = html_processor.process_folder(
                    extensions=['.html', '.htm'],
                    recursive=args.recursive
                )
                logger.info(f"HTML处理完成: 成功 {html_results['success']}, 失败 {html_results['fail']}")
            except ImportError as e:
                logger.error(f"无法处理HTML文件: {e}")
        
        # 处理图像文件
        if args.type in ['image', 'all']:
            try:
                logger.info("开始处理图像文件...")
                image_processor = ImageProcessor(
                    input_path=args.input,
                    output_path=args.output,
                    api_key=api_key,
                    model=args.model
                )
                image_results = image_processor.process_folder(
                    extensions=['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif'],
                    recursive=args.recursive
                )
                logger.info(f"图像处理完成: 成功 {image_results['success']}, 失败 {image_results['fail']}")
            except ImportError as e:
                logger.error(f"无法处理图像文件: {e}")
    
    logger.info("=" * 50)
    logger.info("所有处理完成")
    logger.info(f"输出文件保存在: {args.output}")

if __name__ == "__main__":
    main()
