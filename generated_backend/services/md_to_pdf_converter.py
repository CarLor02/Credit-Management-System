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
        
        # 初始化时尝试加载系统字体
        self._ensure_fonts_available()
        
    def _ensure_fonts_available(self):
        """确保中文字体可用"""
        try:
            import subprocess
            import sys
            
            # 更新字体缓存
            try:
                subprocess.run(['fc-cache', '-f'], check=False, capture_output=True)
                print("字体缓存已更新")
            except Exception as e:
                print(f"更新字体缓存失败: {e}")
                
            # 检查可用字体
            try:
                result = subprocess.run(['fc-list', ':lang=zh'], 
                                      capture_output=True, text=True, check=False)
                available_fonts = result.stdout
                print(f"检测到中文字体: {len(available_fonts.splitlines())} 个")
                
                # 检查关键字体是否可用
                key_fonts = ['Noto Sans CJK', 'WenQuanYi', 'Microsoft YaHei']
                for font in key_fonts:
                    if font in available_fonts:
                        print(f"✓ 找到字体: {font}")
                    else:
                        print(f"✗ 缺少字体: {font}")
                        
            except Exception as e:
                print(f"检查字体失败: {e}")
                
        except ImportError:
            pass
        
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
            text-indent: 2em;  /* 段落首行缩进两个字符 */
        }}

        /* 以冒号结尾的段落（如称呼）不缩进 */
        p.no-indent {{
            text-indent: 0;
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
        # 🔧 修复：在转换为HTML之前，预处理Markdown内容，修复换行符问题
        processed_content = self._preprocess_markdown_for_html(markdown_content)

        md = markdown.Markdown(
            extensions=MARKDOWN_EXTENSIONS,
            extension_configs=MARKDOWN_EXTENSION_CONFIGS
        )

        html_content = md.convert(processed_content)

        # 后处理HTML，为特定段落添加CSS类
        html_content = self._post_process_html(html_content)

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

    def _preprocess_markdown_for_html(self, markdown_content):
        """
        预处理Markdown内容，修复HTML转换时的换行符问题

        这个方法集成了前端的所有后处理逻辑，确保渲染一致性
        """
        if not markdown_content:
            return markdown_content

        try:
            # 应用通用的Markdown后处理逻辑
            processed_content = self._apply_universal_postprocessing(markdown_content)

            # 应用新的通用修复逻辑
            processed_content = self._apply_common_markdown_fixes(processed_content)

            return processed_content
        except Exception as e:
            print(f"⚠️ Markdown预处理失败: {e}")
            return markdown_content  # 出错时返回原内容

    def _apply_universal_postprocessing(self, content):
        """
        应用通用的Markdown后处理逻辑，与前端保持一致

        简化版本：只做最基本的清理，避免破坏原有格式
        """
        if not content:
            return content

        processed_content = content

        # 1. 清理Markdown代码块标记
        processed_content = re.sub(r'```markdown\s*\n', '', processed_content, flags=re.IGNORECASE)
        processed_content = re.sub(r'```\s*$', '', processed_content, flags=re.MULTILINE)
        processed_content = re.sub(r'```[\w]*\s*\n', '', processed_content, flags=re.IGNORECASE)
        processed_content = re.sub(r'```\s*\n', '', processed_content, flags=re.IGNORECASE)

        # 2. 修复冒号后换行问题
        processed_content = self._fix_colon_line_breaks(processed_content)

        # 3. 修复结论格式问题
        processed_content = self._fix_conclusion_format(processed_content)

        # 4. 基本的换行符修复 - 保守处理
        processed_content = self._fix_line_breaks_conservative(processed_content)

        # 4. 清理多余的空行
        processed_content = self._clean_extra_newlines(processed_content)

        return processed_content

    def _fix_colon_line_breaks(self, content):
        """
        修复冒号后的换行问题 - 特别处理文档开头的称呼格式
        支持冒号行和缩进内容之间有空行的情况
        """
        lines = content.split('\n')
        result_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]
            # 检查是否是以冒号结尾的行（通常是称呼或标题）
            if line.strip().endswith('：') or line.strip().endswith(':'):
                result_lines.append(line)
                i += 1

                # 跳过空行，寻找下一个有内容的行
                while i < len(lines) and lines[i].strip() == '':
                    result_lines.append(lines[i])  # 保持空行
                    i += 1

                # 检查是否有缩进内容
                if i < len(lines) and (lines[i].startswith('    ') or lines[i].startswith('\t')):
                    # 去掉缩进并添加到结果中
                    result_lines.append(lines[i].lstrip())
                    print(f"🔧 _fix_colon_line_breaks: 修复了缩进问题")
                    i += 1
                continue
            else:
                result_lines.append(line)
                i += 1

        return '\n'.join(result_lines)

    def _apply_common_markdown_fixes(self, content):
        """
        应用通用的Markdown修复逻辑，解决常见的格式问题

        修复的问题包括：
        1. 移除导致代码块的意外缩进
        2. 清理孤立的HTML标签（如<think>）
        3. 修复Mermaid图表格式
        4. 转换数字列表为标题格式
        """
        if not content:
            return content

        lines = content.split('\n')
        result_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # 1. 修复意外的缩进导致的代码块问题
            # 检测以冒号结尾的行后面跟着缩进的内容
            if line.strip().endswith('：') or line.strip().endswith(':'):
                result_lines.append(line)
                i += 1

                # 跳过空行，寻找下一个有内容的行
                while i < len(lines) and lines[i].strip() == '':
                    result_lines.append(lines[i])  # 保持空行
                    i += 1

                # 检查是否有意外缩进的内容
                if i < len(lines) and lines[i].startswith('    ') and not lines[i].strip().startswith('-') and not lines[i].strip().startswith('*'):
                    # 移除缩进，避免被解释为代码块
                    next_line = lines[i].lstrip()
                    if next_line:  # 只有非空行才处理
                        result_lines.append(next_line)
                        print(f"🔧 修复缩进问题: 移除了4个空格的缩进")
                    else:
                        result_lines.append(lines[i])  # 保持空行
                    i += 1
                continue  # 重要：跳过默认处理，避免重复添加

            # 2. 清理孤立的HTML标签
            elif line.strip() == '<think>' or line.strip().startswith('<think>'):
                # 跳过孤立的<think>标签
                print(f"🧹 清理孤立的HTML标签: {line.strip()}")
                i += 1
                continue

            # 3. 修复Mermaid图表格式
            elif line.strip().startswith('graph ') and (line.startswith('    ') or line.startswith('\t')):
                # 检测缩进的Mermaid图表，转换为正确的代码块格式
                print(f"🔧 修复Mermaid图表格式: {line.strip()}")
                result_lines.append('```mermaid')
                result_lines.append(line.strip())
                i += 1

                # 继续处理图表的其他行
                while i < len(lines) and (lines[i].strip() == '' or
                                        lines[i].startswith('   ') or
                                        lines[i].strip().startswith(('A[', 'B[', 'C[', 'D[', 'E[', 'F[')) or
                                        '-->' in lines[i]):
                    if lines[i].strip():
                        result_lines.append(lines[i].strip())
                    i += 1

                result_lines.append('```')
                continue

            # 4. 转换特定模式的数字列表为标题格式
            # 检测类似 "1. **战略定位**" 的模式，在特定上下文中转换为标题
            elif re.match(r'^\d+\.\s+\*\*[^*]+\*\*\s*$', line.strip()):
                # 检查上下文，如果前面是四级标题或者已经转换的五级标题，则转换为五级标题
                if len(result_lines) > 0:
                    # 查找最近的标题
                    recent_heading_level = 0
                    found_base_heading = False

                    for prev_line in reversed(result_lines[-15:]):  # 检查最近15行
                        if prev_line.strip().startswith('#'):
                            heading_level = len(prev_line.strip().split()[0])

                            # 如果找到四级标题，这是我们的基准
                            if heading_level == 4:
                                found_base_heading = True
                                break
                            # 如果找到五级标题且是数字开头，说明是我们转换的标题
                            elif heading_level == 5 and re.match(r'#####\s+\d+\.', prev_line.strip()):
                                found_base_heading = True
                                break
                            # 如果找到更高级别的标题（1-3级），停止搜索
                            elif heading_level < 4:
                                break

                    # 如果找到了基准标题，转换当前行为五级标题
                    if found_base_heading:
                        # 提取数字和标题文本
                        match = re.match(r'^(\d+)\.\s+\*\*([^*]+)\*\*\s*$', line.strip())
                        if match:
                            number, title = match.groups()
                            new_heading = f"##### {number}. {title.strip()}"
                            result_lines.append(new_heading)
                            print(f"🔄 转换列表为标题: {line.strip()} -> {new_heading}")
                            i += 1
                            continue

            # 默认情况：保持原行不变
            result_lines.append(line)
            i += 1

        return '\n'.join(result_lines)

    def _post_process_html(self, html_content):
        """
        后处理HTML内容，为特定段落添加CSS类
        """
        import re

        # 为以冒号结尾的段落添加no-indent类
        def add_no_indent_class(match):
            p_tag = match.group(0)
            # 检查段落内容是否以冒号结尾
            if '：' in p_tag or ':' in p_tag:
                # 如果段落内容以冒号结尾，添加no-indent类
                if p_tag.strip().endswith('：</p>') or p_tag.strip().endswith(':</p>'):
                    return p_tag.replace('<p>', '<p class="no-indent">')
            return p_tag

        # 使用正则表达式匹配所有段落标签
        processed_html = re.sub(r'<p>.*?</p>', add_no_indent_class, html_content, flags=re.DOTALL)

        return processed_html

    def _fix_conclusion_format(self, content):
        """
        修复结论格式问题 - 将缩进的结论内容转换为正常格式
        """
        lines = content.split('\n')
        result_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # 检查是否是缩进的结论行
            if re.match(r'^\s+\*\*结论：\*\*\s*$', line):
                # 添加无缩进的结论标题
                result_lines.append('**结论：**')
                i += 1

                # 处理后续的缩进数字列表
                while i < len(lines):
                    if i >= len(lines):
                        break
                    next_line = lines[i]

                    # 如果是空行，跳出循环
                    if not next_line.strip():
                        break

                    # 如果是缩进的数字列表项，去掉缩进
                    if re.match(r'^\s+(\d+\.\s.*)', next_line):
                        # 提取数字列表内容，去掉前面的空格
                        match = re.match(r'^\s+(\d+\.\s.*)', next_line)
                        if match:
                            result_lines.append(match.group(1))
                    else:
                        # 其他缩进内容也去掉缩进
                        result_lines.append(next_line.lstrip())
                    i += 1

                # 添加空行分隔
                result_lines.append('')
            else:
                result_lines.append(line)
                i += 1

        return '\n'.join(result_lines)

    def _fix_line_breaks_conservative(self, content):
        """
        保守的换行符修复 - 只处理明显需要修复的情况
        """
        lines = content.split('\n')
        result_lines = []

        for i, line in enumerate(lines):
            # 转换数字标题为Markdown标题
            line = self._convert_numbered_headings(line)
            result_lines.append(line)

            # 确保标题后有空行
            if line.startswith('#') and i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].startswith('#'):
                result_lines.append('')

            # 确保表格前有空行
            elif (i + 1 < len(lines) and
                  lines[i + 1].startswith('|') and
                  line.strip() and
                  not line.startswith('|')):
                result_lines.append('')

            # 确保表格后有空行
            elif (line.startswith('|') and
                  i + 1 < len(lines) and
                  lines[i + 1].strip() and
                  not lines[i + 1].startswith('|')):
                result_lines.append('')

        content = '\n'.join(result_lines)

        # 清理多余的空行
        content = re.sub(r'\n{3,}', '\n\n', content)

        return content

    def _convert_numbered_headings(self, line):
        """
        将数字开头的加粗文本转换为Markdown标题
        但只转换那些看起来像独立标题的，不转换列表项
        """
        # 匹配模式1: 数字. **文本**
        pattern1 = r'^(\s*)(\d+)\.\s*\*\*(.*?)\*\*\s*$'
        # 匹配模式2: 数字. **文本**：（带中文冒号）
        pattern2 = r'^(\s*)(\d+)\.\s*\*\*(.*?)\*\*：\s*$'

        match = re.match(pattern1, line) or re.match(pattern2, line)

        if match:
            indent, number, title = match.groups()

            # 只转换没有缩进的数字标题，有缩进的保持为列表项
            if len(indent) == 0:
                # 检查标题内容，如果是明显的章节标题才转换
                title_text = title.strip().lower()

                # 这些关键词表明是章节标题
                section_keywords = [
                    # 分析类
                    '分析', '评估', '建议', '策略', '方案', '计划', '措施',
                    '优化', '管理', '风险', '融资', '诊断', '结论', '总结',
                    '现状', '问题', '对策', '路径', '升级', '重组', '处置',
                    # 业务类
                    '资本', '治理', '产品', '创新', '能力', '储备', '体系',
                    '资质', '背书', '竞争', '对标', '监测', '供应链', '集中度',
                    '验证', '适配', '结构', '市场', '矩阵', '壁垒', '压力',
                    '波动', '瓶颈', '短期', '中期', '长期', '合规', '稳定',
                    # 财务类
                    '流动性', '盈利', '运营', '效率', '成本', '收入', '负债',
                    '资产', '现金流', '偿债', '融资', '投资', '回报',
                    # 其他重要词汇
                    '查询', '显示', '网络', '舆情', '客户', '技术', '专利',
                    '认证', '荣誉', '引入', '延伸', '研发'
                ]

                # 如果标题包含章节关键词，转换为h5标题
                if any(keyword in title_text for keyword in section_keywords):
                    return f"##### {number}. {title.strip()}"

        return line

    def _fix_line_breaks(self, content):
        """
        修复换行符问题 - 核心修复
        将单个换行符转换为Markdown双换行符，但保护表格和标题
        """
        # 先保护表格行（包含|的行）
        content = re.sub(r'(\|[^|\n]*\|)\n(?!\|)', r'\1\n\n', content)

        # 保护标题行 - 修复：确保标题后有空行
        content = re.sub(r'(#{1,6}[^\n]*)\n(?!#{1,6}|\n)', r'\1\n\n', content)

        # 保护列表项
        content = re.sub(r'(\s*[-*+]\s[^\n]*)\n(?!\s*[-*+]|\n)', r'\1\n\n', content)
        content = re.sub(r'(\s*\d+\.\s[^\n]*)\n(?!\s*\d+\.|\n)', r'\1\n\n', content)

        # 处理普通文本的单换行符：如果不是已经是双换行，就转换为双换行
        # 但要避免在表格、标题、列表中进行此操作
        lines = content.split('\n')
        result_lines = []

        for i, line in enumerate(lines):
            result_lines.append(line)

            # 如果当前行不为空，下一行也不为空，且都不是特殊格式
            if (i < len(lines) - 1 and
                line.strip() and
                lines[i + 1].strip() and
                not line.startswith('#') and  # 不是标题
                not lines[i + 1].startswith('#') and  # 下一行不是标题
                '|' not in line and  # 不是表格
                '|' not in lines[i + 1] and  # 下一行不是表格
                not re.match(r'^\s*[-*+]\s', line) and  # 不是列表
                not re.match(r'^\s*\d+\.\s', line)):  # 不是数字列表

                # 检查下一行是否为空，如果不是则添加空行
                if i + 1 < len(lines) and lines[i + 1].strip():
                    result_lines.append('')

        content = '\n'.join(result_lines)

        # 清理可能产生的三个或更多连续换行符
        content = re.sub(r'\n{3,}', '\n\n', content)

        return content

    def _fix_table_format(self, content):
        """修复表格格式"""
        # 确保表格前后有空行
        content = re.sub(r'([^\n])\n(\|)', r'\1\n\n\2', content)
        content = re.sub(r'(\|[^\n]*)\n([^\|\n])', r'\1\n\n\2', content)

        # 修复表格分隔符
        lines = content.split('\n')
        in_table = False
        result_lines = []

        for i, line in enumerate(lines):
            if '|' in line and line.strip():
                if not in_table:
                    # 表格开始，检查是否需要添加分隔符
                    in_table = True
                    result_lines.append(line)
                    # 如果下一行不是分隔符，添加一个
                    if i + 1 < len(lines) and not re.match(r'^\s*\|[\s\-\|:]+\|\s*$', lines[i + 1]):
                        # 生成分隔符行
                        cols = line.count('|') - 1
                        separator = '|' + '---|' * cols
                        result_lines.append(separator)
                else:
                    result_lines.append(line)
            else:
                if in_table:
                    in_table = False
                result_lines.append(line)

        return '\n'.join(result_lines)

    def _fix_heading_format(self, content):
        """修复标题格式"""
        # 确保#号后面有空格
        content = re.sub(r'^(#{1,6})([^#\s])', r'\1 \2', content, flags=re.MULTILINE)

        # 确保标题前有换行符（除了文档开头）
        content = re.sub(r'([^\n])\n(#{1,6}\s)', r'\1\n\n\2', content)

        # 不要自动转换"第X节"为标题，保持原有格式
        # 这样可以避免破坏原有的 Markdown 结构

        return content

    def _fix_list_format(self, content):
        """修复列表格式"""
        # 确保列表前有空行
        content = re.sub(r'([^\n])\n(\s*[-*+]\s)', r'\1\n\n\2', content)
        content = re.sub(r'([^\n])\n(\s*\d+\.\s)', r'\1\n\n\2', content)

        # 修复列表项之间的间距
        lines = content.split('\n')
        result_lines = []

        for i, line in enumerate(lines):
            result_lines.append(line)

            # 如果当前行是列表项，且下一行也是列表项，确保有适当的间距
            if re.match(r'^\s*[-*+]\s', line) or re.match(r'^\s*\d+\.\s', line):
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if (re.match(r'^\s*[-*+]\s', next_line) or re.match(r'^\s*\d+\.\s', next_line)) and next_line.strip():
                        # 如果下一行也是列表项，不需要额外空行
                        pass
                    elif next_line.strip() and not next_line.startswith(' '):
                        # 如果下一行不是空行且不是缩进内容，添加空行
                        result_lines.append('')

        return '\n'.join(result_lines)

    def _clean_extra_newlines(self, content):
        """清理多余的空行"""
        # 清理文档开头的空行
        content = re.sub(r'^\n+', '', content)

        # 清理文档结尾的空行
        content = re.sub(r'\n+$', '\n', content)

        # 将三个或更多连续换行符替换为两个
        content = re.sub(r'\n{3,}', '\n\n', content)

        return content

    def get_logo_base64(self):
        """获取logo的base64编码"""
        try:
            # 查找logo文件的路径，优先查找容器中的路径
            logo_paths = [
                # Docker容器中的路径（通过COPY或挂载）
                '/app/frontend/logo.jpg',
                # 相对路径查找
                'frontend/logo.jpg',
                '../frontend/logo.jpg', 
                'logo.jpg',
                # 基于当前文件位置的路径
                os.path.join(os.path.dirname(__file__), '../../frontend/logo.jpg'),
                os.path.join(os.path.dirname(__file__), '../../../frontend/logo.jpg'),
                # 绝对路径查找
                '/app/logo.jpg'
            ]

            for logo_path in logo_paths:
                if os.path.exists(logo_path):
                    print(f"✓ 找到logo文件: {logo_path}")
                    with open(logo_path, 'rb') as f:
                        logo_data = f.read()
                        return base64.b64encode(logo_data).decode('utf-8')

            # 如果找不到logo文件，输出调试信息
            print("✗ 未找到logo文件，尝试的路径:")
            for path in logo_paths:
                print(f"  - {path} (存在: {os.path.exists(path)})")
            
            # 列出当前工作目录和相关目录的内容
            current_dir = os.getcwd()
            print(f"当前工作目录: {current_dir}")
            
            # 检查相关目录
            for check_dir in ['/app', '/app/frontend', current_dir, '../frontend']:
                if os.path.exists(check_dir):
                    try:
                        files = os.listdir(check_dir)
                        jpg_files = [f for f in files if f.endswith('.jpg') or f.endswith('.png')]
                        if jpg_files:
                            print(f"目录 {check_dir} 中的图片文件: {jpg_files}")
                    except Exception as e:
                        print(f"无法列出目录 {check_dir}: {e}")
            
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
