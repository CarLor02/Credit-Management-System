/**
 * 认证上下文
 * 提供全局的用户认证状态管理
 */

'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { authService, User } from '../services/authService';
import { parseApiError } from '../utils/errorMessages';

// 认证上下文类型
interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (userData: { username: string; email: string; password: string; phone?: string }) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  updateUser: (userData: Partial<User>) => Promise<{ success: boolean; error?: string }>;
  refreshUser: () => Promise<void>;
}

// 创建认证上下文
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// 认证提供者组件属性
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * 认证提供者组件
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 计算认证状态
  const isAuthenticated = !!user && authService.isLoggedIn();

  /**
   * 初始化用户状态
   */
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // 检查本地存储的用户信息
        const storedUser = authService.getCurrentUser();

        if (storedUser && authService.isLoggedIn()) {
          setUser(storedUser);
        } else {
          // 没有有效的认证信息
          setUser(null);
        }
      } catch (error) {
        console.error('初始化认证状态失败:', error);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  /**
   * 用户登录
   */
  const login = async (username: string, password: string) => {
    try {
      setIsLoading(true);
      const response = await authService.login({ username, password });
      
      if (response.success && response.data) {
        const { user: userData } = response.data;
        setUser(userData);
        return { success: true };
      } else {
        return {
          success: false,
          error: response.error || '登录失败'
        };
      }
    } catch (error) {
      console.error('登录失败:', error);
      return {
        success: false,
        error: parseApiError(error)
      };
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 用户注册
   */
  const register = async (userData: { username: string; email: string; password: string; phone?: string }) => {
    try {
      setIsLoading(true);
      const response = await authService.register(userData);
      
      if (response.success && response.data) {
        const { user: newUser } = response.data;
        setUser(newUser);
        return { success: true };
      } else {
        return {
          success: false,
          error: response.error || '注册失败'
        };
      }
    } catch (error) {
      console.error('注册失败:', error);
      return {
        success: false,
        error: parseApiError(error)
      };
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 用户登出
   */
  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('登出失败:', error);
    } finally {
      // 无论是否成功，都清除本地状态
      setUser(null);
    }
  };

  /**
   * 更新用户信息
   */
  const updateUser = async (userData: Partial<User>) => {
    try {
      const response = await authService.updateProfile(userData);
      
      if (response.success && response.data) {
        setUser(response.data);
        return { success: true };
      } else {
        return { 
          success: false, 
          error: response.error || '更新失败' 
        };
      }
    } catch (error) {
      console.error('更新用户信息失败:', error);
      return {
        success: false,
        error: parseApiError(error)
      };
    }
  };

  /**
   * 刷新用户信息
   */
  const refreshUser = async () => {
    try {
      const userData = authService.getCurrentUser();
      if (userData) {
        setUser(userData);
      }
    } catch (error) {
      console.error('刷新用户信息失败:', error);
    }
  };

  // 上下文值
  const contextValue: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    updateUser,
    refreshUser
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * 使用认证上下文的Hook
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
}

/**
 * 权限检查Hook
 */
export function usePermission(requiredRole: 'admin' | 'user') {
  const { user } = useAuth();

  const roleHierarchy = {
    'user': 1,
    'admin': 2
  };

  const hasPermission = user && roleHierarchy[user.role] >= roleHierarchy[requiredRole];

  return hasPermission;
}
