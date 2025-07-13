
'use client';

import { useState, useEffect } from 'react';
import Header from '@/components/Header';
import StatsCard from './StatsCard';
import RecentActivity from './RecentActivity';
import RiskTrends from './RiskTrends';
import { statsService, StatCard, DashboardStats } from '@/services/statsService';

export default function DashboardPage() {
  const [stats, setStats] = useState<StatCard[]>([]);
  const [dashboardData, setDashboardData] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await statsService.getDashboardStats();

      if (response.success && response.data) {
        setDashboardData(response.data);
        const statCards = statsService.transformToStatCards(response.data);
        setStats(statCards);
      } else {
        setError(response.error || '加载统计数据失败');
      }
    } catch (err) {
      setError('网络错误，请稍后重试');
      console.error('Load dashboard data error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="p-6">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">加载中...</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="p-6">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="text-red-500 text-xl mb-4">⚠️</div>
              <p className="text-gray-600 mb-4">{error}</p>
              <button
                onClick={loadDashboardData}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                重新加载
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="p-6">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-800 mb-2">数据总览</h1>
          <p className="text-gray-600">征信管理系统核心指标监控</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => (
            <StatsCard key={index} {...stat} />
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <RiskTrends dashboardData={dashboardData} />
          </div>
          <div>
            <RecentActivity />
          </div>
        </div>
      </main>
    </div>
  );
}
