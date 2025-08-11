# -*- coding: utf-8 -*-
"""
配置文件 - 可以自定义PDF样式和设置
"""

# 页面设置
PAGE_CONFIG = {
    'size': 'A4',  # A4, A3, Letter, Legal
    'margin': '1cm 2cm 2cm 2cm',  # 上边距1cm，其他边距2cm
    'orientation': 'portrait'  # portrait (竖向) 或 landscape (横向)
}

# 字体设置
FONT_CONFIG = {
    'primary_fonts': [
        "PingFang SC",
        "Microsoft YaHei", 
        "SimHei",
        "Arial Unicode MS",
        "sans-serif"
    ],
    'code_fonts': [
        "Consolas",
        "Monaco", 
        "Courier New",
        "monospace"
    ],
    'base_font_size': '12pt',
    'line_height': 1.6
}

# 颜色主题
COLOR_THEME = {
    'text_color': '#000000',  # 改为全黑
    'heading_color': '#000000',  # 标题也改为全黑
    'link_color': '#3498db',
    'border_color': '#bdc3c7',
    'code_bg_color': '#f8f9fa',
    'quote_border_color': '#3498db',
    'quote_text_color': '#000000'  # 引用文字也改为全黑
}

# 标题样式
HEADING_STYLES = {
    'h1': {
        'font_size': '24pt',
        'margin_top': '1.5em',
        'margin_bottom': '0.5em'
    },
    'h2': {
        'font_size': '20pt',
        'border_bottom': '1px solid #bdc3c7',
        'margin_top': '1.5em',
        'margin_bottom': '0.5em'
    },
    'h3': {
        'font_size': '16pt',
        'margin_top': '1.5em',
        'margin_bottom': '0.5em'
    },
    'h4': {
        'font_size': '14pt',
        'margin_top': '1.5em',
        'margin_bottom': '0.5em'
    }
}

# 代码块样式
CODE_STYLE = {
    'background_color': '#f8f9fa',
    'border': '1px solid #e9ecef',
    'border_radius': '5px',
    'padding': '1em',
    'font_size': '0.9em'
}

# 表格样式
TABLE_STYLE = {
    'border_collapse': 'collapse',
    'border': '1px solid #ddd',
    'cell_padding': '8px',
    'header_bg_color': '#f2f2f2'
}

# Markdown扩展配置
MARKDOWN_EXTENSIONS = [
    'markdown.extensions.extra',
    'markdown.extensions.codehilite',
    'markdown.extensions.toc',
    'markdown.extensions.tables',
    'markdown.extensions.fenced_code'
]

MARKDOWN_EXTENSION_CONFIGS = {
    'markdown.extensions.codehilite': {
        'css_class': 'highlight',
        'use_pygments': True
    },
    'markdown.extensions.toc': {
        'permalink': False
    }
}
