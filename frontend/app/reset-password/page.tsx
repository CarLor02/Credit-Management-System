'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useNotification } from '@/contexts/NotificationContext';

export default function ResetPasswordPage() {
  const [step, setStep] = useState<'email' | 'code' | 'password'>('email');
  const [formData, setFormData] = useState({
    email: '',
    code: '',
    newPassword: '',
    confirmPassword: ''
  });
  const { addNotification } = useNotification();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (step === 'email') {
      // 发送重置邮件
      console.log('发送重置邮件到:', formData.email);
      setStep('code');
    } else if (step === 'code') {
      // 验证验证码
      console.log('验证验证码:', formData.code);
      setStep('password');
    } else if (step === 'password') {
      // 重置密码
      console.log('重置密码:', formData.newPassword);
      // 重置成功后跳转到登录页面
      addNotification('密码重置成功，请重新登录', 'success');
      setTimeout(() => {
        window.location.href = '/login';
      }, 2000); // 延迟2秒跳转
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const renderStepContent = () => {
    switch (step) {
      case 'email':
        return (
          <>
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-2">重置密码</h2>
              <p className="text-gray-600">请输入您的邮箱地址，我们将发送重置密码的链接</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  邮箱地址
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="请输入您的邮箱地址"
                  required
                />
              </div>

              <div className="mt-6">
                <button
                  type="submit"
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  发送重置邮件
                </button>
              </div>
            </div>
          </>
        );

      case 'code':
        return (
          <>
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-2">验证邮箱</h2>
              <p className="text-gray-600">
                我们已向 <strong>{formData.email}</strong> 发送了验证码
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  验证码
                </label>
                <input
                  type="text"
                  name="code"
                  value={formData.code}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="请输入6位验证码"
                  maxLength={6}
                  required
                />
              </div>

              <div className="mt-6">
                <button
                  type="submit"
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  验证并继续
                </button>
              </div>

              <div className="text-center">
                <button
                  type="button"
                  onClick={() => setStep('email')}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  重新发送验证码
                </button>
              </div>
            </div>
          </>
        );

      case 'password':
        return (
          <>
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-2">设置新密码</h2>
              <p className="text-gray-600">请输入您的新密码</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  新密码
                </label>
                <input
                  type="password"
                  name="newPassword"
                  value={formData.newPassword}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="请输入新密码"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  确认新密码
                </label>
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="请确认新密码"
                  required
                />
              </div>

              <div className="mt-6">
                <button
                  type="submit"
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  重置密码
                </button>
              </div>
            </div>
          </>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full animate-fadeIn">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-6">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">征信管理系统</h1>
            <p className="text-gray-600">企业与个人征信数据管理平台</p>
          </div>

          <form onSubmit={handleSubmit}>
            {renderStepContent()}
          </form>

          <div className="mt-6 text-center">
            <Link href="/login" className="text-blue-600 hover:text-blue-800 text-sm">
              返回登录
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
