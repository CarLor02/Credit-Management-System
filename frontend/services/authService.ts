/**
 * 认证服务
 * 处理用户登录、注册、token管理等认证相关功能
 */

import { apiClient } from './api';
import { MOCK_CONFIG, mockDelay, mockLog } from '../config/mock';
import { parseApiError, getErrorMessage } from '../utils/errorMessages';

// 用户角色类型
export type UserRole = 'admin' | 'user';

// 用户信息接口
export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
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
  full_name: string;
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
 * Token管理工具类
 */
export class TokenManager {
  private static readonly TOKEN_KEY = 'auth_token';
  private static readonly USER_KEY = 'auth_user';

  /**
   * 保存token
   */
  static setToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(this.TOKEN_KEY, token);
    }
  }

  /**
   * 获取token
   */
  static getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(this.TOKEN_KEY);
    }
    return null;
  }

  /**
   * 删除token
   */
  static removeToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(this.TOKEN_KEY);
      localStorage.removeItem(this.USER_KEY);
    }
  }

  /**
   * 保存用户信息
   */
  static setUser(user: User): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    }
  }

  /**
   * 获取用户信息
   */
  static getUser(): User | null {
    if (typeof window !== 'undefined') {
      const userStr = localStorage.getItem(this.USER_KEY);
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
   * 检查token是否过期
   */
  static isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp * 1000 < Date.now();
    } catch {
      return true;
    }
  }

  /**
   * 检查当前token是否有效
   */
  static isTokenValid(): boolean {
    const token = this.getToken();
    if (!token) return false;
    return !this.isTokenExpired(token);
  }
}

/**
 * 认证服务类
 */
class AuthService {
  /**
   * 用户登录
   */
  async login(credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    if (MOCK_CONFIG.enabled) {
      mockLog('User login attempt', credentials);
      await mockDelay();

      // Mock登录逻辑
      if (credentials.username === 'admin' && credentials.password === 'admin123') {
        const mockUser: User = {
          id: 1,
          username: 'admin',
          email: 'admin@example.com',
          full_name: '系统管理员',
          role: 'admin',
          avatar_url: '',
          is_active: true,
          last_login: new Date().toISOString(),
          created_at: '2024-01-01T00:00:00Z',
          updated_at: new Date().toISOString()
        };

        const mockToken = 'mock-jwt-token-' + Date.now();
        
        return {
          success: true,
          data: {
            token: mockToken,
            user: mockUser
          },
          message: '登录成功'
        };
      } else {
        return {
          success: false,
          error: getErrorMessage('invalid_credentials')
        };
      }
    }

    // 真实API调用
    const response = await apiClient.post<LoginResponse>('/auth/login', credentials);

    // 如果API调用失败，确保错误信息是用户友好的
    if (!response.success && response.error) {
      return {
        ...response,
        error: parseApiError(response.error)
      };
    }

    return response;
  }

  /**
   * 用户注册
   */
  async register(userData: RegisterRequest): Promise<ApiResponse<LoginResponse>> {
    if (MOCK_CONFIG.enabled) {
      mockLog('User registration attempt', userData);
      await mockDelay();

      // Mock注册逻辑
      const mockUser: User = {
        id: Date.now(),
        username: userData.username,
        email: userData.email,
        full_name: userData.full_name,
        role: 'user',
        avatar_url: '',
        is_active: true,
        last_login: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      const mockToken = 'mock-jwt-token-' + Date.now();
      
      return {
        success: true,
        data: {
          token: mockToken,
          user: mockUser
        },
        message: '注册成功'
      };
    }

    // 真实API调用
    const response = await apiClient.post<LoginResponse>('/auth/register', userData);

    // 如果API调用失败，确保错误信息是用户友好的
    if (!response.success && response.error) {
      return {
        ...response,
        error: parseApiError(response.error)
      };
    }

    return response;
  }

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<ApiResponse<User>> {
    if (MOCK_CONFIG.enabled) {
      mockLog('Getting current user');
      await mockDelay();

      const user = TokenManager.getUser();
      if (user) {
        return {
          success: true,
          data: user
        };
      } else {
        return {
          success: false,
          error: getErrorMessage('missing_token')
        };
      }
    }

    // 真实API调用
    const token = TokenManager.getToken();
    if (!token || TokenManager.isTokenExpired(token)) {
      return {
        success: false,
        error: getErrorMessage('token_expired')
      };
    }

    const response = await apiClient.get<User>('/auth/profile', {
      'Authorization': `Bearer ${token}`
    });

    // 如果API调用失败，确保错误信息是用户友好的
    if (!response.success && response.error) {
      return {
        ...response,
        error: parseApiError(response.error)
      };
    }

    return response;
  }

  /**
   * 用户登出
   */
  async logout(): Promise<void> {
    if (MOCK_CONFIG.enabled) {
      mockLog('User logout');
      await mockDelay();
    }

    // 清除本地存储的认证信息
    TokenManager.removeToken();
  }

  /**
   * 修改密码
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<ApiResponse<void>> {
    if (MOCK_CONFIG.enabled) {
      mockLog('Change password attempt');
      await mockDelay();

      return {
        success: true,
        message: '密码修改成功'
      };
    }

    // 真实API调用
    const token = TokenManager.getToken();
    if (!token || TokenManager.isTokenExpired(token)) {
      return {
        success: false,
        error: getErrorMessage('token_expired')
      };
    }

    const response = await apiClient.post<void>('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    }, {
      'Authorization': `Bearer ${token}`
    });

    // 如果API调用失败，确保错误信息是用户友好的
    if (!response.success && response.error) {
      return {
        ...response,
        error: parseApiError(response.error)
      };
    }

    return response;
  }

  /**
   * 更新用户信息
   */
  async updateProfile(userData: Partial<User>): Promise<ApiResponse<User>> {
    if (MOCK_CONFIG.enabled) {
      mockLog('Update profile attempt', userData);
      await mockDelay();

      const currentUser = TokenManager.getUser();
      if (currentUser) {
        const updatedUser = { ...currentUser, ...userData };
        TokenManager.setUser(updatedUser);

        return {
          success: true,
          data: updatedUser,
          message: '个人信息更新成功'
        };
      } else {
        return {
          success: false,
          error: getErrorMessage('missing_token')
        };
      }
    }

    // 真实API调用
    const token = TokenManager.getToken();
    if (!token || TokenManager.isTokenExpired(token)) {
      return {
        success: false,
        error: getErrorMessage('token_expired')
      };
    }

    const response = await apiClient.put<User>('/auth/profile', userData, {
      'Authorization': `Bearer ${token}`
    });

    // 如果API调用失败，确保错误信息是用户友好的
    if (!response.success && response.error) {
      return {
        ...response,
        error: parseApiError(response.error)
      };
    }

    return response;
  }

  /**
   * 检查用户是否已登录
   */
  isAuthenticated(): boolean {
    return TokenManager.isTokenValid();
  }

  /**
   * 获取当前用户（同步方法）
   */
  getCurrentUserSync(): User | null {
    return TokenManager.getUser();
  }
}

// 导出认证服务实例
export const authService = new AuthService();
