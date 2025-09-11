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
  warnings?: string[]; // 添加警告信息字段
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
          // 检查token是否过期（增加5分钟容错时间，避免服务器时间差异导致的问题）
          try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const currentTime = Date.now();
            const expiredTime = payload.exp * 1000;
            const bufferTime = 5 * 60 * 1000; // 5分钟容错时间
            const isExpired = expiredTime < (currentTime - bufferTime);

            if (!isExpired) {
              finalHeaders['Authorization'] = `Bearer ${token}`;
            } else {
              // Token过期，清除本地存储
              console.info('Token已过期，清除本地存储');
              localStorage.removeItem('auth_token');
              localStorage.removeItem('auth_user');
            }
          } catch (tokenError) {
            // Token格式错误，清除本地存储
            console.warn('Token格式错误，清除本地存储:', tokenError);
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
          return {
            success: false,
            error: getHttpErrorMessage(response.status),
          };
        }

        // 如果后端返回了具体的错误信息，直接使用它
        if (errorData && errorData.error) {
          return {
            success: false,
            error: errorData.error,
          };
        }

        // 否则使用状态码映射
        return {
          success: false,
          error: getHttpErrorMessage(response.status),
        };
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
      // 对于真正的网络错误或其他异常
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
          // 检查token是否过期（增加5分钟容错时间，避免服务器时间差异导致的问题）
          try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const currentTime = Date.now();
            const expiredTime = payload.exp * 1000;
            const bufferTime = 5 * 60 * 1000; // 5分钟容错时间
            const isExpired = expiredTime < (currentTime - bufferTime);

            if (!isExpired) {
              finalHeaders['Authorization'] = `Bearer ${token}`;
            } else {
              // Token过期，清除本地存储
              console.info('Token已过期，清除本地存储');
              localStorage.removeItem('auth_token');
              localStorage.removeItem('auth_user');
            }
          } catch (tokenError) {
            // Token格式错误，清除本地存储
            console.warn('Token格式错误，清除本地存储:', tokenError);
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
          const error = new Error(getHttpErrorMessage(response.status));
          (error as any).status = response.status;
          throw error;
        }

        // 如果后端返回了具体的错误信息，使用它
        if (errorData && errorData.error) {
          const error = new Error(parseApiError(errorData.error));
          (error as any).status = response.status;
          throw error;
        }

        // 否则使用状态码映射
        const error = new Error(getHttpErrorMessage(response.status));
        (error as any).status = response.status;
        throw error;
      }

      const blob = await response.blob();

      return {
        success: true,
        data: blob,
      };

    } catch (error) {
      // 根据状态码决定日志级别
      const status = (error as any).status;
      const isExpectedError = status === 404 || status === 401 || status === 403;

      if (isExpectedError) {
        // 对于预期的业务错误（如资源不存在、未授权等），使用info级别
        console.info(`API Info: GET Blob ${endpoint} - ${status}`, (error as Error).message);
      } else {
        // 对于真正的错误（如500、网络错误等），使用error级别
        console.error(`API Error: GET Blob ${endpoint}`, error);
      }

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
