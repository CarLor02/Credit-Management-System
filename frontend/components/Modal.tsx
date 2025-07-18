'use client';

import { useEffect, ReactNode } from 'react';

interface ModalProps {
  isOpen: boolean;
  onCloseAction: () => void;
  children: ReactNode;
  closeOnEscape?: boolean;
  closeOnOverlayClick?: boolean;
  preventClose?: boolean;
}

export default function Modal({ 
  isOpen, 
  onCloseAction, 
  children, 
  closeOnEscape = true, 
  closeOnOverlayClick = true,
  preventClose = false
}: ModalProps) {
  useEffect(() => {
    if (!isOpen) return;

    // 保存当前滚动位置
    const scrollY = window.scrollY;
    
    // 锁定页面滚动并保持当前位置
    document.body.style.overflow = 'hidden';
    document.body.style.position = 'fixed';
    document.body.style.top = `-${scrollY}px`;
    document.body.style.width = '100%';

    // ESC键关闭
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && closeOnEscape && !preventClose) {
        onCloseAction();
      }
    };

    if (closeOnEscape) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      // 恢复页面滚动和位置
      document.body.style.overflow = '';
      document.body.style.position = '';
      document.body.style.top = '';
      document.body.style.width = '';
      window.scrollTo(0, scrollY);

      if (closeOnEscape) {
        document.removeEventListener('keydown', handleEscape);
      }
    };
  }, [isOpen, closeOnEscape, onCloseAction, preventClose]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && closeOnOverlayClick && !preventClose) {
          onCloseAction();
        }
      }}
    >
      <div 
        className="bg-white rounded-xl shadow-xl animate-fadeIn relative"
        style={{
          maxHeight: '90vh',
          maxWidth: '28rem',
          width: '100%',
          overflow: 'auto'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );
}
