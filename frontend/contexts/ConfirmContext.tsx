'use client';

import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';

export interface ConfirmOptions {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'warning' | 'danger' | 'info';
}

interface ConfirmContextType {
  showConfirm: (options: ConfirmOptions) => Promise<boolean>;
}

const ConfirmContext = createContext<ConfirmContextType | undefined>(undefined);

export function useConfirm() {
  const context = useContext(ConfirmContext);
  if (!context) {
    throw new Error('useConfirm must be used within a ConfirmProvider');
  }
  return context;
}

interface ConfirmProviderProps {
  children: ReactNode;
}

interface ConfirmState extends ConfirmOptions {
  isOpen: boolean;
  isLoading: boolean;
  resolve?: (value: boolean) => void;
}

export function ConfirmProvider({ children }: ConfirmProviderProps) {
  const [confirmState, setConfirmState] = useState<ConfirmState>({
    isOpen: false,
    isLoading: false,
    title: '',
    message: '',
  });

  const handleCancel = () => {
    setConfirmState(prev => {
      prev.resolve?.(false);
      return { ...prev, isOpen: false, isLoading: false };
    });
  };

  const handleConfirm = () => {
    setConfirmState(prev => ({ ...prev, isLoading: true }));
    setTimeout(() => {
      setConfirmState(prev => {
        prev.resolve?.(true);
        return { ...prev, isOpen: false, isLoading: false };
      });
    }, 0);
  };

  // ESC键关闭弹窗
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && confirmState.isOpen && !confirmState.isLoading) {
        handleCancel();
      }
    };

    if (confirmState.isOpen) {
      document.addEventListener('keydown', handleEscape);
      // 防止页面滚动
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  });

  const showConfirm = (options: ConfirmOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      setConfirmState({
        ...options,
        isOpen: true,
        isLoading: false,
        resolve,
      });
    });
  };

  return (
    <ConfirmContext.Provider value={{ showConfirm }}>
      {children}
      {confirmState.isOpen && (
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
            if (e.target === e.currentTarget && !confirmState.isLoading) {
              handleCancel();
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
            <div className={`flex items-center justify-center w-12 h-12 mx-auto ${
              confirmState.type === 'danger' ? 'bg-red-100' : 
              confirmState.type === 'info' ? 'bg-blue-100' : 'bg-yellow-100'
            } rounded-full mb-4`}>
              <i className={`${
                confirmState.type === 'danger' ? 'ri-error-warning-line text-red-600' : 
                confirmState.type === 'info' ? 'ri-information-line text-blue-600' : 'ri-error-warning-line text-yellow-600'
              } text-xl`}></i>
            </div>
            
            <h3 className="text-lg font-medium text-gray-800 text-center mb-2">
              {confirmState.title}
            </h3>
            
            <div 
              className="text-gray-600 text-center mb-6"
              dangerouslySetInnerHTML={{ __html: confirmState.message }}
            />
            
            <div className="flex space-x-3">
              <button
                onClick={handleCancel}
                disabled={confirmState.isLoading}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {confirmState.cancelText || '取消'}
              </button>
              <button
                onClick={handleConfirm}
                disabled={confirmState.isLoading}
                className={`flex-1 px-4 py-2 text-white rounded-lg transition-colors whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center ${
                  confirmState.type === 'danger' ? 'bg-red-600 hover:bg-red-700' : 
                  confirmState.type === 'info' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-yellow-600 hover:bg-yellow-700'
                }`}
              >
                {confirmState.isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                    处理中...
                  </>
                ) : (
                  confirmState.confirmText || '确认'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}
