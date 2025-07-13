'use client';

import { useState } from 'react';
import { projectService } from '@/services/projectService';
import { documentService } from '@/services/documentService';
import { USE_MOCK } from '@/config/mock';
import Header from '@/components/Header';

/**
 * Mock系统测试页面
 * 用于测试和验证Mock系统的功能
 */
export default function TestMockPage() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  const addResult = (operation: string, success: boolean, data?: any, error?: string) => {
    const result = {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString(),
      operation,
      success,
      data,
      error
    };
    setResults(prev => [result, ...prev]);
  };

  const testProjectAPI = async () => {
    setLoading(true);
    
    try {
      // 测试获取项目列表
      const listResponse = await projectService.getProjects();
      addResult('获取项目列表', listResponse.success, listResponse.data, listResponse.error);

      if (listResponse.success && listResponse.data && listResponse.data.length > 0) {
        // 测试获取单个项目
        const projectId = listResponse.data[0].id;
        const detailResponse = await projectService.getProjectById(projectId);
        addResult(`获取项目详情 (ID: ${projectId})`, detailResponse.success, detailResponse.data, detailResponse.error);
      }

      // 测试创建项目
      const createResponse = await projectService.createProject({
        name: `测试项目 ${Date.now()}`,
        type: 'enterprise',
        description: '这是一个测试项目'
      });
      addResult('创建项目', createResponse.success, createResponse.data, createResponse.error);

    } catch (error) {
      addResult('项目API测试', false, null, error instanceof Error ? error.message : '未知错误');
    } finally {
      setLoading(false);
    }
  };

  const testDocumentAPI = async () => {
    setLoading(true);
    
    try {
      // 测试获取文档列表
      const listResponse = await documentService.getDocuments();
      addResult('获取文档列表', listResponse.success, listResponse.data, listResponse.error);

      if (listResponse.success && listResponse.data && listResponse.data.length > 0) {
        // 测试获取单个文档
        const documentId = listResponse.data[0].id;
        const detailResponse = await documentService.getDocumentById(documentId);
        addResult(`获取文档详情 (ID: ${documentId})`, detailResponse.success, detailResponse.data, detailResponse.error);
      }

    } catch (error) {
      addResult('文档API测试', false, null, error instanceof Error ? error.message : '未知错误');
    } finally {
      setLoading(false);
    }
  };

  const clearResults = () => {
    setResults([]);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="p-6">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-800 mb-2">Mock系统测试</h1>
            <p className="text-gray-600">测试和验证Mock系统的功能</p>
          </div>

          {/* 当前状态 */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">当前状态</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${USE_MOCK ? 'bg-yellow-500' : 'bg-green-500'}`}></div>
                <span className="text-gray-700">
                  模式: {USE_MOCK ? 'Mock数据' : '真实API'}
                </span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                <span className="text-gray-700">
                  环境: {process.env.NODE_ENV || 'development'}
                </span>
              </div>
            </div>
          </div>

          {/* 测试按钮 */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">API测试</h2>
            <div className="flex flex-wrap gap-4">
              <button
                onClick={testProjectAPI}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? '测试中...' : '测试项目API'}
              </button>
              <button
                onClick={testDocumentAPI}
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? '测试中...' : '测试文档API'}
              </button>
              <button
                onClick={clearResults}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
              >
                清空结果
              </button>
            </div>
          </div>

          {/* 测试结果 */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">测试结果</h2>
            
            {results.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                暂无测试结果，点击上方按钮开始测试
              </div>
            ) : (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {results.map((result) => (
                  <div
                    key={result.id}
                    className={`p-4 rounded-lg border ${
                      result.success 
                        ? 'bg-green-50 border-green-200' 
                        : 'bg-red-50 border-red-200'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <div className={`w-2 h-2 rounded-full ${
                          result.success ? 'bg-green-500' : 'bg-red-500'
                        }`}></div>
                        <span className="font-medium text-gray-800">
                          {result.operation}
                        </span>
                      </div>
                      <span className="text-sm text-gray-500">
                        {result.timestamp}
                      </span>
                    </div>
                    
                    {result.error && (
                      <div className="text-red-600 text-sm mb-2">
                        错误: {result.error}
                      </div>
                    )}
                    
                    {result.data && (
                      <details className="text-sm">
                        <summary className="cursor-pointer text-gray-600 hover:text-gray-800">
                          查看数据 ({Array.isArray(result.data) ? `${result.data.length} 项` : '对象'})
                        </summary>
                        <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-x-auto">
                          {JSON.stringify(result.data, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
