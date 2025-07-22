'use client';

import { useState } from 'react';
import Header from '@/components/Header';
import { useAuth } from '@/contexts/AuthContext';

export default function ProfilePage() {
  const [activeTab, setActiveTab] = useState('info');
  const [showEditModal, setShowEditModal] = useState(false);
  const [showRechargeModal, setShowRechargeModal] = useState(false);
  const { user } = useAuth();

  // 用户数据 - 使用真实用户数据，如果没有则使用默认值
  const userData = {
    username: user?.username || 'admin',
    email: user?.email || 'admin@example.com',
    phone: user?.phone || '13800138000',
    joinDate: user?.created_at ? new Date(user.created_at).toLocaleDateString() : '2023-03-15',
    avatar: user?.username?.charAt(0).toUpperCase() || 'A',
    points: 2580,
    memberLevel: 'VIP金卡',
    membershipExpiry: '2024-12-31',
    totalProjects: 45,
    completedProjects: 38,
    pendingProjects: 7
  };

  const pointsHistory = [
    { date: '2024-01-20', action: '完成项目评估', points: +150, type: 'earn' },
    { date: '2024-01-19', action: '下载征信报告', points: -50, type: 'spend' },
    { date: '2024-01-18', action: '系统奖励', points: +100, type: 'earn' },
    { date: '2024-01-17', action: '生成分析报告', points: -80, type: 'spend' },
    { date: '2024-01-16', action: '完成文档审核', points: +120, type: 'earn' },
    { date: '2024-01-15', action: '购买高级功能', points: -200, type: 'spend' }
  ];

  const memberBenefits = [
    { icon: 'ri-vip-crown-line', title: '优先处理', desc: '项目评估优先级提升' },
    { icon: 'ri-download-line', title: '无限下载', desc: '不限制报告下载次数' },
    { icon: 'ri-customer-service-line', title: '专属客服', desc: '7×24小时专属服务' },
    { icon: 'ri-shield-check-line', title: '数据保护', desc: '企业级数据安全保障' },
    { icon: 'ri-speed-up-line', title: '加速处理', desc: '征信分析速度提升50%' },
    { icon: 'ri-gift-line', title: '专属优惠', desc: '享受会员专属折扣' }
  ];

  const rechargeOptions = [
    { points: 500, price: 50, bonus: 0, popular: false },
    { points: 1000, price: 90, bonus: 100, popular: true },
    { points: 2000, price: 160, bonus: 300, popular: false },
    { points: 5000, price: 380, bonus: 1000, popular: false }
  ];

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

        {/* 会员状态和点数信息 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 rounded-xl p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <i className="ri-vip-crown-fill text-2xl mr-3"></i>
                <div>
                  <h3 className="text-lg font-bold">会员等级</h3>
                  <p className="text-yellow-100">{userData.memberLevel}</p>
                </div>
              </div>
            </div>
            <div className="text-sm text-yellow-100">
              到期时间：{userData.membershipExpiry}
            </div>
          </div>

          <div className="bg-gradient-to-r from-blue-500 to-blue-700 rounded-xl p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <i className="ri-coin-line text-2xl mr-3"></i>
                <div>
                  <h3 className="text-lg font-bold">可用点数</h3>
                  <p className="text-2xl font-bold">{userData.points.toLocaleString()}</p>
                </div>
              </div>
              <button
                onClick={() => setShowRechargeModal(true)}
                className="px-3 py-1 bg-white/20 rounded-lg hover:bg-white/30 transition-colors text-sm whitespace-nowrap"
              >
                充值
              </button>
            </div>
            <div className="text-sm text-blue-100">
              本月获得 +350 点数
            </div>
          </div>

          <div className="bg-gradient-to-r from-green-500 to-green-700 rounded-xl p-6 text-white">
            <div className="flex items-center">
              <i className="ri-trophy-line text-2xl mr-3"></i>
              <div>
                <h3 className="text-lg font-bold">项目统计</h3>
                <div className="flex items-center space-x-4 mt-2">
                  <div>
                    <p className="text-xl font-bold">{userData.totalProjects}</p>
                    <p className="text-green-100 text-sm">总项目</p>
                  </div>
                  <div>
                    <p className="text-xl font-bold">{userData.completedProjects}</p>
                    <p className="text-green-100 text-sm">已完成</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 标签页导航 */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'info', name: '基本信息', icon: 'ri-user-line' },
                { id: 'points', name: '点数记录', icon: 'ri-coin-line' },
                { id: 'membership', name: '会员权益', icon: 'ri-vip-crown-line' },
                { id: 'security', name: '安全设置', icon: 'ri-shield-line' }
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

            {activeTab === 'points' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">点数使用记录</h3>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-600">当前余额</span>
                    <span className="text-xl font-bold text-blue-600">{userData.points.toLocaleString()}</span>
                    <button
                      onClick={() => setShowRechargeModal(true)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium whitespace-nowrap"
                    >
                      <i className="ri-add-line mr-2"></i>
                      充值点数
                    </button>
                  </div>
                </div>
                
                <div className="space-y-3">
                  {pointsHistory.map((record, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          record.type === 'earn' ? 'bg-green-100' : 'bg-red-100'
                        }`}>
                          <i className={`${record.type === 'earn' ? 'ri-add-line text-green-600' : 'ri-subtract-line text-red-600'}`}></i>
                        </div>
                        <div className="ml-4">
                          <p className="font-medium text-gray-900">{record.action}</p>
                          <p className="text-sm text-gray-500">{record.date}</p>
                        </div>
                      </div>
                      <div className={`text-lg font-bold ${
                        record.type === 'earn' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {record.type === 'earn' ? '+' : ''}{record.points}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'membership' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">会员权益</h3>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">当前等级：</span>
                    <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                      {userData.memberLevel}
                    </span>
                  </div>
                </div>

                <div className="bg-gradient-to-r from-yellow-50 to-yellow-100 rounded-lg p-6 border border-yellow-200">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                      <i className="ri-vip-crown-fill text-yellow-600 text-2xl mr-3"></i>
                      <div>
                        <h4 className="text-lg font-bold text-yellow-800">VIP金卡会员</h4>
                        <p className="text-yellow-700">到期时间：{userData.membershipExpiry}</p>
                      </div>
                    </div>
                    <button className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors text-sm font-medium whitespace-nowrap">
                      <i className="ri-refresh-line mr-2"></i>
                      续费会员
                    </button>
                  </div>
                  <div className="text-sm text-yellow-700">
                    距离到期还有 <span className="font-bold">342</span> 天
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {memberBenefits.map((benefit, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center mb-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                          <i className={`${benefit.icon} text-blue-600`}></i>
                        </div>
                        <h4 className="font-semibold text-gray-900 ml-3">{benefit.title}</h4>
                      </div>
                      <p className="text-sm text-gray-600">{benefit.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'security' && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-gray-900">安全设置</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center">
                      <i className="ri-lock-line text-gray-600 mr-3"></i>
                      <div>
                        <h4 className="font-medium text-gray-900">登录密码</h4>
                        <p className="text-sm text-gray-500">上次修改：2024-01-10</p>
                      </div>
                    </div>
                    <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium whitespace-nowrap">
                      修改密码
                    </button>
                  </div>

                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center">
                      <i className="ri-phone-line text-gray-600 mr-3"></i>
                      <div>
                        <h4 className="font-medium text-gray-900">手机验证</h4>
                        <p className="text-sm text-gray-500">已绑定：{userData.phone}</p>
                      </div>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-600 text-sm mr-2">已验证</span>
                      <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium whitespace-nowrap">
                        更换手机
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center">
                      <i className="ri-mail-line text-gray-600 mr-3"></i>
                      <div>
                        <h4 className="font-medium text-gray-900">邮箱验证</h4>
                        <p className="text-sm text-gray-500">已绑定：{userData.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-600 text-sm mr-2">已验证</span>
                      <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium whitespace-nowrap">
                        更换邮箱
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center">
                      <i className="ri-shield-keyhole-line text-gray-600 mr-3"></i>
                      <div>
                        <h4 className="font-medium text-gray-900">双重验证</h4>
                        <p className="text-sm text-gray-500">提高账户安全性</p>
                      </div>
                    </div>
                    <div className="flex items-center">
                      <span className="text-red-600 text-sm mr-2">未开启</span>
                      <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium whitespace-nowrap">
                        立即开启
                      </button>
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
                  defaultValue={userData.email}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">手机号</label>
                <input
                  type="tel"
                  defaultValue={userData.phone}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => setShowEditModal(false)}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors font-medium whitespace-nowrap"
              >
                取消
              </button>
              <button
                onClick={() => setShowEditModal(false)}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium whitespace-nowrap"
              >
                保存修改
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 充值弹窗 */}
      {showRechargeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">充值点数</h3>
            <div className="grid grid-cols-2 gap-4 mb-6">
              {rechargeOptions.map((option, index) => (
                <div
                  key={index}
                  className={`border-2 rounded-lg p-4 cursor-pointer transition-colors hover:border-blue-300 ${
                    option.popular ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                  }`}
                >
                  {option.popular && (
                    <div className="text-xs bg-blue-500 text-white px-2 py-1 rounded-full inline-block mb-2">
                      推荐
                    </div>
                  )}
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900">
                      {option.points.toLocaleString()}
                      {option.bonus > 0 && (
                        <span className="text-sm text-green-600">+{option.bonus}</span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600 mb-2">点数</div>
                    <div className="text-lg font-semibold text-blue-600">¥{option.price}</div>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowRechargeModal(false)}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors font-medium whitespace-nowrap"
              >
                取消
              </button>
              <button
                onClick={() => setShowRechargeModal(false)}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium whitespace-nowrap"
              >
                立即充值
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}