/**
 * API服务层
 * 统一处理API调用和Mock数据切换
 */

import { MOCK_CONFIG, API_BASE_URL, mockLog, mockDelay, shouldSimulateError } from '@/config/mock';

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
      // 如果启用mock，直接返回mock数据
      if (MOCK_CONFIG.enabled) {
        mockLog(`Mock API call: ${method} ${endpoint}`, body);
        
        // 模拟网络延迟
        await mockDelay();
        
        // 模拟随机错误
        if (shouldSimulateError()) {
          throw new Error('Mock API Error: Simulated network error');
        }
        
        // 这里会被具体的服务类重写
        return {
          success: false,
          error: 'Mock implementation not found'
        };
      }

      // 真实API调用
      const url = `${this.baseUrl}${endpoint}`;
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
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
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
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
