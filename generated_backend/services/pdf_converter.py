# -*- coding: utf-8 -*-
"""
PDF转换服务
将Markdown文件转换为PDF格式
"""

import os
import sys
import tempfile
import logging
from pathlib import Path
from typing import Optional, Tuple

try:
    from .md_to_pdf_converter import MarkdownToPDFConverter
except ImportError as e:
    logging.error(f"无法导入md_to_pdf_converter模块: {e}")
    MarkdownToPDFConverter = None


class PDFConverterService:
    """PDF转换服务类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.converter = None
        
        if MarkdownToPDFConverter:
            try:
                self.converter = MarkdownToPDFConverter()
                self.logger.info("PDF转换器初始化成功")
            except Exception as e:
                self.logger.error(f"PDF转换器初始化失败: {e}")
        else:
            self.logger.error("MarkdownToPDFConverter未能正确导入")
    
    def is_available(self) -> bool:
        """检查PDF转换功能是否可用"""
        return self.converter is not None
    
    def convert_md_to_pdf(self, md_file_path: str, output_pdf_path: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        将Markdown文件转换为PDF
        
        Args:
            md_file_path: Markdown文件路径
            output_pdf_path: 输出PDF文件路径，如果为None则自动生成
            
        Returns:
            Tuple[bool, str, Optional[str]]: (成功标志, 消息, PDF文件路径)
        """
        if not self.converter:
            return False, "PDF转换器未初始化", None
            
        try:
            # 检查输入文件是否存在
            if not os.path.exists(md_file_path):
                return False, f"Markdown文件不存在: {md_file_path}", None
            
            # 如果没有指定输出路径，则自动生成
            if output_pdf_path is None:
                md_path = Path(md_file_path)
                output_pdf_path = str(md_path.with_suffix('.pdf'))
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_pdf_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # 执行转换
            success = self.converter.convert_to_pdf(md_file_path, output_pdf_path)
            
            if success and os.path.exists(output_pdf_path):
                file_size = os.path.getsize(output_pdf_path)
                self.logger.info(f"PDF转换成功: {md_file_path} -> {output_pdf_path} ({file_size} bytes)")
                return True, "转换成功", output_pdf_path
            else:
                return False, "转换失败，未生成PDF文件", None
                
        except Exception as e:
            self.logger.error(f"PDF转换异常: {e}")
            return False, f"转换异常: {str(e)}", None
    
    def convert_md_content_to_pdf(self, md_content: str, company_name: str = "报告") -> Tuple[bool, str, Optional[str]]:
        """
        将Markdown内容转换为PDF
        
        Args:
            md_content: Markdown内容字符串
            company_name: 公司名称，用于生成文件名
            
        Returns:
            Tuple[bool, str, Optional[str]]: (成功标志, 消息, PDF文件路径)
        """
        if not self.converter:
            return False, "PDF转换器未初始化", None
            
        try:
            # 创建临时Markdown文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', 
                                           encoding='utf-8', delete=False) as temp_md:
                temp_md.write(md_content)
                temp_md_path = temp_md.name
            
            try:
                # 生成PDF文件路径
                safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).strip()
                if not safe_company_name:
                    safe_company_name = "报告"
                
                # 创建临时PDF文件
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                    temp_pdf_path = temp_pdf.name
                
                # 执行转换
                success = self.converter.convert_to_pdf(temp_md_path, temp_pdf_path)
                
                if success and os.path.exists(temp_pdf_path):
                    file_size = os.path.getsize(temp_pdf_path)
                    self.logger.info(f"PDF内容转换成功: {len(md_content)} chars -> {temp_pdf_path} ({file_size} bytes)")
                    return True, "转换成功", temp_pdf_path
                else:
                    # 清理临时PDF文件
                    if os.path.exists(temp_pdf_path):
                        os.unlink(temp_pdf_path)
                    return False, "转换失败，未生成PDF文件", None
                    
            finally:
                # 清理临时Markdown文件
                if os.path.exists(temp_md_path):
                    os.unlink(temp_md_path)
                    
        except Exception as e:
            self.logger.error(f"PDF内容转换异常: {e}")
            return False, f"转换异常: {str(e)}", None
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """清理临时文件"""
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
                self.logger.debug(f"已清理临时文件: {file_path}")
        except Exception as e:
            self.logger.warning(f"清理临时文件失败: {e}")


# 创建全局服务实例
pdf_converter_service = PDFConverterService()


def convert_report_to_pdf(md_content: str, company_name: str = "报告") -> Tuple[bool, str, Optional[str]]:
    """
    便捷函数：将报告内容转换为PDF
    
    Args:
        md_content: Markdown报告内容
        company_name: 公司名称
        
    Returns:
        Tuple[bool, str, Optional[str]]: (成功标志, 消息, PDF文件路径)
    """
    return pdf_converter_service.convert_md_content_to_pdf(md_content, company_name)


def is_pdf_conversion_available() -> bool:
    """检查PDF转换功能是否可用"""
    return pdf_converter_service.is_available()
