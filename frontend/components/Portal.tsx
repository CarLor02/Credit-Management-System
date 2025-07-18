/**
 * Portal组件 - 用于将组件渲染到document.body
 * 确保弹窗始终在视窗中央，不受父组件影响
 */

'use client';

import { useEffect, useState, ReactNode } from 'react';
import { createPortal } from 'react-dom';

interface PortalProps {
  children: ReactNode;
  wrapperId?: string;
}

export default function Portal({ children, wrapperId = 'portal-root' }: PortalProps) {
  const [wrapperElement, setWrapperElement] = useState<HTMLElement | null>(null);

  useEffect(() => {
    // 检查是否在客户端
    if (typeof document === 'undefined') return;

    let element = document.getElementById(wrapperId);
    let systemCreated = false;

    // 如果不存在wrapper元素，创建一个
    if (!element) {
      systemCreated = true;
      element = document.createElement('div');
      element.setAttribute('id', wrapperId);
      element.style.position = 'relative';
      element.style.zIndex = '9999';
      document.body.appendChild(element);
    }

    setWrapperElement(element);

    // 清理函数
    return () => {
      // 如果是系统创建的元素且没有子节点，则移除
      if (systemCreated && element?.parentNode && element.childNodes.length === 0) {
        element.parentNode.removeChild(element);
      }
    };
  }, [wrapperId]);

  // 如果wrapper元素不存在，返回null
  if (wrapperElement === null) return null;

  // 使用Portal渲染children到wrapper元素
  return createPortal(children, wrapperElement);
}
