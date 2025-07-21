/**
 * 路由保护组件
 * 确保只有已认证的用户才能访问受保护的页面
 */

'use client';

import { useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: 'admin' | 'manager' | 'analyst' | 'user';
  fallbackPath?: string;
}

/**
 * 路由保护组件
 */
export default function ProtectedRoute({ 
  children, 
  requiredRole,
  fallbackPath = '/login' 
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // 等待认证状态加载完成
    if (isLoading) return;

    // 如果未认证，重定向到登录页
    if (!isAuthenticated) {
      router.push(fallbackPath);
      return;
    }

    // 如果需要特定角色权限
    if (requiredRole && user) {
      const roleHierarchy = {
        'user': 1,
        'analyst': 2,
        'manager': 3,
        'admin': 4
      };

      const userLevel = roleHierarchy[user.role];
      const requiredLevel = roleHierarchy[requiredRole];

      // 权限不足，重定向到无权限页面或首页
      if (userLevel < requiredLevel) {
        router.push('/dashboard'); // 或者创建一个无权限页面
        return;
      }
    }
  }, [isAuthenticated, isLoading, user, requiredRole, router, fallbackPath]);

  // 显示加载状态
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">正在验证身份...</p>
        </div>
      </div>
    );
  }

  // 如果未认证，显示空白页面（实际会重定向）
  if (!isAuthenticated) {
    return null;
  }

  // 如果需要特定角色但权限不足，显示空白页面（实际会重定向）
  if (requiredRole && user) {
    const roleHierarchy = {
      'user': 1,
      'analyst': 2,
      'manager': 3,
      'admin': 4
    };

    const userLevel = roleHierarchy[user.role];
    const requiredLevel = roleHierarchy[requiredRole];

    if (userLevel < requiredLevel) {
      return null;
    }
  }

  // 认证通过，渲染子组件
  return <>{children}</>;
}

/**
 * 管理员路由保护组件
 */
export function AdminRoute({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute requiredRole="admin">
      {children}
    </ProtectedRoute>
  );
}

/**
 * 经理路由保护组件
 */
export function ManagerRoute({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute requiredRole="manager">
      {children}
    </ProtectedRoute>
  );
}

/**
 * 分析师路由保护组件
 */
export function AnalystRoute({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute requiredRole="analyst">
      {children}
    </ProtectedRoute>
  );
}
