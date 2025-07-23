/**
 * 项目详情服务
 * 处理财务分析、经营状况、时间轴等详细信息
 */

import { apiClient, ApiResponse } from './api';

// 财务分析数据接口
export interface FinancialAnalysis {
  revenue: {
    current: number;
    previous: number;
    growth: number;
  };
  profit: {
    current: number;
    previous: number;
    growth: number;
  };
  assets: {
    current: number;
    previous: number;
    growth: number;
  };
  liabilities: {
    current: number;
    previous: number;
    growth: number;
  };
}

// 经营状况数据接口
export interface BusinessStatus {
  operatingStatus: 'normal' | 'warning' | 'risk';
  creditRating: string;
  riskLevel: 'low' | 'medium' | 'high';
  complianceScore: number;
  marketPosition: string;
  businessScope: string[];
}

// 时间轴事件接口
export interface TimelineEvent {
  id: number;
  date: string;
  type: 'document' | 'analysis' | 'report' | 'milestone';
  title: string;
  description: string;
  status: 'completed' | 'processing' | 'pending';
}

class ProjectDetailService {
  /**
   * 获取项目财务分析数据
   */
  async getFinancialAnalysis(projectId: number): Promise<ApiResponse<FinancialAnalysis>> {
    try {
      return await apiClient.request<FinancialAnalysis>(`/projects/${projectId}/financial-analysis`, {
        method: 'GET'
      });
    } catch (error) {
      console.error('获取财务分析数据失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取财务分析数据失败'
      };
    }
  }

  /**
   * 获取项目经营状况数据
   */
  async getBusinessStatus(projectId: number): Promise<ApiResponse<BusinessStatus>> {
    try {
      return await apiClient.request<BusinessStatus>(`/projects/${projectId}/business-status`, {
        method: 'GET'
      });
    } catch (error) {
      console.error('获取经营状况数据失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取经营状况数据失败'
      };
    }
  }

  /**
   * 获取项目时间轴数据
   */
  async getTimeline(projectId: number): Promise<ApiResponse<TimelineEvent[]>> {
    try {
      return await apiClient.request<TimelineEvent[]>(`/projects/${projectId}/timeline`, {
        method: 'GET'
      });
    } catch (error) {
      console.error('获取时间轴数据失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取时间轴数据失败'
      };
    }
  }

  /**
   * 生成项目报告
   */
  async generateReport(projectId: number): Promise<ApiResponse<{ content: string; filename: string }>> {
    try {
      return await apiClient.request<{ content: string; filename: string }>(`/projects/${projectId}/generate-report`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('生成报告失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '生成报告失败'
      };
    }
  }

  /**
   * 更新项目状态
   */
  async updateProjectStatus(projectId: number, status: string): Promise<ApiResponse<void>> {
    try {
      return await apiClient.request<void>(`/projects/${projectId}/status`, {
        method: 'PUT',
        body: { status }
      });
    } catch (error) {
      console.error('更新项目状态失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '更新项目状态失败'
      };
    }
  }
}

// 创建并导出服务实例
export const projectDetailService = new ProjectDetailService();
