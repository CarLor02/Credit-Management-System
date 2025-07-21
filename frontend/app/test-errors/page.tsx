'use client';

import { useState } from 'react';
import { authService } from '../../services/authService';
import { parseApiError, getHttpErrorMessage, getErrorMessage } from '../../utils/errorMessages';

export default function TestErrorsPage() {
  const [results, setResults] = useState<string[]>([]);

  const addResult = (message: string) => {
    setResults(prev => [...prev, message]);
  };

  const testLoginError = async () => {
    addResult('测试登录错误...');
    try {
      const response = await authService.login({ username: 'wronguser', password: 'wrongpass' });
      if (!response.success) {
        addResult(`✅ 登录错误: ${response.error}`);
      }
    } catch (error) {
      addResult(`❌ 登录测试失败: ${error}`);
    }
  };

  const testRegisterError = async () => {
    addResult('测试注册错误...');
    try {
      const response = await authService.register({
        username: 'admin', // 已存在的用户名
        email: 'test@example.com',
        password: 'test123',
        full_name: '测试用户'
      });
      if (!response.success) {
        addResult(`✅ 注册错误: ${response.error}`);
      }
    } catch (error) {
      addResult(`❌ 注册测试失败: ${error}`);
    }
  };

  const testHttpErrorMessages = () => {
    addResult('测试HTTP错误信息映射...');
    addResult(`✅ 400错误: ${getHttpErrorMessage(400)}`);
    addResult(`✅ 401错误: ${getHttpErrorMessage(401)}`);
    addResult(`✅ 403错误: ${getHttpErrorMessage(403)}`);
    addResult(`✅ 404错误: ${getHttpErrorMessage(404)}`);
    addResult(`✅ 500错误: ${getHttpErrorMessage(500)}`);
  };

  const testAuthErrorMessages = () => {
    addResult('测试认证错误信息映射...');
    addResult(`✅ 无效凭据: ${getErrorMessage('invalid_credentials')}`);
    addResult(`✅ 用户名已存在: ${getErrorMessage('username_exists')}`);
    addResult(`✅ 邮箱已存在: ${getErrorMessage('email_exists')}`);
    addResult(`✅ Token过期: ${getErrorMessage('token_expired')}`);
    addResult(`✅ 权限不足: ${getErrorMessage('permission_denied')}`);
  };

  const testNetworkError = () => {
    addResult('测试网络错误解析...');
    const networkError = new Error('fetch failed');
    networkError.name = 'NetworkError';
    addResult(`✅ 网络错误: ${parseApiError(networkError)}`);
    
    const timeoutError = new Error('timeout');
    timeoutError.name = 'TimeoutError';
    addResult(`✅ 超时错误: ${parseApiError(timeoutError)}`);
  };

  const clearResults = () => {
    setResults([]);
  };

  const runAllTests = async () => {
    clearResults();
    addResult('开始运行所有错误处理测试...');
    addResult('---');
    
    testHttpErrorMessages();
    addResult('---');
    
    testAuthErrorMessages();
    addResult('---');
    
    testNetworkError();
    addResult('---');
    
    await testLoginError();
    addResult('---');
    
    await testRegisterError();
    addResult('---');
    
    addResult('所有测试完成！');
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">错误处理测试页面</h1>
        
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">测试控制</h2>
          <div className="flex flex-wrap gap-4">
            <button
              onClick={runAllTests}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              运行所有测试
            </button>
            <button
              onClick={testLoginError}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
            >
              测试登录错误
            </button>
            <button
              onClick={testRegisterError}
              className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors"
            >
              测试注册错误
            </button>
            <button
              onClick={testHttpErrorMessages}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
            >
              测试HTTP错误
            </button>
            <button
              onClick={testAuthErrorMessages}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
            >
              测试认证错误
            </button>
            <button
              onClick={testNetworkError}
              className="bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 transition-colors"
            >
              测试网络错误
            </button>
            <button
              onClick={clearResults}
              className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
            >
              清除结果
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">测试结果</h2>
          <div className="bg-gray-100 rounded-lg p-4 max-h-96 overflow-y-auto">
            {results.length === 0 ? (
              <p className="text-gray-500">点击上方按钮开始测试...</p>
            ) : (
              <div className="space-y-2">
                {results.map((result, index) => (
                  <div key={index} className="text-sm font-mono">
                    {result}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="mt-6 text-center">
          <a
            href="/login"
            className="text-blue-600 hover:text-blue-800 underline"
          >
            返回登录页面
          </a>
        </div>
      </div>
    </div>
  );
}
