
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '../../contexts/AuthContext';

export default function LoginPage() {
  const [loginType, setLoginType] = useState('login');
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    phone: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const { login, register, isAuthenticated } = useAuth();
  const router = useRouter();

  // 如果已经登录，重定向到仪表板
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (loginType === 'login') {
        // 登录逻辑
        if (!formData.username || !formData.password) {
          setError('请输入用户名和密码');
          return;
        }

        const result = await login(formData.username, formData.password);
        if (result.success) {
          router.push('/dashboard');
        } else {
          setError(result.error || '登录失败');
        }
      } else {
        // 注册逻辑
        if (!formData.username || !formData.email || !formData.password || !formData.full_name) {
          setError('请填写所有必填字段');
          return;
        }

        if (formData.password !== formData.confirmPassword) {
          setError('两次输入的密码不一致');
          return;
        }

        if (formData.password.length < 6) {
          setError('密码长度至少6位');
          return;
        }

        const result = await register({
          username: formData.username,
          email: formData.email,
          password: formData.password,
          full_name: formData.full_name
        });

        if (result.success) {
          router.push('/dashboard');
        } else {
          setError(result.error || '注册失败');
        }
      }
    } catch (error) {
      setError('网络错误，请稍后重试');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    // 清除错误信息
    if (error) setError('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full animate-fadeIn">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">征信管理系统</h1>
            <p className="text-gray-600">企业与个人征信数据管理平台</p>
          </div>

          <div className="flex mb-6">
            <button
              onClick={() => setLoginType('login')}
              className={`flex-1 py-2 px-4 rounded-l-lg font-medium transition-colors ${
                loginType === 'login'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              登录
            </button>
            <button
              onClick={() => setLoginType('register')}
              className={`flex-1 py-2 px-4 rounded-r-lg font-medium transition-colors ${
                loginType === 'register'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              注册
            </button>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {loginType === 'register' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  姓名 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="请输入您的姓名"
                  required
                />
              </div>
            )}

            {loginType === 'register' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  用户名 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="请输入用户名"
                  required
                />
              </div>
            )}

            {loginType === 'login' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  用户名 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="请输入用户名"
                  required
                />
              </div>
            )}

            {loginType === 'register' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  邮箱 <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="请输入您的邮箱"
                  required
                />
              </div>
            )}

            {loginType === 'register' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  手机号
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="请输入您的手机号"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                密码 <span className="text-red-500">*</span>
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={loginType === 'register' ? '请输入密码（至少6位）' : '请输入密码'}
                required
                minLength={loginType === 'register' ? 6 : undefined}
              />
            </div>

            {loginType === 'register' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  确认密码 <span className="text-red-500">*</span>
                </label>
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="请确认密码"
                  required
                />
              </div>
            )}

            <div className="mt-6">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    {loginType === 'login' ? '登录中...' : '注册中...'}
                  </>
                ) : (
                  loginType === 'login' ? '登录' : '注册'
                )}
              </button>
            </div>
          </form>

          {loginType === 'login' && (
            <div className="mt-4 text-center">
              <Link href="/reset-password" className="text-blue-600 hover:text-blue-800 text-sm">
                忘记密码？
              </Link>
            </div>
          )}

          <div className="mt-6 text-center text-sm text-gray-600">
            <p>
              {loginType === 'login' ? '还没有账号？' : '已有账号？'}
              <button
                onClick={() => setLoginType(loginType === 'login' ? 'register' : 'login')}
                className="text-blue-600 hover:text-blue-800 ml-1"
              >
                {loginType === 'login' ? '立即注册' : '立即登录'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
