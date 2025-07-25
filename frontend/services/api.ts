/**
 * API服务层
 * 统一处理API调用和Mock数据切换
 */

import { parseApiError, getHttpErrorMessage } from '../utils/errorMessages';

// API基础URL配置
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5001/api';

/**
 * 通用API响应类型
 */
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

/**
 * HTTP请求方法
 */
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

/**
 * 请求配置
 */
interface RequestConfig {
  method?: HttpMethod;
  headers?: Record<string, string>;
  body?: any;
}

/**
 * 基础API客户端类
 */
class ApiClient {
  public baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * 发送HTTP请求
   */
  async request<T>(endpoint: string, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    const { method = 'GET', headers = {}, body } = config;

    try {
      // 真实API调用
      const url = `${this.baseUrl}${endpoint}`;

      // 自动添加认证头
      const finalHeaders: Record<string, string> = {
        'Content-Type': 'application/json',
        ...headers,
      };

      // 如果有token且不是登录/注册请求，自动添加Authorization头
      if (typeof window !== 'undefined' &&
          !endpoint.includes('/auth/login') &&
          !endpoint.includes('/auth/register')) {
        const token = localStorage.getItem('auth_token');
        if (token) {
          // 检查token是否过期
          try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const isExpired = payload.exp * 1000 < Date.now();

            if (!isExpired) {
              finalHeaders['Authorization'] = `Bearer ${token}`;
            } else {
              // Token过期，清除本地存储
              localStorage.removeItem('auth_token');
              localStorage.removeItem('auth_user');
            }
          } catch (error) {
            // Token格式错误，清除本地存储
            localStorage.removeItem('auth_token');
            localStorage.removeItem('auth_user');
          }
        }
      }

      const response = await fetch(url, {
        method,
        headers: finalHeaders,
        body: body ? JSON.stringify(body) : undefined,
      });

      if (!response.ok) {
        // 尝试解析错误响应
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          // 如果无法解析JSON，使用状态码生成错误信息
          throw new Error(getHttpErrorMessage(response.status));
        }

        // 如果后端返回了具体的错误信息，使用它
        if (errorData && errorData.error) {
          throw new Error(parseApiError(errorData.error));
        }

        // 否则使用状态码映射
        throw new Error(getHttpErrorMessage(response.status));
      }

      const responseData = await response.json();

      // 如果后端已经返回了包含success和data字段的结构，直接返回
      if (responseData.success !== undefined && responseData.data !== undefined) {
        return responseData;
      }

      // 否则包装成标准格式
      return {
        success: true,
        data: responseData,
      };

    } catch (error) {
      console.error(`API Error: ${method} ${endpoint}`, error);

      // 使用友好的错误信息
      const friendlyError = parseApiError(error);

      return {
        success: false,
        error: friendlyError,
      };
    }
  }

  /**
   * GET请求
   */
  async get<T>(endpoint: string, headers?: Record<string, string>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET', headers });
  }

  /**
   * GET请求 - 下载文件（返回Blob）
   */
  async getBlob(endpoint: string, headers?: Record<string, string>): Promise<ApiResponse<Blob>> {

    try {
      // 真实API调用
      const url = `${this.baseUrl}${endpoint}`;

      // 自动添加认证头
      const finalHeaders = {
        ...headers,
      };

      // 如果有token且不是认证相关的请求，自动添加Authorization头
      if (typeof window !== 'undefined' && !endpoint.includes('/auth/')) {
        const token = localStorage.getItem('auth_token');
        if (token) {
          // 检查token是否过期
          try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const isExpired = payload.exp * 1000 < Date.now();

            if (!isExpired) {
              finalHeaders['Authorization'] = `Bearer ${token}`;
            } else {
              // Token过期，清除本地存储
              localStorage.removeItem('auth_token');
              localStorage.removeItem('auth_user');
            }
          } catch (error) {
            // Token格式错误，清除本地存储
            localStorage.removeItem('auth_token');
            localStorage.removeItem('auth_user');
          }
        }
      }

      const response = await fetch(url, {
        method: 'GET',
        headers: finalHeaders,
      });

      if (!response.ok) {
        // 尝试解析错误响应
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          // 如果无法解析JSON，使用状态码生成错误信息
          throw new Error(getHttpErrorMessage(response.status));
        }

        // 如果后端返回了具体的错误信息，使用它
        if (errorData && errorData.error) {
          throw new Error(parseApiError(errorData.error));
        }

        // 否则使用状态码映射
        throw new Error(getHttpErrorMessage(response.status));
      }

      const blob = await response.blob();

      return {
        success: true,
        data: blob,
      };

    } catch (error) {
      console.error(`API Error: GET Blob ${endpoint}`, error);

      // 使用友好的错误信息
      const friendlyError = parseApiError(error);

      return {
        success: false,
        error: friendlyError,
      };
    }
  }

  /**
   * POST请求
   */
  async post<T>(endpoint: string, body?: any, headers?: Record<string, string>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'POST', body, headers });
  }

  /**
   * PUT请求
   */
  async put<T>(endpoint: string, body?: any, headers?: Record<string, string>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'PUT', body, headers });
  }

  /**
   * DELETE请求
   */
  async delete<T>(endpoint: string, headers?: Record<string, string>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE', headers });
  }
}

// 导出API客户端实例
export const apiClient = new ApiClient();
