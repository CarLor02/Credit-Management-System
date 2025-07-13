/**
 * 项目详情服务
 * 处理财务分析、经营状况、时间轴等详细信息
 */

import { apiClient, ApiResponse } from './api';
import { MOCK_CONFIG, mockLog, mockDelay } from '@/config/mock';

// 财务分析数据接口
export interface FinancialAnalysis {
  id: number;
  project_id: number;
  total_assets: number | null;
  annual_revenue: number | null;
  net_profit: number | null;
  debt_ratio: number | null;
  current_ratio: number | null;
  quick_ratio: number | null;
  cash_ratio: number | null;
  gross_profit_margin: number | null;
  net_profit_margin: number | null;
  roe: number | null;
  roa: number | null;
  inventory_turnover: number | null;
  receivables_turnover: number | null;
  total_asset_turnover: number | null;
  revenue_growth_rate: number | null;
  profit_growth_rate: number | null;
  analysis_year: number;
  analysis_quarter: number | null;
  created_at: string;
  updated_at: string;
}

// 经营状况数据接口
export interface BusinessStatus {
  id: number;
  project_id: number;
  business_license_status: string;
  business_license_expiry: string | null;
  tax_registration_status: string;
  organization_code_status: string;
  legal_violations: number;
  tax_compliance_status: string;
  environmental_compliance: string;
  labor_compliance: string;
  market_risk_level: string;
  financial_risk_level: string;
  operational_risk_level: string;
  industry_ranking: number | null;
  market_share: number | null;
  competitive_advantage: string | null;
  overall_score: number;
  qualification_score: number;
  compliance_score: number;
  risk_score: number;
  risk_factors: string | null;
  improvement_suggestions: string | null;
  evaluation_date: string;
  created_at: string;
  updated_at: string;
}

// 时间轴事件接口
export interface TimelineEvent {
  id: number;
  project_id: number;
  event_title: string;
  event_description: string | null;
  event_type: string;
  status: string;
  priority: string;
  event_date: string;
  planned_date: string | null;
  completed_date: string | null;
  related_document_id: number | null;
  related_document_name: string | null;
  related_user_id: number | null;
  related_user_name: string | null;
  progress: number;
  created_by: number | null;
  creator_name: string | null;
  created_at: string;
  updated_at: string;
}

// 项目详情摘要接口
export interface ProjectDetailSummary {
  project: any;
  has_financial_data: boolean;
  has_business_status: boolean;
  timeline_events_count: number;
  latest_events: TimelineEvent[];
}

// 创建时间轴事件数据接口
export interface CreateTimelineEventData {
  event_title: string;
  event_description?: string;
  event_type?: string;
  status?: string;
  priority?: string;
  event_date: string;
  planned_date?: string;
  progress?: number;
}

// 更新时间轴事件数据接口
export interface UpdateTimelineEventData {
  event_title?: string;
  event_description?: string;
  status?: string;
  progress?: number;
  completed_date?: string;
}

class ProjectDetailService {
  /**
   * 获取项目财务分析数据
   */
  async getProjectFinancial(projectId: number): Promise<ApiResponse<FinancialAnalysis[]>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Getting financial data for project ${projectId}`);
      await mockDelay();

      // Mock财务分析数据
      const mockFinancialData: FinancialAnalysis[] = [
        {
          id: 1,
          project_id: projectId,
          total_assets: 25000.0,
          annual_revenue: 18000.0,
          net_profit: 3500.0,
          debt_ratio: 45.5,
          current_ratio: 1.8,
          quick_ratio: 1.4,
          cash_ratio: 0.9,
          gross_profit_margin: 28.5,
          net_profit_margin: 19.4,
          roe: 16.8,
          roa: 9.2,
          inventory_turnover: 5.2,
          receivables_turnover: 7.8,
          total_asset_turnover: 1.4,
          revenue_growth_rate: 15.2,
          profit_growth_rate: 18.7,
          analysis_year: 2024,
          analysis_quarter: null,
          created_at: '2025-07-10T10:00:00',
          updated_at: '2025-07-10T10:00:00'
        }
      ];

      return {
        success: true,
        data: mockFinancialData
      };
    }

    return apiClient.get<FinancialAnalysis[]>(`/projects/${projectId}/financial`);
  }

  /**
   * 获取项目经营状况数据
   */
  async getProjectBusinessStatus(projectId: number): Promise<ApiResponse<BusinessStatus>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Getting business status for project ${projectId}`);
      await mockDelay();

      // Mock经营状况数据
      const mockBusinessStatus: BusinessStatus = {
        id: 1,
        project_id: projectId,
        business_license_status: 'normal',
        business_license_expiry: '2026-12-31',
        tax_registration_status: 'normal',
        organization_code_status: 'normal',
        legal_violations: 0,
        tax_compliance_status: 'compliant',
        environmental_compliance: 'compliant',
        labor_compliance: 'compliant',
        market_risk_level: 'low',
        financial_risk_level: 'low',
        operational_risk_level: 'low',
        industry_ranking: 15,
        market_share: 8.5,
        competitive_advantage: '技术领先，品牌优势明显，成本控制能力强',
        overall_score: 85,
        qualification_score: 92,
        compliance_score: 88,
        risk_score: 78,
        risk_factors: '市场竞争激烈，原材料价格波动',
        improvement_suggestions: '加强技术创新，优化成本结构，拓展新市场',
        evaluation_date: '2025-07-10',
        created_at: '2025-07-10T10:00:00',
        updated_at: '2025-07-10T10:00:00'
      };

      return {
        success: true,
        data: mockBusinessStatus
      };
    }

    return apiClient.get<BusinessStatus>(`/projects/${projectId}/business-status`);
  }

  /**
   * 获取项目时间轴数据
   */
  async getProjectTimeline(projectId: number, params?: {
    limit?: number;
    offset?: number;
    status?: string;
  }): Promise<ApiResponse<{
    data: TimelineEvent[];
    pagination: {
      total: number;
      limit: number;
      offset: number;
      has_more: boolean;
    };
  }>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Getting timeline for project ${projectId}`, params);
      await mockDelay();

      // Mock时间轴数据
      const mockTimelineEvents: TimelineEvent[] = [
        {
          id: 1,
          project_id: projectId,
          event_title: '项目启动',
          event_description: '项目正式启动，开始收集相关资料',
          event_type: 'milestone',
          status: 'completed',
          priority: 'high',
          event_date: '2025-06-10',
          planned_date: '2025-06-10',
          completed_date: '2025-06-10',
          related_document_id: null,
          related_document_name: null,
          related_user_id: 1,
          related_user_name: '管理员',
          progress: 100,
          created_by: 1,
          creator_name: '管理员',
          created_at: '2025-06-10T09:00:00',
          updated_at: '2025-06-10T09:00:00'
        },
        {
          id: 2,
          project_id: projectId,
          event_title: '文档收集完成',
          event_description: '完成所有必要文档的收集工作',
          event_type: 'document',
          status: 'completed',
          priority: 'medium',
          event_date: '2025-06-15',
          planned_date: '2025-06-15',
          completed_date: '2025-06-15',
          related_document_id: null,
          related_document_name: null,
          related_user_id: 1,
          related_user_name: '管理员',
          progress: 100,
          created_by: 1,
          creator_name: '管理员',
          created_at: '2025-06-15T14:00:00',
          updated_at: '2025-06-15T14:00:00'
        },
        {
          id: 3,
          project_id: projectId,
          event_title: '财务数据分析',
          event_description: '对企业财务数据进行深入分析',
          event_type: 'analysis',
          status: 'in_progress',
          priority: 'high',
          event_date: '2025-07-05',
          planned_date: '2025-07-05',
          completed_date: null,
          related_document_id: null,
          related_document_name: null,
          related_user_id: 1,
          related_user_name: '管理员',
          progress: 75,
          created_by: 1,
          creator_name: '管理员',
          created_at: '2025-07-05T10:00:00',
          updated_at: '2025-07-10T15:30:00'
        }
      ];

      return {
        success: true,
        data: {
          data: mockTimelineEvents,
          pagination: {
            total: mockTimelineEvents.length,
            limit: params?.limit || 50,
            offset: params?.offset || 0,
            has_more: false
          }
        }
      };
    }

    const queryString = params ? new URLSearchParams(params as any).toString() : '';
    const endpoint = `/projects/${projectId}/timeline${queryString ? `?${queryString}` : ''}`;
    return apiClient.get(endpoint);
  }

  /**
   * 创建时间轴事件
   */
  async createTimelineEvent(projectId: number, data: CreateTimelineEventData): Promise<ApiResponse<TimelineEvent>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Creating timeline event for project ${projectId}`, data);
      await mockDelay();

      const newEvent: TimelineEvent = {
        id: Date.now(),
        project_id: projectId,
        event_title: data.event_title,
        event_description: data.event_description || null,
        event_type: data.event_type || 'other',
        status: data.status || 'pending',
        priority: data.priority || 'medium',
        event_date: data.event_date,
        planned_date: data.planned_date || null,
        completed_date: null,
        related_document_id: null,
        related_document_name: null,
        related_user_id: null,
        related_user_name: null,
        progress: data.progress || 0,
        created_by: 1,
        creator_name: '管理员',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      return {
        success: true,
        data: newEvent
      };
    }

    return apiClient.post<TimelineEvent>(`/projects/${projectId}/timeline`, data);
  }

  /**
   * 更新时间轴事件
   */
  async updateTimelineEvent(
    projectId: number, 
    eventId: number, 
    data: UpdateTimelineEventData
  ): Promise<ApiResponse<TimelineEvent>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Updating timeline event ${eventId} for project ${projectId}`, data);
      await mockDelay();

      // Mock更新响应
      return {
        success: true,
        data: {} as TimelineEvent // 简化的mock响应
      };
    }

    return apiClient.put<TimelineEvent>(`/projects/${projectId}/timeline/${eventId}`, data);
  }

  /**
   * 获取项目详情摘要
   */
  async getProjectDetailSummary(projectId: number): Promise<ApiResponse<ProjectDetailSummary>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Getting project detail summary for ${projectId}`);
      await mockDelay();

      const mockSummary: ProjectDetailSummary = {
        project: {}, // 这里会被实际的项目数据填充
        has_financial_data: true,
        has_business_status: true,
        timeline_events_count: 5,
        latest_events: []
      };

      return {
        success: true,
        data: mockSummary
      };
    }

    return apiClient.get<ProjectDetailSummary>(`/projects/${projectId}/summary`);
  }
}

// 导出项目详情服务实例
export const projectDetailService = new ProjectDetailService();
