/**
 * 错误信息映射工具
 * 将HTTP状态码和错误类型转换为用户友好的错误信息
 */

// HTTP状态码到用户友好错误信息的映射
export const HTTP_ERROR_MESSAGES: Record<number, string> = {
  // 客户端错误 4xx
  400: '请求参数有误，请检查输入信息',
  401: '登录已过期，请重新登录',
  403: '您没有权限执行此操作',
  404: '请求的资源不存在',
  405: '不支持的操作方式',
  408: '请求超时，请稍后重试',
  409: '操作冲突，请刷新页面后重试',
  422: '提交的数据格式不正确',
  429: '操作过于频繁，请稍后重试',
  
  // 服务器错误 5xx
  500: '服务器内部错误，请稍后重试',
  501: '服务暂不支持此功能',
  502: '服务器网关错误，请稍后重试',
  503: '服务暂时不可用，请稍后重试',
  504: '服务器响应超时，请稍后重试',
  
  // 网络错误
  0: '网络连接失败，请检查网络设置'
};

// 认证相关的特定错误信息
export const AUTH_ERROR_MESSAGES: Record<string, string> = {
  'invalid_credentials': '用户名或密码错误',
  'user_not_found': '用户不存在',
  'user_disabled': '账户已被禁用，请联系管理员',
  'email_exists': '邮箱已被注册，请使用其他邮箱',
  'username_exists': '用户名已存在，请选择其他用户名',
  'weak_password': '密码强度不够，请使用至少6位字符',
  'invalid_email': '邮箱格式不正确',
  'token_expired': '登录已过期，请重新登录',
  'token_invalid': '登录状态无效，请重新登录',
  'missing_token': '请先登录后再进行操作',
  'permission_denied': '您没有权限执行此操作',
  'old_password_incorrect': '原密码不正确',
  'password_mismatch': '两次输入的密码不一致'
};

// 业务相关的错误信息
export const BUSINESS_ERROR_MESSAGES: Record<string, string> = {
  'project_not_found': '项目不存在或已被删除',
  'document_not_found': '文档不存在或已被删除',
  'file_too_large': '文件大小超出限制，请选择较小的文件',
  'file_type_not_supported': '不支持的文件类型',
  'upload_failed': '文件上传失败，请重试',
  'processing_failed': '文件处理失败，请检查文件格式',
  'report_generation_failed': '报告生成失败，请稍后重试',
  'insufficient_data': '数据不足，无法生成报告',
  'quota_exceeded': '已超出使用配额，请升级账户',
  'operation_not_allowed': '当前状态下不允许此操作'
};

// 网络相关错误信息
export const NETWORK_ERROR_MESSAGES: Record<string, string> = {
  'network_error': '网络连接失败，请检查网络设置',
  'timeout': '请求超时，请稍后重试',
  'connection_refused': '无法连接到服务器，请稍后重试',
  'dns_error': '域名解析失败，请检查网络设置',
  'ssl_error': '安全连接失败，请检查网络设置'
};

/**
 * 根据HTTP状态码获取用户友好的错误信息
 */
export function getHttpErrorMessage(statusCode: number): string {
  return HTTP_ERROR_MESSAGES[statusCode] || '未知错误，请稍后重试';
}

/**
 * 根据错误类型获取用户友好的错误信息
 */
export function getErrorMessage(errorType: string): string {
  // 优先查找认证错误
  if (AUTH_ERROR_MESSAGES[errorType]) {
    return AUTH_ERROR_MESSAGES[errorType];
  }
  
  // 查找业务错误
  if (BUSINESS_ERROR_MESSAGES[errorType]) {
    return BUSINESS_ERROR_MESSAGES[errorType];
  }
  
  // 查找网络错误
  if (NETWORK_ERROR_MESSAGES[errorType]) {
    return NETWORK_ERROR_MESSAGES[errorType];
  }
  
  return errorType || '操作失败，请稍后重试';
}

/**
 * 解析API错误响应，返回用户友好的错误信息
 */
export function parseApiError(error: any): string {
  // 如果是字符串，直接返回
  if (typeof error === 'string') {
    return getErrorMessage(error);
  }
  
  // 如果有response对象（axios风格）
  if (error.response) {
    const { status, data } = error.response;
    
    // 优先使用后端返回的错误信息
    if (data && data.error) {
      return getErrorMessage(data.error);
    }
    
    // 使用状态码映射
    return getHttpErrorMessage(status);
  }
  
  // 如果是fetch API错误
  if (error.status) {
    return getHttpErrorMessage(error.status);
  }
  
  // 网络错误
  if (error.name === 'NetworkError' || error.message?.includes('fetch')) {
    return NETWORK_ERROR_MESSAGES.network_error;
  }
  
  // 超时错误
  if (error.name === 'TimeoutError' || error.message?.includes('timeout')) {
    return NETWORK_ERROR_MESSAGES.timeout;
  }
  
  // 默认错误信息
  return error.message || '操作失败，请稍后重试';
}

/**
 * 根据错误类型获取错误级别
 */
export function getErrorLevel(errorType: string): 'error' | 'warning' | 'info' {
  // 认证错误通常是警告级别
  if (AUTH_ERROR_MESSAGES[errorType]) {
    return 'warning';
  }
  
  // 权限错误是警告级别
  if (errorType.includes('permission') || errorType.includes('forbidden')) {
    return 'warning';
  }
  
  // 网络错误是错误级别
  if (NETWORK_ERROR_MESSAGES[errorType]) {
    return 'error';
  }
  
  // 其他默认为错误级别
  return 'error';
}

/**
 * 格式化错误信息，添加建议操作
 */
export function formatErrorWithSuggestion(errorType: string): { message: string; suggestion?: string } {
  const message = getErrorMessage(errorType);
  
  const suggestions: Record<string, string> = {
    'network_error': '请检查网络连接后重试',
    'token_expired': '请重新登录',
    'permission_denied': '请联系管理员获取权限',
    'file_too_large': '请选择小于10MB的文件',
    'quota_exceeded': '请升级账户或联系客服',
    'invalid_credentials': '请检查用户名和密码是否正确'
  };
  
  return {
    message,
    suggestion: suggestions[errorType]
  };
}
