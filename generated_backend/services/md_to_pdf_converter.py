#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to PDF Converter with Chinese Support
支持中文的Markdown转PDF工具
"""

import os
import sys
import argparse
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import tempfile
from pathlib import Path
import base64
import datetime
import re
try:
    from .pdf_config import (
        PAGE_CONFIG, FONT_CONFIG, COLOR_THEME, HEADING_STYLES,
        CODE_STYLE, TABLE_STYLE, MARKDOWN_EXTENSIONS, MARKDOWN_EXTENSION_CONFIGS
    )
except ImportError:
    # 如果没有配置文件，使用默认配置
    PAGE_CONFIG = {'size': 'A4', 'margin': '2cm', 'orientation': 'portrait'}
    FONT_CONFIG = {
        'primary_fonts': ["PingFang SC", "Microsoft YaHei", "SimHei", "Arial Unicode MS", "sans-serif"],
        'code_fonts': ["Consolas", "Monaco", "Courier New", "monospace"],
        'base_font_size': '12pt',
        'line_height': 1.6
    }
    COLOR_THEME = {
        'text_color': '#333333', 'heading_color': '#2c3e50', 'link_color': '#3498db',
        'border_color': '#bdc3c7', 'code_bg_color': '#f8f9fa',
        'quote_border_color': '#3498db', 'quote_text_color': '#7f8c8d'
    }
    HEADING_STYLES = {
        'h1': {'font_size': '24pt', 'border_bottom': '2px solid #3498db'},
        'h2': {'font_size': '20pt', 'border_bottom': '1px solid #bdc3c7'},
        'h3': {'font_size': '16pt'}, 'h4': {'font_size': '14pt'}
    }
    CODE_STYLE = {'background_color': '#f8f9fa', 'border': '1px solid #e9ecef'}
    TABLE_STYLE = {'border': '1px solid #ddd', 'cell_padding': '8px'}
    MARKDOWN_EXTENSIONS = ['markdown.extensions.extra', 'markdown.extensions.codehilite',
                          'markdown.extensions.toc', 'markdown.extensions.tables',
                          'markdown.extensions.fenced_code']
    MARKDOWN_EXTENSION_CONFIGS = {
        'markdown.extensions.codehilite': {'css_class': 'highlight', 'use_pygments': True},
        'markdown.extensions.toc': {'permalink': False}
    }


class MarkdownToPDFConverter:
    def __init__(self):
        self.font_config = FontConfiguration()
        
    def get_css_styles(self):
        """获取CSS样式，包含中文字体支持"""
        primary_fonts = ', '.join(f'"{font}"' for font in FONT_CONFIG['primary_fonts'])
        code_fonts = ', '.join(f'"{font}"' for font in FONT_CONFIG['code_fonts'])

        return f"""
        @page {{
            size: {PAGE_CONFIG['size']};
            margin: {PAGE_CONFIG['margin']};
        }}

        body {{
            font-family: {primary_fonts};
            font-size: {FONT_CONFIG['base_font_size']};
            line-height: {FONT_CONFIG['line_height']};
            color: {COLOR_THEME['text_color']};
            max-width: 100%;
            margin: 0;
            padding: 0;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            font-family: {primary_fonts};
            color: {COLOR_THEME['heading_color']};
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            font-weight: bold;
        }}

        h1 {{
            font-size: {HEADING_STYLES['h1']['font_size']};
        }}

        h2 {{
            font-size: {HEADING_STYLES['h2']['font_size']};
            border-bottom: {HEADING_STYLES['h2']['border_bottom']};
            padding-bottom: 0.2em;
        }}

        h3 {{
            font-size: {HEADING_STYLES['h3']['font_size']};
        }}

        h4 {{
            font-size: {HEADING_STYLES['h4']['font_size']};
        }}
        
        p {{
            margin-bottom: 1em;
            text-align: justify;
        }}
        
        code {{
            font-family: {code_fonts};
            background-color: {CODE_STYLE.get('background_color', '#f8f9fa')};
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 0.9em;
        }}

        pre {{
            background-color: {CODE_STYLE.get('background_color', '#f8f9fa')};
            border: {CODE_STYLE.get('border', '1px solid #e9ecef')};
            border-radius: 5px;
            padding: 1em;
            overflow-x: auto;
            margin: 1em 0;
        }}
        
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        
        blockquote {{
            border-left: 4px solid {COLOR_THEME['quote_border_color']};
            margin: 1em 0;
            padding-left: 1em;
            color: {COLOR_THEME['quote_text_color']};
            font-style: italic;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        
        th, td {{
            border: {TABLE_STYLE.get('border', '1px solid #ddd')};
            padding: {TABLE_STYLE.get('cell_padding', '8px')};
            text-align: left;
        }}

        th {{
            background-color: {TABLE_STYLE.get('header_bg_color', '#f2f2f2')};
            font-weight: bold;
        }}
        
        ul, ol {{
            margin: 1em 0;
            padding-left: 2em;
        }}

        li {{
            margin-bottom: 0.5em;
        }}
        
        a {{
            color: {COLOR_THEME['link_color']};
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}

        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1em auto;
        }}
        
        .page-break {{
            page-break-before: always;
        }}
        """
    
    def convert_markdown_to_html(self, markdown_content, file_path=None):
        """将Markdown内容转换为HTML"""
        md = markdown.Markdown(
            extensions=MARKDOWN_EXTENSIONS,
            extension_configs=MARKDOWN_EXTENSION_CONFIGS
        )

        html_content = md.convert(markdown_content)

        # 获取与PDF相同的CSS样式
        css_styles = self.get_css_styles()

        # 创建完整的HTML文档，包含与PDF相同的样式
        full_html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>征信报告</title>
            <style>
                {css_styles}
                /* 针对HTML预览的额外样式调整 */
                body {{
                    max-width: 800px;
                    margin: 20px auto;
                    padding: 20px;
                    background-color: white;
                }}
                @page {{
                    /* 移除打印相关的页面设置 */
                }}
                /* 报告头部样式 */
                .report-header {{
                    position: relative;
                    text-align: center;
                    margin-bottom: 40px;
                    padding-top: 60px;
                }}
                .report-logo {{
                    position: absolute;
                    left: 0;
                    top: 0;
                    height: 40px;
                    width: auto;
                }}
                .report-title {{
                    color: #000000;
                    font-size: 32px;
                    font-weight: bold;
                    margin: 0;
                    padding: 0;
                    margin-top: 20px;
                }}
                .report-time {{
                    color: #666666;
                    font-size: 14px;
                    margin-top: 8px;
                    font-weight: normal;
                }}
            </style>
        </head>
        <body>
            <div class="report-header">
                <img src="data:image/png;base64,{self.get_logo_base64()}" alt="Logo" class="report-logo">
                <h1 class="report-title">征信报告</h1>
                <div class="report-time">{self.extract_report_time(markdown_content, file_path)}</div>
            </div>
            {html_content}
        </body>
        </html>
        """

        return full_html

    def get_logo_base64(self):
        """获取logo的base64编码"""
        try:
            # 查找logo文件的路径
            logo_paths = [
                'logo.jpg',
                'frontend/logo.jpg',
                '../frontend/logo.jpg',
                os.path.join(os.path.dirname(__file__), '../../frontend/logo.jpg'),
                os.path.join(os.path.dirname(__file__), '../../../frontend/logo.jpg')
            ]

            for logo_path in logo_paths:
                if os.path.exists(logo_path):
                    with open(logo_path, 'rb') as f:
                        logo_data = f.read()
                        return base64.b64encode(logo_data).decode('utf-8')

            # 如果找不到logo文件，返回空字符串
            return ""
        except Exception as e:
            print(f"获取logo失败: {e}")
            return ""

    def extract_report_time(self, markdown_content, file_path=None):
        """从Markdown内容中提取报告生成时间，优先使用文件修改时间"""
        import re

        # 首先尝试从文件修改时间获取
        if file_path and os.path.exists(file_path):
            try:
                # 获取文件的最后修改时间
                mtime = os.path.getmtime(file_path)
                file_time = datetime.datetime.fromtimestamp(mtime)
                return f"生成时间：{file_time.strftime('%Y-%m-%d %H:%M:%S')}"
            except Exception as e:
                print(f"获取文件修改时间失败: {e}")

        # 如果文件时间获取失败，尝试从内容中提取
        time_patterns = [
            r'生成时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
            r'报告时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
            r'创建时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
            r'时间[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',  # 直接匹配时间格式
            r'生成时间[：:]\s*(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})',
            r'(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})',  # 斜杠分隔的日期
        ]

        for pattern in time_patterns:
            match = re.search(pattern, markdown_content)
            if match:
                return f"生成时间：{match.group(1)}"

        # 如果都没有找到，返回当前时间作为最后的回退
        return f"生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def get_logo_base64(self):
        """获取logo的base64编码"""
        try:
            # 查找logo文件的路径
            logo_paths = [
                'logo.jpg',
                'frontend/logo.jpg',
                '../frontend/logo.jpg',
                os.path.join(os.path.dirname(__file__), '../../frontend/logo.jpg'),
                os.path.join(os.path.dirname(__file__), '../../../frontend/logo.jpg')
            ]

            for logo_path in logo_paths:
                if os.path.exists(logo_path):
                    with open(logo_path, 'rb') as f:
                        logo_data = f.read()
                        return base64.b64encode(logo_data).decode('utf-8')

            # 如果找不到logo文件，返回空字符串
            return ""
        except Exception as e:
            print(f"获取logo失败: {e}")
            return ""


    
    def convert_to_pdf(self, input_file, output_file=None):
        """将Markdown文件转换为PDF"""
        try:
            # 读取Markdown文件
            with open(input_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # 转换为HTML
            html_content = self.convert_markdown_to_html(markdown_content, input_file)
            
            # 设置输出文件名
            if output_file is None:
                input_path = Path(input_file)
                output_file = input_path.with_suffix('.pdf')
            
            # 创建临时HTML文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', 
                                           encoding='utf-8', delete=False) as temp_html:
                temp_html.write(html_content)
                temp_html_path = temp_html.name
            
            try:
                # 转换为PDF
                css = CSS(string=self.get_css_styles(), font_config=self.font_config)
                html_doc = HTML(filename=temp_html_path)
                html_doc.write_pdf(output_file, stylesheets=[css], 
                                 font_config=self.font_config)
                
                print(f"✅ 转换成功: {input_file} -> {output_file}")
                return True
                
            finally:
                # 清理临时文件
                os.unlink(temp_html_path)
                
        except Exception as e:
            print(f"❌ 转换失败: {str(e)}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description='将Markdown文件转换为PDF (支持中文)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python md2pdf.py input.md                    # 输出为 input.pdf
  python md2pdf.py input.md -o output.pdf      # 指定输出文件名
  python md2pdf.py *.md                        # 批量转换
        """
    )
    
    parser.add_argument('input_files', nargs='+', 
                       help='输入的Markdown文件路径 (支持通配符)')
    parser.add_argument('-o', '--output', 
                       help='输出PDF文件路径 (仅在单文件转换时有效)')
    
    args = parser.parse_args()
    
    converter = MarkdownToPDFConverter()
    
    # 处理多个文件
    success_count = 0
    total_count = len(args.input_files)
    
    for input_file in args.input_files:
        if not os.path.exists(input_file):
            print(f"⚠️  文件不存在: {input_file}")
            continue
            
        if not input_file.lower().endswith('.md'):
            print(f"⚠️  跳过非Markdown文件: {input_file}")
            continue
        
        # 确定输出文件名
        output_file = None
        if args.output and total_count == 1:
            output_file = args.output
        
        if converter.convert_to_pdf(input_file, output_file):
            success_count += 1
    
    print(f"\n📊 转换完成: {success_count}/{total_count} 个文件成功转换")


if __name__ == '__main__':
    main()
