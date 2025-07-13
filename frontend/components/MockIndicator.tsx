'use client';

import { USE_MOCK } from '@/config/mock';

/**
 * Mock状态指示器组件
 * 显示当前是否在使用Mock数据
 */
export default function MockIndicator() {
  if (!USE_MOCK) {
    return null; // 使用真实API时不显示指示器
  }

  return (
    <div className="fixed top-4 right-4 z-50">
      <div className="bg-yellow-100 border border-yellow-300 rounded-lg px-3 py-2 shadow-sm">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
          <span className="text-yellow-800 text-sm font-medium">Mock模式</span>
          <div className="text-yellow-600 text-xs">
            使用模拟数据
          </div>
        </div>
      </div>
    </div>
  );
}
