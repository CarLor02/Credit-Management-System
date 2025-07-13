
'use client';

import { useState, useEffect } from 'react';
import { statsService, ActivityItem } from '@/services/statsService';

export default function RecentActivity() {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadActivities = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await statsService.getRecentActivities(8);

      if (response.success && response.data) {
        setActivities(response.data);
      } else {
        setError(response.error || '加载活动数据失败');
      }
    } catch (err) {
      setError('网络错误，请稍后重试');
      console.error('Load activities error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadActivities();
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-800">最近活动</h2>
        </div>
        <div className="flex items-center justify-center h-48">
          <div className="text-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-gray-600 text-sm">加载活动数据...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-800">最近活动</h2>
        </div>
        <div className="flex items-center justify-center h-48">
          <div className="text-center">
            <div className="text-red-500 text-lg mb-2">⚠️</div>
            <p className="text-gray-600 text-sm mb-4">{error}</p>
            <button
              onClick={loadActivities}
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
        <h2 className="text-lg font-semibold text-gray-800">最近活动</h2>
        <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
          查看全部
        </button>
      </div>

      <div className="space-y-4">
        {activities.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 text-4xl mb-2">📝</div>
            <p className="text-gray-500 text-sm">暂无活动记录</p>
          </div>
        ) : (
          activities.map((activity) => {
            const { icon, color } = statsService.getActivityIcon(activity.type);
            return (
              <div key={activity.id} className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                <div className={`flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center ${color}`}>
                  <i className={`${icon} text-sm`}></i>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">
                    {activity.title}
                  </p>
                  {activity.description && (
                    <p className="text-xs text-gray-600 mt-1 truncate">
                      {activity.description}
                    </p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    {activity.relative_time}
                  </p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
