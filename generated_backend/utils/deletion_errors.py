"""
删除项目时的错误处理工具函数
"""

def format_deletion_error(error_type: str, error_message: str) -> str:
    """
    格式化删除错误消息，使其更用户友好
    
    Args:
        error_type: 错误类型 ('knowledge_base', 'documents', 'report')
        error_message: 原始错误消息
        
    Returns:
        格式化后的用户友好错误消息
    """
    error_mapping = {
        'knowledge_base': {
            'timeout': '知识库服务响应超时，请稍后重试',
            'connection': '无法连接到知识库服务',
            'api_error': '知识库API调用失败',
            'not_found': '知识库不存在或已被删除',
            'permission': '没有权限删除知识库',
            'default': '知识库删除失败'
        },
        'documents': {
            'permission': '没有权限删除文档文件',
            'file_in_use': '文档文件正在被其他程序使用',
            'disk_space': '磁盘空间不足',
            'default': '文档文件删除失败'
        },
        'report': {
            'permission': '没有权限删除报告文件',
            'file_in_use': '报告文件正在被其他程序使用',
            'default': '报告文件删除失败'
        }
    }
    
    error_messages = error_mapping.get(error_type, {})
    
    # 检查常见错误模式
    error_lower = error_message.lower()
    
    if 'timeout' in error_lower or 'timed out' in error_lower:
        return error_messages.get('timeout', error_messages.get('default', error_message))
    elif 'connection' in error_lower or 'connect' in error_lower:
        return error_messages.get('connection', error_messages.get('default', error_message))
    elif 'permission' in error_lower or 'access' in error_lower:
        return error_messages.get('permission', error_messages.get('default', error_message))
    elif 'not found' in error_lower or '404' in error_lower:
        return error_messages.get('not_found', error_messages.get('default', error_message))
    elif 'in use' in error_lower or 'being used' in error_lower:
        return error_messages.get('file_in_use', error_messages.get('default', error_message))
    else:
        return error_messages.get('default', error_message)

def categorize_deletion_warnings(warnings: list) -> dict:
    """
    对删除警告进行分类和优先级排序
    
    Args:
        warnings: 警告消息列表
        
    Returns:
        分类后的警告字典
    """
    categorized = {
        'critical': [],    # 关键警告（可能影响系统正常运行）
        'important': [],   # 重要警告（可能影响用户体验）
        'minor': []        # 次要警告（不影响核心功能）
    }
    
    for warning in warnings:
        warning_lower = warning.lower()
        
        if any(keyword in warning_lower for keyword in ['知识库', 'knowledge_base', 'dataset']):
            categorized['critical'].append(warning)
        elif any(keyword in warning_lower for keyword in ['文档', 'document', '文件']):
            categorized['important'].append(warning)
        elif any(keyword in warning_lower for keyword in ['报告', 'report']):
            categorized['minor'].append(warning)
        else:
            categorized['important'].append(warning)
    
    return categorized

def generate_user_friendly_summary(warnings: list) -> str:
    """
    生成用户友好的警告摘要
    
    Args:
        warnings: 警告消息列表
        
    Returns:
        用户友好的摘要消息
    """
    if not warnings:
        return "项目删除成功"
    
    categorized = categorize_deletion_warnings(warnings)
    
    summary_parts = []
    
    if categorized['critical']:
        summary_parts.append(f"{len(categorized['critical'])}个关键问题")
    if categorized['important']:
        summary_parts.append(f"{len(categorized['important'])}个重要问题")
    if categorized['minor']:
        summary_parts.append(f"{len(categorized['minor'])}个次要问题")
    
    if len(warnings) == 1:
        return f"项目删除成功，但有1个问题需要注意"
    else:
        summary = "、".join(summary_parts)
        return f"项目删除成功，但有{summary}需要注意"
