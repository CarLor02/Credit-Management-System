
'use client';

interface StatsCardProps {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down';
  icon: string;
}

export default function StatsCard({ title, value, change, trend, icon }: StatsCardProps) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
          trend === 'up' ? 'bg-green-100' : 'bg-red-100'
        }`}>
          <i className={`${icon} text-xl ${
            trend === 'up' ? 'text-green-600' : 'text-red-600'
          }`}></i>
        </div>
        <div className={`flex items-center text-sm font-medium ${
          trend === 'up' ? 'text-green-600' : 'text-red-600'
        }`}>
          <i className={`${trend === 'up' ? 'ri-arrow-up-line' : 'ri-arrow-down-line'} mr-1`}></i>
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
