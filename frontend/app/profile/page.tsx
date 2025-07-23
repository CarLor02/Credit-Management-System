'use client';

import { useState, useEffect } from 'react';
import Header from '@/components/Header';
import { useAuth } from '@/contexts/AuthContext';
import { userService, UpdateUserData } from '@/services/userService';

export default function ProfilePage() {
  const [activeTab, setActiveTab] = useState('info');
  const [showEditModal, setShowEditModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    phone: ''
  });

  const { user, updateUser } = useAuth();

  // 用户数据 - 使用真实用户数据，如果没有则使用默认值
  const userData = {
    username: user?.username || 'admin',
    email: user?.email || 'admin@example.com',
    phone: user?.phone || '13800138000',
    joinDate: user?.created_at ? new Date(user.created_at).toLocaleDateString() : '2023-03-15',
    avatar: user?.username?.charAt(0).toUpperCase() || 'A',
  };

  // 初始化表单数据
  useEffect(() => {
    if (user) {
      setFormData({
        email: user.email || '',
        phone: user.phone || ''
      });
    }
  }, [user]);

  // 处理表单输入变化
  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // 表单验证
  const validateForm = () => {
    if (!formData.email.trim()) {
      alert('邮箱不能为空');
      return false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      alert('请输入有效的邮箱地址');
      return false;
    }

    if (formData.phone && formData.phone.trim()) {
      const phoneRegex = /^1[3-9]\d{9}$/;
      if (!phoneRegex.test(formData.phone)) {
        alert('请输入有效的手机号码');
        return false;
      }
    }

    return true;
  };

  // 处理保存修改
  const handleSaveProfile = async () => {
    if (!user) return;

    // 表单验证
    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);

      // 准备更新数据
      const updateData: UpdateUserData = {};

      if (formData.email !== user.email) {
        updateData.email = formData.email;
      }

      if (formData.phone !== user.phone) {
        updateData.phone = formData.phone;
      }

      // 如果没有变化，直接关闭弹窗
      if (Object.keys(updateData).length === 0) {
        alert('没有检测到任何修改');
        setShowEditModal(false);
        return;
      }

      // 调用API更新用户信息
      const response = await userService.updateProfile(updateData);

      if (response.success && response.data) {
        // 更新AuthContext中的用户信息
        if (updateUser) {
          await updateUser(response.data);
        }

        alert(response.message || '个人信息更新成功！');
        setShowEditModal(false);
      } else {
        alert(response.error || '更新失败，请稍后重试');
      }
    } catch (error) {
      console.error('更新用户信息失败:', error);
      alert('更新失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };



  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="max-w-6xl mx-auto px-6 py-8 animate-fadeIn">
        {/* 头部信息卡片 */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-8">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-6">
              <div className="w-20 h-20 bg-blue-600 rounded-full flex items-center justify-center">
                <span className="text-2xl font-bold text-white">{userData.avatar}</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 mb-2">{userData.username}</h1>
                <div className="space-y-1 text-sm text-gray-600">
                  <p>{userData.email}</p>
                  <p>{userData.phone}</p>
                  <p>加入时间：{userData.joinDate}</p>
                </div>
              </div>
            </div>
            <button
              onClick={() => setShowEditModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium whitespace-nowrap"
            >
              <i className="ri-edit-line mr-2"></i>
              编辑资料
            </button>
          </div>
        </div>



        {/* 标签页导航 */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'info', name: '基本信息', icon: 'ri-user-line' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <i className={`${tab.icon} mr-2`}></i>
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'info' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-gray-900">基本信息</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">用户名</label>
                      <div className="px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-600">
                        {userData.username}
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">邮箱</label>
                      <div className="px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-600">
                        {userData.email}
                      </div>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">手机号</label>
                      <div className="px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-600">
                        {userData.phone}
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">加入时间</label>
                      <div className="px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-600">
                        {userData.joinDate}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}






          </div>
        </div>
      </div>

      {/* 编辑资料弹窗 */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">编辑个人资料</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">用户名</label>
                <input
                  type="text"
                  defaultValue={userData.username}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  disabled
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">邮箱</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  placeholder="请输入邮箱地址"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">手机号</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  placeholder="请输入手机号码"
                />
              </div>
            </div>
            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => setShowEditModal(false)}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors font-medium whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
              >
                取消
              </button>
              <button
                onClick={handleSaveProfile}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <i className="ri-loader-4-line animate-spin mr-2"></i>
                    保存中...
                  </>
                ) : (
                  '保存修改'
                )}
              </button>
            </div>
          </div>
        </div>
      )}


    </div>
  );
}