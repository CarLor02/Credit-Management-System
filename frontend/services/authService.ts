/**
 * 认证服务
 * 处理用户登录、注册、token管理等认证相关功能
 */

import { apiClient } from './api';

// 用户角色类型
export type UserRole = 'admin' | 'user';

// 用户信息接口
export interface User {
  id: number;
  username: string;
  email: string;
  phone?: string;
  role: UserRole;
  avatar_url?: string;
  is_active: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

// 登录请求接口
export interface LoginRequest {
  username: string;
  password: string;
}

// 注册请求接口
export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  phone?: string;
}

// 登录响应接口
export interface LoginResponse {
  token: string;
  user: User;
}

// API响应接口
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

/**
 * 认证服务类
 */
class AuthService {
  private static readonly TOKEN_KEY = 'auth_token';
  private static readonly USER_KEY = 'auth_user';

  /**
   * 用户登录
   */
  async login(credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    try {
      const response = await apiClient.request<LoginResponse>('/auth/login', {
        method: 'POST',
        body: credentials
      });

      if (response.success && response.data) {
        // 保存token和用户信息
        localStorage.setItem(AuthService.TOKEN_KEY, response.data.token);
        localStorage.setItem(AuthService.USER_KEY, JSON.stringify(response.data.user));
      }

      return response;
    } catch (error) {
      console.error('登录失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '登录失败'
      };
    }
  }

  /**
   * 用户注册
   */
  async register(userData: RegisterRequest): Promise<ApiResponse<LoginResponse>> {
    try {
      const response = await apiClient.request<LoginResponse>('/auth/register', {
        method: 'POST',
        body: userData
      });

      if (response.success && response.data) {
        // 注册成功后自动登录
        localStorage.setItem(AuthService.TOKEN_KEY, response.data.token);
        localStorage.setItem(AuthService.USER_KEY, JSON.stringify(response.data.user));
      }

      return response;
    } catch (error) {
      console.error('注册失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '注册失败'
      };
    }
  }

  /**
   * 用户登出
   */
  async logout(): Promise<void> {
    // 对于登出操作，我们优先保证本地状态清理
    // 后端登出调用是可选的，失败不应该影响用户体验

    try {
      const token = localStorage.getItem(AuthService.TOKEN_KEY);

      // 先清除本地存储，确保用户能够立即登出
      if (typeof window !== 'undefined') {
        localStorage.removeItem(AuthService.TOKEN_KEY);
        localStorage.removeItem(AuthService.USER_KEY);
      }

      // 如果有token，尝试通知后端（但不等待结果）
      if (token) {
        try {
          // 检查token格式是否有效
          const payload = JSON.parse(atob(token.split('.')[1]));
          const isExpired = payload.exp * 1000 < Date.now();

          if (!isExpired) {
            // 异步调用后端登出，不等待结果，使用原始fetch避免apiClient的额外处理
            fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5001/api'}/auth/logout`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              }
            }).catch(error => {
              // 静默处理错误，不影响用户体验
              console.debug('后端登出调用失败（已忽略）:', error.message);
            });
          }
        } catch (tokenError) {
          // Token格式错误，跳过后端调用
          console.debug('Token格式无效，跳过后端登出调用');
        }
      }
    } catch (error) {
      // 即使出现任何错误，也要确保本地存储被清除
      console.warn('登出过程中出现错误，但本地状态已清理:', error);
      if (typeof window !== 'undefined') {
        localStorage.removeItem(AuthService.TOKEN_KEY);
        localStorage.removeItem(AuthService.USER_KEY);
      }
    }
  }

  /**
   * 获取当前用户信息
   */
  getCurrentUser(): User | null {
    if (typeof window !== 'undefined') {
      const userStr = localStorage.getItem(AuthService.USER_KEY);
      if (userStr) {
        try {
          return JSON.parse(userStr);
        } catch {
          return null;
        }
      }
    }
    return null;
  }

  /**
   * 检查用户是否已登录
   */
  isLoggedIn(): boolean {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem(AuthService.TOKEN_KEY);
      return token !== null;
    }
    return false;
  }

  /**
   * 更新用户资料
   */
  async updateProfile(userData: Partial<User>): Promise<ApiResponse<User>> {
    try {
      const response = await apiClient.request<User>('/auth/profile', {
        method: 'PUT',
        body: userData
      });

      if (response.success && response.data) {
        // 更新本地存储的用户信息
        localStorage.setItem(AuthService.USER_KEY, JSON.stringify(response.data));
      }

      return response;
    } catch (error) {
      console.error('更新用户资料失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '更新用户资料失败'
      };
    }
  }
}

// 创建并导出服务实例
export const authService = new AuthService();

// 导出便捷函数
export const login = (credentials: LoginRequest) => authService.login(credentials);
export const register = (userData: RegisterRequest) => authService.register(userData);
export const logout = () => authService.logout();
export const getCurrentUser = () => authService.getCurrentUser();
export const isLoggedIn = () => authService.isLoggedIn();