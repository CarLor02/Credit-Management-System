
'use client';

import { useState } from 'react';
import Link from 'next/link';
import Header from '@/components/Header';

export default function UpgradePage() {
  const [selectedPlan, setSelectedPlan] = useState('vip');
  const [billingCycle, setBillingCycle] = useState('yearly');

  const plans = [
    {
      id: 'basic',
      name: '基础版',
      price: { monthly: 99, yearly: 999 },
      originalPrice: { monthly: 149, yearly: 1499 },
      features: [
        '基础风险评估',
        '月度报告生成',
        '标准客服支持',
        '基础数据分析',
        '5个项目额度'
      ],
      popular: false,
      color: 'gray'
    },
    {
      id: 'vip',
      name: 'VIP金卡',
      price: { monthly: 299, yearly: 2999 },
      originalPrice: { monthly: 399, yearly: 3999 },
      features: [
        '高级风险评估',
        '实时数据监控',
        '专属客服支持',
        '深度数据分析',
        '无限项目额度',
        '优先处理权限',
        '专属API接口'
      ],
      popular: true,
      color: 'yellow'
    },
    {
      id: 'enterprise',
      name: '企业版',
      price: { monthly: 899, yearly: 8999 },
      originalPrice: { monthly: 1299, yearly: 12999 },
      features: [
        '企业级风险评估',
        '24/7实时监控',
        '专属客户经理',
        '定制化分析报告',
        '无限项目和用户',
        '私有化部署',
        '定制开发服务',
        '企业级安全保障'
      ],
      popular: false,
      color: 'blue'
    }
  ];

  const currentPlan = {
    name: 'VIP金卡',
    expiry: '2024-12-31',
    daysLeft: 342
  };

  const getColorClasses = (color, type) => {
    const colorMap = {
      gray: {
        border: 'border-gray-300',
        bg: 'bg-gray-50',
        text: 'text-gray-600',
        button: 'bg-gray-600 hover:bg-gray-700'
      },
      yellow: {
        border: 'border-yellow-400',
        bg: 'bg-yellow-50',
        text: 'text-yellow-600',
        button: 'bg-yellow-600 hover:bg-yellow-700'
      },
      blue: {
        border: 'border-blue-400',
        bg: 'bg-blue-50',
        text: 'text-blue-600',
        button: 'bg-blue-600 hover:bg-blue-700'
      }
    };
    return colorMap[color][type];
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* 头部 */}
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">升级会员套餐</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            选择最适合您的套餐，解锁更强大的风险管理功能
          </p>
        </div>

        {/* 当前会员状态 */}
        <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 rounded-xl p-6 text-white mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <i className="ri-vip-crown-fill text-3xl mr-4"></i>
              <div>
                <h3 className="text-xl font-bold">当前会员：{currentPlan.name}</h3>
                <p className="text-yellow-100">到期时间：{currentPlan.expiry} （还有{currentPlan.daysLeft}天）</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-yellow-100 text-sm">享受专属权益</p>
              <p className="text-lg font-semibold">优先处理 · 专属客服</p>
            </div>
          </div>
        </div>

        {/* 计费周期选择 */}
        <div className="flex justify-center mb-8">
          <div className="bg-white rounded-lg p-1 shadow-sm border border-gray-200">
            <div className="flex">
              <button
                onClick={() => setBillingCycle('monthly')}
                className={`px-6 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap ${
                  billingCycle === 'monthly'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                按月付费
              </button>
              <button
                onClick={() => setBillingCycle('yearly')}
                className={`px-6 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap relative ${
                  billingCycle === 'yearly'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                按年付费
                <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full">
                  省20%
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* 套餐卡片 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={`bg-white rounded-xl shadow-sm border-2 transition-all duration-200 hover:shadow-lg ${
                plan.popular ? 'border-yellow-400 relative' : 'border-gray-200'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-yellow-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                    推荐套餐
                  </span>
                </div>
              )}

              <div className="p-8">
                <div className="text-center mb-6">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                  <div className="flex items-center justify-center">
                    <span className="text-3xl font-bold text-gray-900">
                      ¥{plan.price[billingCycle]}
                    </span>
                    <span className="text-gray-600 ml-2">
                      /{billingCycle === 'monthly' ? '月' : '年'}
                    </span>
                  </div>
                  <div className="text-sm text-gray-500 mt-1">
                    原价 ¥{plan.originalPrice[billingCycle]}
                  </div>
                </div>

                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-center">
                      <i className="ri-check-line text-green-500 mr-3"></i>
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => setSelectedPlan(plan.id)}
                  className={`w-full py-3 rounded-lg font-medium transition-colors whitespace-nowrap ${
                    plan.id === 'vip' && currentPlan.name === 'VIP金卡'
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : `text-white ${getColorClasses(plan.color, 'button')}`
                  }`}
                  disabled={plan.id === 'vip' && currentPlan.name === 'VIP金卡'}
                >
                  {plan.id === 'vip' && currentPlan.name === 'VIP金卡' ? '当前套餐' : '立即升级'}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* 功能对比表 */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">功能对比详情</h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">功能特性</th>
                  <th className="px-6 py-3 text-center text-sm font-medium text-gray-500">基础版</th>
                  <th className="px-6 py-3 text-center text-sm font-medium text-gray-500">VIP金卡</th>
                  <th className="px-6 py-3 text-center text-sm font-medium text-gray-500">企业版</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {[
                  { feature: '项目数量', basic: '5个', vip: '无限制', enterprise: '无限制' },
                  { feature: '用户数量', basic: '1个', vip: '3个', enterprise: '无限制' },
                  { feature: '数据存储', basic: '1GB', vip: '10GB', enterprise: '无限制' },
                  { feature: 'API调用', basic: '1000次/月', vip: '10000次/月', enterprise: '无限制' },
                  { feature: '报告生成', basic: '基础报告', vip: '高级报告', enterprise: '定制报告' },
                  { feature: '客服支持', basic: '工作时间', vip: '优先支持', enterprise: '专属客户经理' },
                  { feature: '数据备份', basic: '每周', vip: '每日', enterprise: '实时备份' },
                  { feature: '安全等级', basic: '标准', vip: '高级', enterprise: '企业级' }
                ].map((row, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{row.feature}</td>
                    <td className="px-6 py-4 text-sm text-gray-600 text-center">{row.basic}</td>
                    <td className="px-6 py-4 text-sm text-gray-600 text-center">{row.vip}</td>
                    <td className="px-6 py-4 text-sm text-gray-600 text-center">{row.enterprise}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 常见问题 */}
        <div className="mt-12">
          <h3 className="text-xl font-bold text-gray-900 mb-6 text-center">常见问题</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              {
                question: '如何升级套餐？',
                answer: '选择合适的套餐后点击"立即升级"，完成支付即可立即生效。'
              },
              {
                question: '可以随时取消吗？',
                answer: '是的，您可以随时取消订阅，已付费用将按比例退还。'
              },
              {
                question: '升级后立即生效吗？',
                answer: '是的，升级后所有功能立即生效，原套餐剩余时间会折算到新套餐。'
              },
              {
                question: '支持哪些支付方式？',
                answer: '支持支付宝、微信支付、银行卡、企业转账等多种支付方式。'
              }
            ].map((faq, index) => (
              <div key={index} className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
                <h4 className="font-semibold text-gray-900 mb-2">{faq.question}</h4>
                <p className="text-gray-600 text-sm">{faq.answer}</p>
              </div>
            ))}
          </div>
        </div>

        {/* 底部联系信息 */}
        <div className="mt-12 text-center">
          <p className="text-gray-600 mb-4">需要帮助？联系我们的专业团队</p>
          <div className="flex justify-center space-x-6">
            <div className="flex items-center">
              <i className="ri-phone-line text-blue-600 mr-2"></i>
              <span className="text-gray-700">400-888-8888</span>
            </div>
            <div className="flex items-center">
              <i className="ri-mail-line text-blue-600 mr-2"></i>
              <span className="text-gray-700">support@company.com</span>
            </div>
            <div className="flex items-center">
              <i className="ri-wechat-line text-blue-600 mr-2"></i>
              <span className="text-gray-700">在线客服</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
