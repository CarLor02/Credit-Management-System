
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // 检查用户是否已登录
    const token = localStorage.getItem('auth_token');
    if (token) {
      // 已登录，重定向到项目管理页面
      router.push('/projects');
    } else {
      // 未登录，重定向到登录页
      router.push('/login');
    }
  }, [router]);

  // 显示加载状态
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">正在跳转...</p>
      </div>
    </div>
  );
}
