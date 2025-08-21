'use client';

import { createContext, useContext } from 'react';

// 定义通知类型
export type NotificationType = 'success' | 'error' | 'info' | 'warning';

// 定义单个通知的接口
export interface Notification {
  id: string;
  message: string;
  type: NotificationType;
  duration?: number; // 可选的持续时间
}

// 定义上下文类型
export interface NotificationContextType {
  addNotification: (message: string, type: NotificationType, duration?: number) => void;
}

// 创建上下文
export const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

// 创建一个自定义Hook，方便在组件中使用通知
export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification 必须在 NotificationProvider 内部使用');
  }
  return context;
};
