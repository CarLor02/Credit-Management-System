'use client';

import { useState, useCallback, ReactNode } from 'react';
import { NotificationContext, Notification, NotificationType } from './NotificationContext';
import NotificationComponent from '@/components/Notification';
import Portal from '@/components/Portal';

interface ProviderProps {
  children: ReactNode;
}

export function NotificationProvider({ children }: ProviderProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [removingIds, setRemovingIds] = useState<Set<string>>(new Set());

  const addNotification = useCallback((message: string, type: NotificationType, duration?: number) => {
    const id = new Date().toISOString() + Math.random().toString();
    setNotifications(prev => [...prev, { id, message, type, duration }]);
  }, []);

  const removeNotification = useCallback((id: string) => {
    // 首先标记为正在移除，触发移除动画
    setRemovingIds(prev => new Set([...prev, id]));
    
    // 等待动画完成后再从列表中移除
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
      setRemovingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }, 300); // 与CSS动画时间匹配
  }, []);

  return (
    <NotificationContext.Provider value={{ addNotification }}>
      {children}
      <Portal wrapperId="notification-portal">
        <div className="fixed top-16 left-1/2 transform -translate-x-1/2 z-[10000] notification-container">
          {notifications.map(notification => (
            <div
              key={notification.id}
              className={`notification-item ${removingIds.has(notification.id) ? 'removing' : ''}`}
            >
              <NotificationComponent
                notification={notification}
                onClose={removeNotification}
              />
            </div>
          ))}
        </div>
      </Portal>
    </NotificationContext.Provider>
  );
}
