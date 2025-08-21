/**
 * 项目服务
 * 处理项目相关的API调用
 */

import { apiClient, ApiResponse } from './api';

// 项目接口定义
export interface Project {
  id: number;
  name: string;
  type: 'enterprise' | 'individual';
  status: 'collecting' | 'processing' | 'completed';
  score: number;
  riskLevel: 'low' | 'medium' | 'high';
  lastUpdate: string;
  documents: number;
  progress: number;
  description?: string;
  created_by?: number;
  assigned_to?: number;
  created_at?: string;
  updated_at?: string;
  // 知识库相关字段
  dataset_id?: string;
  knowledge_base_name?: string;
  // 报告相关字段
  report_status?: 'not_generated' | 'generating' | 'generated' | 'cancelled';
  report_path?: string;
}

/**
 * 项目创建数据
 */
export interface CreateProjectData {
  name: string;
  type: 'enterprise' | 'individual';
  description?: string;
}

/**
 * 项目更新数据
 */
export interface UpdateProjectData {
  name?: string;
  status?: 'collecting' | 'processing' | 'completed';
  score?: number;
  riskLevel?: 'low' | 'medium' | 'high';
}

/**
 * 项目查询参数
 */
export interface ProjectQueryParams {
  type?: 'enterprise' | 'individual';
  status?: 'collecting' | 'processing' | 'completed';
  search?: string;
  page?: number;
  limit?: number;
}

class ProjectService {
  /**
   * 获取项目列表
   */
  async getProjects(params?: ProjectQueryParams): Promise<ApiResponse<Project[]>> {
    try {
      // 构建查询参数
      const queryParams = new URLSearchParams();
      
      if (params) {
        if (params.type) {
          queryParams.append('type', params.type);
        }
        if (params.status) {
          queryParams.append('status', params.status);
        }
        if (params.search) {
          queryParams.append('search', params.search);
        }
        if (params.page) {
          queryParams.append('page', params.page.toString());
        }
        if (params.limit) {
          queryParams.append('limit', params.limit.toString());
        }
      }

      const url = queryParams.toString() ? `/projects?${queryParams.toString()}` : '/projects';
      return await apiClient.request<Project[]>(url, { method: 'GET' });
    } catch (error) {
      console.error('获取项目列表失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取项目列表失败'
      };
    }
  }

  /**
   * 创建项目
   */
  async createProject(data: CreateProjectData): Promise<ApiResponse<Project>> {
    try {
      return await apiClient.request<Project>('/projects', {
        method: 'POST',
        body: data
      });
    } catch (error) {
      console.error('创建项目失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '创建项目失败'
      };
    }
  }

  /**
   * 获取项目详情
   */
  async getProject(id: number): Promise<ApiResponse<Project>> {
    try {
      return await apiClient.request<Project>(`/projects/${id}`, { method: 'GET' });
    } catch (error) {
      console.error('获取项目详情失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取项目详情失败'
      };
    }
  }

  /**
   * 根据ID获取项目详情（别名方法，保持向后兼容）
   */
  async getProjectById(id: number): Promise<ApiResponse<Project>> {
    return this.getProject(id);
  }

  /**
   * 更新项目
   */
  async updateProject(id: number, data: UpdateProjectData): Promise<ApiResponse<Project>> {
    try {
      return await apiClient.request<Project>(`/projects/${id}`, {
        method: 'PUT',
        body: data
      });
    } catch (error) {
      console.error('更新项目失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '更新项目失败'
      };
    }
  }

  /**
   * 删除项目
   */
  async deleteProject(id: number): Promise<ApiResponse<void>> {
    try {
      return await apiClient.request<void>(`/projects/${id}`, { method: 'DELETE' });
    } catch (error) {
      console.error('删除项目失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '删除项目失败'
      };
    }
  }
}

// 创建并导出服务实例
export const projectService = new ProjectService();
