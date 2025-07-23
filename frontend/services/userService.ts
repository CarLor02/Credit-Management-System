/**
 * 用户服务
 * 处理用户相关的API调用
 */

import { apiClient } from './api';

export interface User {
  id: number;
  username: string;
  email: string;
  phone?: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

export interface UpdateUserData {
  email?: string;
  phone?: string;
  avatar_url?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

class UserService {
  /**
   * 获取用户信息
   */
  async getProfile(): Promise<ApiResponse<User>> {
    try {
      return await apiClient.request<User>('/auth/profile', {
        method: 'GET'
      });
    } catch (error) {
      console.error('获取用户信息失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取用户信息失败'
      };
    }
  }

  /**
   * 更新用户信息
   */
  async updateProfile(userData: UpdateUserData): Promise<ApiResponse<User>> {
    try {
      return await apiClient.request<User>('/auth/profile', {
        method: 'PUT',
        body: userData
      });
    } catch (error) {
      console.error('更新用户信息失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '更新用户信息失败'
      };
    }
  }

  /**
   * 修改密码
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<ApiResponse<void>> {
    try {
      return await apiClient.request<void>('/auth/change-password', {
        method: 'POST',
        body: {
          old_password: oldPassword,
          new_password: newPassword
        }
      });
    } catch (error) {
      console.error('修改密码失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '修改密码失败'
      };
    }
  }
}

// 创建并导出服务实例
export const userService = new UserService();
