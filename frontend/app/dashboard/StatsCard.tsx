
'use client';

interface StatsCardProps {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'stable';
  icon: string;
  color?: string;
}

export default function StatsCard({ title, value, change, trend, icon, color }: StatsCardProps) {
  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-green-600';
      case 'down':
        return 'text-red-600';
      case 'stable':
        return 'text-gray-600';
      default:
        return 'text-gray-600';
    }
  };

  const getTrendBgColor = () => {
    switch (trend) {
      case 'up':
        return 'bg-green-100';
      case 'down':
        return 'bg-red-100';
      case 'stable':
        return 'bg-gray-100';
      default:
        return 'bg-gray-100';
    }
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return 'ri-arrow-up-line';
      case 'down':
        return 'ri-arrow-down-line';
      case 'stable':
        return 'ri-subtract-line';
      default:
        return 'ri-subtract-line';
    }
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${getTrendBgColor()}`}>
          <i className={`${icon} text-xl ${color || getTrendColor()}`}></i>
        </div>
        <div className={`flex items-center text-sm font-medium ${getTrendColor()}`}>
          <i className={`${getTrendIcon()} mr-1`}></i>
          {change}
        </div>
      </div>
      
      <div>
        <h3 className="text-2xl font-bold text-gray-800 mb-1">{value}</h3>
        <p className="text-gray-600 text-sm">{title}</p>
      </div>
    </div>
  );
}
