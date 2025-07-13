
'use client';

import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, Area, AreaChart } from 'recharts';
import { statsService, TrendData, DashboardStats } from '@/services/statsService';

interface RiskTrendsProps {
  dashboardData?: DashboardStats | null;
}

export default function RiskTrends({ dashboardData }: RiskTrendsProps) {
  const [trendsData, setTrendsData] = useState<TrendData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTrendsData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await statsService.getTrendsData('month', 6);

      if (response.success && response.data) {
        setTrendsData(response.data);
      } else {
        setError(response.error || '加载趋势数据失败');
      }
    } catch (err) {
      setError('网络错误，请稍后重试');
      console.error('Load trends data error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTrendsData();
  }, []);

  // 转换数据格式以适配图表
  const chartData = Array.isArray(trendsData) ? trendsData.map(item => {
    const totalProjects = item.total_projects || 1; // 避免除零
    const riskProjects = item.risk_projects || 0;
    const normalProjects = item.normal_projects || 0;

    // 计算风险比例（百分比）
    const riskRatio = (riskProjects / totalProjects) * 100;
    const normalRatio = (normalProjects / totalProjects) * 100;

    return {
      month: item.month,
      风险比例: Math.round(riskRatio * 10) / 10, // 保留1位小数
      正常比例: Math.round(normalRatio * 10) / 10,
      风险项目数: riskProjects,
      正常项目数: normalProjects,
      总项目数: totalProjects,
      平均评分: Math.round(item.average_score * 10) / 10
    };
  }) : [];

  if (loading) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center justify-center h-80">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-gray-600 text-sm">加载趋势数据...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center justify-center h-80">
          <div className="text-center">
            <div className="text-red-500 text-xl mb-2">⚠️</div>
            <p className="text-gray-600 text-sm mb-4">{error}</p>
            <button
              onClick={loadTrendsData}
              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
            >
              重新加载
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">风险趋势分析</h2>
          <p className="text-sm text-gray-600 mt-1">近6个月征信风险变化趋势</p>
        </div>
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
            <span className="text-gray-600">风险比例(%)</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
            <span className="text-gray-600">正常比例(%)</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
            <span className="text-gray-600">平均评分</span>
          </div>
        </div>
      </div>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="month"
              stroke="#9ca3af"
              fontSize={12}
            />
            {/* 左Y轴：风险比例 (0-100%) */}
            <YAxis
              yAxisId="percentage"
              stroke="#9ca3af"
              fontSize={12}
              domain={[0, 100]}
              label={{ value: '比例(%)', angle: -90, position: 'insideLeft' }}
            />
            {/* 右Y轴：评分 (0-100分) */}
            <YAxis
              yAxisId="score"
              orientation="right"
              stroke="#3b82f6"
              fontSize={12}
              domain={[0, 100]}
              label={{ value: '评分', angle: 90, position: 'insideRight' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
              formatter={(value: any, name: string) => {
                if (name === '风险比例' || name === '正常比例') {
                  return [`${value}%`, name];
                } else if (name === '平均评分') {
                  return [`${value}分`, name];
                }
                return [value, name];
              }}
              labelFormatter={(label) => `${label}`}
            />

            {/* 风险比例区域图 */}
            <Area
              yAxisId="percentage"
              type="monotone"
              dataKey="风险比例"
              stroke="#ef4444"
              fill="#ef4444"
              fillOpacity={0.2}
              strokeWidth={2}
            />

            {/* 正常比例区域图 */}
            <Area
              yAxisId="percentage"
              type="monotone"
              dataKey="正常比例"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.1}
              strokeWidth={1}
            />

            {/* 平均评分线图 */}
            <Line
              yAxisId="score"
              type="monotone"
              dataKey="平均评分"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2, fill: '#fff' }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
