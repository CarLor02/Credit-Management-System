'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '../contexts/AuthContext';

export default function Header() {
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout } = useAuth();

  // 检查导航项是否处于激活状态
  const isActiveNav = (path: string) => {
    return pathname.startsWith(path);
  };

  const handleProfileClick = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsProfileOpen(false);
    router.push('/profile');
  };



  const handleLogout = async (e: React.MouseEvent) => {
    e.preventDefault();
    setIsProfileOpen(false);
    await logout();
    router.push('/login');
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <Link href="/projects" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <i className="ri-building-line text-white text-lg"></i>
              </div>
              <span className="text-xl font-bold text-gray-800">征信管理系统</span>
            </Link>
            
            <nav className="flex space-x-8">
              <Link
                href="/projects"
                className={`transition-colors ${isActiveNav('/projects') ? 'text-blue-600 font-medium' : 'text-gray-600 hover:text-blue-600'}`}
              >
                项目管理
              </Link>
              <Link
                href="/documents"
                className={`transition-colors ${isActiveNav('/documents') ? 'text-blue-600 font-medium' : 'text-gray-600 hover:text-blue-600'}`}
              >
                文档中心
              </Link>
            </nav>
          </div>

          <div className="flex items-center space-x-4">
            <div className="relative">
              <button
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  {user?.avatar_url ? (
                    <Image
                      src={user.avatar_url}
                      alt={user.username}
                      width={32}
                      height={32}
                      className="w-8 h-8 rounded-full object-cover"
                    />
                  ) : (
                    <span className="text-white text-sm font-medium">
                      {user?.username?.charAt(0) || 'U'}
                    </span>
                  )}
                </div>
                <span className="text-gray-700 font-medium">
                  {user?.username || '用户'}
                </span>
                <i className="ri-arrow-down-s-line text-gray-400"></i>
              </button>
              
              {isProfileOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
                  <button 
                    onClick={handleProfileClick}
                    className="block w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-50"
                  >
                    个人资料
                  </button>

                  <hr className="my-2" />
                  <button
                    onClick={handleLogout}
                    className="block w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-50"
                  >
                    退出登录
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
