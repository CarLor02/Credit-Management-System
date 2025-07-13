
'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full text-center">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">征信管理系统</h1>
          <p className="text-xl text-gray-600 mb-8">企业与个人征信数据管理平台</p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <i className="ri-database-2-line text-blue-600 text-xl"></i>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">数据采集</h3>
              <p className="text-gray-600 text-sm">多格式文档上传与智能解析</p>
            </div>
            
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <i className="ri-file-text-line text-green-600 text-xl"></i>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">报告生成</h3>
              <p className="text-gray-600 text-sm">一键生成专业征信报告</p>
            </div>
            
            <div className="bg-white p-6 rounded-xl shadow-sm">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <i className="ri-pie-chart-line text-purple-600 text-xl"></i>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">画像分析</h3>
              <p className="text-gray-600 text-sm">智能风险评估与趋势分析</p>
            </div>
          </div>
          
          <Link href="/login">
            <button className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors text-lg font-medium whitespace-nowrap">
              立即开始
            </button>
          </Link>
        </div>
      </div>
    </div>
  );
}
