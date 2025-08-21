'use client';

import React, { useEffect } from 'react';
import Portal from './Portal';

export interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'warning' | 'danger' | 'info';
  isLoading?: boolean;
  onConfirmAction: () => void;
  onCancelAction: () => void;
}

const DIALOG_CONFIG = {
  warning: {
    icon: 'ri-error-warning-line',
    iconBg: 'bg-yellow-100',
    iconColor: 'text-yellow-600',
    confirmBg: 'bg-yellow-600 hover:bg-yellow-700',
  },
  danger: {
    icon: 'ri-error-warning-line',
    iconBg: 'bg-red-100',
    iconColor: 'text-red-600',
    confirmBg: 'bg-red-600 hover:bg-red-700',
  },
  info: {
    icon: 'ri-information-line',
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    confirmBg: 'bg-blue-600 hover:bg-blue-700',
  },
};

export default function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmText = '确认',
  cancelText = '取消',
  type = 'warning',
  isLoading = false,
  onConfirmAction,
  onCancelAction,
}: ConfirmDialogProps) {
  // ESC键关闭弹窗
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isLoading) {
        onCancelAction();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      // 防止页面滚动
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, isLoading, onCancelAction]);

  if (!isOpen) return null;

  const config = DIALOG_CONFIG[type];

  return (
    <Portal>
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 z-[9999] flex items-center justify-center p-4"
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 9999
        }}
        onClick={(e) => {
          // 点击遮罩层关闭弹窗
          if (e.target === e.currentTarget && !isLoading) {
            onCancelAction();
          }
        }}
      >
        <div 
          className="bg-white rounded-xl p-6 max-w-md w-full shadow-xl animate-fadeIn"
          style={{
            maxHeight: '90vh',
            overflow: 'auto'
          }}
          onClick={(e) => e.stopPropagation()} // 防止点击弹窗内容时关闭
        >
          <div className={`flex items-center justify-center w-12 h-12 mx-auto ${config.iconBg} rounded-full mb-4`}>
            <i className={`${config.icon} ${config.iconColor} text-xl`}></i>
          </div>
          
          <h3 className="text-lg font-medium text-gray-800 text-center mb-2">
            {title}
          </h3>
          
          <div 
            className="text-gray-600 text-center mb-6"
            dangerouslySetInnerHTML={{ __html: message }}
          />
          
          <div className="flex space-x-3">
            <button
              onClick={onCancelAction}
              disabled={isLoading}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {cancelText}
            </button>
            <button
              onClick={onConfirmAction}
              disabled={isLoading}
              className={`flex-1 px-4 py-2 text-white rounded-lg transition-colors whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center ${config.confirmBg}`}
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  处理中...
                </>
              ) : (
                confirmText
              )}
            </button>
          </div>
        </div>
      </div>
    </Portal>
  );
}
