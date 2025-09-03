#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown后处理服务
用于修复和优化Markdown内容，特别是表格格式
"""

import re
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class MarkdownPostProcessor:
    """Markdown后处理器"""
    
    def __init__(self):
        self.logger = logger
    
    def process(self, markdown_content: str) -> str:
        """
        处理Markdown内容，修复各种格式问题
        
        Args:
            markdown_content: 原始Markdown内容
            
        Returns:
            处理后的Markdown内容
        """
        if not markdown_content:
            return markdown_content
            
        try:
            # 1. 应用前端使用的正则表达式处理
            content = self.apply_frontend_regex_processing(markdown_content)
            
            # 2. 修复表格格式
            content = self.fix_table_format(content)
            
            # 3. 修复列表格式
            content = self.fix_list_format(content)
            
            # 4. 修复标题格式
            content = self.fix_heading_format(content)
            
            # 5. 清理多余的空行
            content = self.clean_extra_newlines(content)
            
            # 6. 修复代码块格式
            content = self.fix_code_block_format(content)
            
            self.logger.info("Markdown后处理完成")
            return content
            
        except Exception as e:
            self.logger.error(f"Markdown后处理失败: {str(e)}")
            return markdown_content  # 出错时返回原内容
    
    def apply_frontend_regex_processing(self, content: str) -> str:
        """
        应用前端使用的正则表达式处理逻辑
        
        处理逻辑包括：
        1. 将 \\n 替换为换行符
        2. 将 \r?\n 统一为 \n
        3. 移除代码块标记
        4. 在表格行前后添加换行符
        5. 在表格分隔符行前后添加换行符
        6. 在标题行前后添加换行符
        7. 在 | 符号前后添加空格
        8. 将多个连续换行符替换为最多2个换行符
        
        Args:
            content: 原始内容
            
        Returns:
            处理后的内容
        """
        if not content:
            return content
            
        # 1. 将 \\n 替换为换行符
        content = re.sub(r'\\n', '\n', content)
        
        # 2. 将 \r?\n 统一为 \n
        content = re.sub(r'\r?\n', '\n', content)
        
        # 3. 移除代码块标记 ```[a-zA-Z]*\n? 和 ```
        content = re.sub(r'```[a-zA-Z]*\n?', '', content)
        content = re.sub(r'```', '', content)
        
        # 🔧 修复：移除简单的表格处理，避免与完整表格处理冲突
        # 注释掉简单的表格行处理，使用完整的表格处理逻辑
        # content = re.sub(r'^(\|.*\|)$', r'\n\1\n', content, flags=re.MULTILINE)

        # 4. 在标题行前后添加换行符 (# 标题)
        content = re.sub(r'^(\s*#{1,6}\s.*)$', r'\n\1\n', content, flags=re.MULTILINE)

        # 🔧 修复：移除全局的|符号替换，避免破坏表格格式
        # 注释掉全局的|符号处理，在表格处理中单独处理
        # content = re.sub(r'\|', ' | ', content)
        
        # 8. 将多个连续换行符替换为最多2个换行符
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content
    
    def fix_table_format(self, content: str) -> str:
        """
        修复表格格式问题
        
        主要解决：
        1. 表格分隔符不正确
        2. 表格列对齐问题
        3. 表格边框缺失
        """
        lines = content.split('\n')
        processed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # 检测可能的表格行（包含 | 符号）
            if '|' in line and self._is_potential_table_row(line):
                table_lines = self._extract_table_block(lines, i)
                if table_lines:
                    # 处理表格块
                    processed_table = self._process_table_block(table_lines)
                    processed_lines.extend(processed_table)
                    i += len(table_lines)
                    continue
            
            processed_lines.append(lines[i])
            i += 1
        
        return '\n'.join(processed_lines)
    
    def _is_potential_table_row(self, line: str) -> bool:
        """判断是否可能是表格行"""
        if not line.strip():
            return False
            
        # 检查是否包含表格分隔符
        pipe_count = line.count('|')
        if pipe_count < 2:  # 至少需要2个|符号
            return False
            
        # 排除代码块中的内容
        if line.strip().startswith('```') or line.strip().startswith('`'):
            return False
            
        return True
    
    def _extract_table_block(self, lines: List[str], start_index: int) -> List[str]:
        """提取完整的表格块"""
        table_lines = []
        i = start_index
        
        # 向前查找表格开始
        while i > 0 and self._is_potential_table_row(lines[i-1]):
            i -= 1
        
        # 从表格开始提取所有表格行
        while i < len(lines):
            line = lines[i].strip()
            if self._is_potential_table_row(line) or self._is_table_separator(line):
                table_lines.append(lines[i])
                i += 1
            elif not line:  # 空行，可能是表格结束
                break
            else:
                break
        
        # 验证是否是有效的表格（至少2行）
        if len(table_lines) >= 2:
            return table_lines
        return []
    
    def _is_table_separator(self, line: str) -> bool:
        """判断是否是表格分隔符行"""
        line = line.strip()
        if not line:
            return False
            
        # 检查是否主要由 -, |, : 和空格组成
        allowed_chars = set('-|: ')
        return all(c in allowed_chars for c in line) and '|' in line
    
    def _process_table_block(self, table_lines: List[str]) -> List[str]:
        """处理表格块，修复格式问题"""
        if not table_lines:
            return table_lines
        
        # 解析表格数据
        rows = []
        separator_index = -1
        
        for i, line in enumerate(table_lines):
            line = line.strip()
            if self._is_table_separator(line):
                separator_index = i
                continue
                
            # 解析表格行
            cells = self._parse_table_row(line)
            if cells:
                rows.append(cells)
        
        if not rows:
            return table_lines
        
        # 确定列数（取最大列数）
        max_cols = max(len(row) for row in rows)
        
        # 标准化所有行的列数
        for row in rows:
            while len(row) < max_cols:
                row.append('')
        
        # 生成标准格式的表格
        result = []
        
        # 添加表头（第一行）
        if rows:
            header = '| ' + ' | '.join(rows[0]) + ' |'
            result.append(header)
            
            # 添加分隔符
            separator = '| ' + ' | '.join(['---'] * max_cols) + ' |'
            result.append(separator)
            
            # 添加数据行
            for row in rows[1:]:
                data_row = '| ' + ' | '.join(row) + ' |'
                result.append(data_row)
        
        return result
    
    def _parse_table_row(self, line: str) -> List[str]:
        """解析表格行，提取单元格内容"""
        if not line.strip():
            return []
            
        # 移除首尾的 | 符号
        line = line.strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        
        # 分割单元格
        cells = [cell.strip() for cell in line.split('|')]
        return cells
    
    def fix_list_format(self, content: str) -> str:
        """修复列表格式"""
        lines = content.split('\n')
        processed_lines = []
        
        for line in lines:
            # 修复列表项格式
            stripped = line.lstrip()
            if stripped.startswith(('- ', '* ', '+ ')):
                # 确保列表项前有正确的缩进
                indent = len(line) - len(stripped)
                processed_lines.append(' ' * indent + stripped)
            elif re.match(r'^\s*\d+\.\s', line):
                # 有序列表
                processed_lines.append(line)
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def fix_heading_format(self, content: str) -> str:
        """修复标题格式"""
        lines = content.split('\n')
        processed_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                # 确保#后面有空格
                match = re.match(r'^(#+)(.*)$', stripped)
                if match:
                    hashes, title = match.groups()
                    title = title.strip()
                    if title and not title.startswith(' '):
                        processed_lines.append(f"{hashes} {title}")
                    else:
                        processed_lines.append(f"{hashes}{title}")
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def clean_extra_newlines(self, content: str) -> str:
        """清理多余的空行"""
        # 将连续的多个空行替换为最多2个空行
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        return content.strip()
    
    def fix_code_block_format(self, content: str) -> str:
        """修复代码块格式"""
        # 确保代码块前后有空行
        content = re.sub(r'([^\n])\n```', r'\1\n\n```', content)
        content = re.sub(r'```\n([^\n])', r'```\n\n\1', content)
        return content


# 创建全局实例
markdown_postprocessor = MarkdownPostProcessor()


def process_markdown_content(content: str) -> str:
    """
    处理Markdown内容的便捷函数
    
    Args:
        content: 原始Markdown内容
        
    Returns:
        处理后的Markdown内容
    """
    return markdown_postprocessor.process(content)
