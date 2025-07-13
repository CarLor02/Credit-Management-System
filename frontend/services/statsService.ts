/**
 * 统计服务
 * 处理仪表板统计、趋势数据、活动日志等
 */

import { apiClient, ApiResponse } from './api';
import { MOCK_CONFIG, mockLog, mockDelay } from '@/config/mock';

// 统计数据接口定义
export interface DashboardStats {
  projects: {
    total: number;
    completed: number;
    processing: number;
    collecting: number;
    archived: number;
    completion_rate: number;
  };
  documents: {
    total: number;
    completed: number;
    processing: number;
    failed: number;
    completion_rate: number;
  };
  users: {
    total: number;
    active: number;
  };
  risk_analysis: {
    high_risk: number;
    medium_risk: number;
    low_risk: number;
  };
  average_score: number;
}

export interface TrendData {
  period: string;
  month: string;
  total_projects: number;
  risk_projects: number;
  normal_projects: number;
  average_score: number;
}

export interface ActivityItem {
  id: number;
  type: string;
  title: string;
  description?: string;
  user_name: string;
  created_at: string;
  relative_time: string;
}

// 前端展示用的统计卡片数据
export interface StatCard {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'stable';
  icon: string;
  color?: string;
}

class StatsService {
  /**
   * 获取仪表板统计数据
   */
  async getDashboardStats(): Promise<ApiResponse<DashboardStats>> {
    if (MOCK_CONFIG.enabled) {
      mockLog('Getting dashboard stats');
      await mockDelay();

      const mockStats: DashboardStats = {
        projects: {
          total: 156,
          completed: 89,
          processing: 23,
          collecting: 32,
          archived: 12,
          completion_rate: 57.1
        },
        documents: {
          total: 342,
          completed: 298,
          processing: 15,
          failed: 29,
          completion_rate: 87.1
        },
        users: {
          total: 24,
          active: 18
        },
        risk_analysis: {
          high_risk: 7,
          medium_risk: 45,
          low_risk: 104
        },
        average_score: 78.5
      };

      return {
        success: true,
        data: mockStats
      };
    }

    return apiClient.get<DashboardStats>('/stats/dashboard');
  }

  /**
   * 获取趋势数据
   */
  async getTrendsData(period: string = 'month', months: number = 6): Promise<ApiResponse<TrendData[]>> {
    if (MOCK_CONFIG.enabled) {
      mockLog('Getting trends data', { period, months });
      await mockDelay();

      const mockTrends: TrendData[] = [
        {
          period: '2024-07',
          month: '7月',
          total_projects: 120,
          risk_projects: 12,
          normal_projects: 108,
          average_score: 76.2
        },
        {
          period: '2024-08',
          month: '8月',
          total_projects: 135,
          risk_projects: 8,
          normal_projects: 127,
          average_score: 78.5
        },
        {
          period: '2024-09',
          month: '9月',
          total_projects: 142,
          risk_projects: 15,
          normal_projects: 127,
          average_score: 75.8
        },
        {
          period: '2024-10',
          month: '10月',
          total_projects: 148,
          risk_projects: 9,
          normal_projects: 139,
          average_score: 79.2
        },
        {
          period: '2024-11',
          month: '11月',
          total_projects: 152,
          risk_projects: 11,
          normal_projects: 141,
          average_score: 77.9
        },
        {
          period: '2024-12',
          month: '12月',
          total_projects: 156,
          risk_projects: 7,
          normal_projects: 149,
          average_score: 78.5
        }
      ];

      return {
        success: true,
        data: mockTrends
      };
    }

    // 真实API调用
    const params = new URLSearchParams({ period, months: months.toString() });
    return apiClient.get<TrendData[]>(`/stats/trends?${params}`);
  }

  /**
   * 获取最近活动
   */
  async getRecentActivities(limit: number = 10): Promise<ApiResponse<ActivityItem[]>> {
    if (MOCK_CONFIG.enabled) {
      mockLog('Getting recent activities', { limit });
      await mockDelay();

      const mockActivities: ActivityItem[] = [
        {
          id: 1,
          type: 'report_generated',
          title: '腾讯科技征信报告已生成',
          description: '项目ID: 1, 评分: 85',
          user_name: '张三',
          created_at: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
          relative_time: '2分钟前'
        },
        {
          id: 2,
          type: 'document_uploaded',
          title: '阿里巴巴财务文档上传完成',
          description: '文件: 财务报表.pdf',
          user_name: '李四',
          created_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
          relative_time: '15分钟前'
        },
        {
          id: 3,
          type: 'project_created',
          title: '创建了新项目：字节跳动征信分析',
          description: '项目ID: 13',
          user_name: '王五',
          created_at: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
          relative_time: '45分钟前'
        },
        {
          id: 4,
          type: 'user_login',
          title: '赵六 登录系统',
          user_name: '赵六',
          created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          relative_time: '2小时前'
        },
        {
          id: 5,
          type: 'report_generated',
          title: '美团征信报告已生成',
          description: '项目ID: 8, 评分: 92',
          user_name: '孙七',
          created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
          relative_time: '4小时前'
        }
      ];

      return {
        success: true,
        data: mockActivities.slice(0, limit)
      };
    }

    return apiClient.get<ActivityItem[]>(`/stats/recent-activities?limit=${limit}`);
  }

  /**
   * 将统计数据转换为前端卡片格式
   */
  transformToStatCards(stats: DashboardStats): StatCard[] {
    // 添加防御性检查
    if (!stats || !stats.projects) {
      console.error('Invalid stats data:', stats);
      return [];
    }

    const { projects, documents, users } = stats;

    // 确保所有必需的字段都存在，提供默认值
    const safeProjects = {
      total: projects?.total ?? 0,
      completed: projects?.completed ?? 0,
      processing: projects?.processing ?? 0,
      collecting: projects?.collecting ?? 0,
      archived: projects?.archived ?? 0,
      completion_rate: projects?.completion_rate ?? 0
    };

    const safeDocuments = {
      total: documents?.total ?? 0,
      completed: documents?.completed ?? 0,
      processing: documents?.processing ?? 0,
      failed: documents?.failed ?? 0,
      completion_rate: documents?.completion_rate ?? 0
    };

    const safeUsers = {
      total: users?.total ?? 0,
      active: users?.active ?? 0
    };

    return [
      {
        title: '总项目数',
        value: safeProjects.total.toString(),
        change: this.calculateChange(safeProjects.total, 144), // 假设上期数据
        trend: safeProjects.total > 144 ? 'up' : 'down',
        icon: 'ri-folder-line',
        color: 'text-blue-600'
      },
      {
        title: '待处理项目',
        value: safeProjects.processing.toString(),
        change: this.calculateChange(safeProjects.processing, 28),
        trend: safeProjects.processing < 28 ? 'up' : 'down', // 待处理减少是好事
        icon: 'ri-time-line',
        color: 'text-orange-600'
      },
      {
        title: '已完成报告',
        value: safeProjects.completed.toString(),
        change: this.calculateChange(safeProjects.completed, 76),
        trend: safeProjects.completed > 76 ? 'up' : 'down',
        icon: 'ri-file-text-line',
        color: 'text-green-600'
      },
      {
        title: '风险预警',
        value: (stats.risk_analysis?.high_risk ?? 0).toString(),
        change: this.calculateChange(stats.risk_analysis?.high_risk ?? 0, 5),
        trend: (stats.risk_analysis?.high_risk ?? 0) < 5 ? 'up' : 'down', // 风险减少是好事
        icon: 'ri-alert-line',
        color: 'text-red-600'
      }
    ];
  }

  /**
   * 计算变化百分比
   */
  private calculateChange(current: number, previous: number): string {
    if (previous === 0) return '+100%';
    
    const change = ((current - previous) / previous) * 100;
    const sign = change >= 0 ? '+' : '';
    return `${sign}${Math.round(change)}%`;
  }

  /**
   * 获取活动类型对应的图标和颜色
   */
  getActivityIcon(type: string): { icon: string; color: string } {
    const iconMap: Record<string, { icon: string; color: string }> = {
      'report_generated': { icon: 'ri-file-text-line', color: 'text-blue-600' },
      'document_uploaded': { icon: 'ri-upload-line', color: 'text-green-600' },
      'project_created': { icon: 'ri-folder-add-line', color: 'text-purple-600' },
      'user_login': { icon: 'ri-user-line', color: 'text-gray-600' },
      'project_updated': { icon: 'ri-edit-line', color: 'text-orange-600' },
      'document_deleted': { icon: 'ri-delete-bin-line', color: 'text-red-600' }
    };

    return iconMap[type] || { icon: 'ri-information-line', color: 'text-gray-600' };
  }

  /**
   * 手动更新统计数据
   */
  async updateDailyStats(): Promise<ApiResponse<void>> {
    if (MOCK_CONFIG.enabled) {
      mockLog('Updating daily stats');
      await mockDelay();

      return {
        success: true,
        message: '统计数据更新成功'
      };
    }

    return apiClient.post<void>('/stats/update');
  }
}

export const statsService = new StatsService();
