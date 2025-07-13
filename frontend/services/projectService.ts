/**
 * 项目服务
 * 处理项目相关的API调用和Mock数据
 */

import { apiClient, ApiResponse } from './api';
import { MOCK_CONFIG, mockLog, mockDelay } from '@/config/mock';
import { Project, mockProjects } from '@/data/mockData';

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
    if (MOCK_CONFIG.enabled) {
      mockLog('Getting projects list', params);
      await mockDelay();

      let filteredProjects = [...mockProjects];

      // 应用过滤条件
      if (params) {
        if (params.type) {
          filteredProjects = filteredProjects.filter(p => p.type === params.type);
        }
        if (params.status) {
          filteredProjects = filteredProjects.filter(p => p.status === params.status);
        }
        if (params.search) {
          const searchLower = params.search.toLowerCase();
          filteredProjects = filteredProjects.filter(p => 
            p.name.toLowerCase().includes(searchLower)
          );
        }
      }

      return {
        success: true,
        data: filteredProjects
      };
    }

    // 真实API调用
    const queryString = params ? new URLSearchParams(params as any).toString() : '';
    const endpoint = `/projects${queryString ? `?${queryString}` : ''}`;
    return apiClient.get<Project[]>(endpoint);
  }

  /**
   * 根据ID获取项目详情
   */
  async getProjectById(id: number): Promise<ApiResponse<Project>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Getting project by ID: ${id}`);
      await mockDelay();

      const project = mockProjects.find(p => p.id === id);
      if (!project) {
        return {
          success: false,
          error: 'Project not found'
        };
      }

      return {
        success: true,
        data: project
      };
    }

    // 真实API调用
    return apiClient.get<Project>(`/projects/${id}`);
  }

  /**
   * 创建新项目
   */
  async createProject(data: CreateProjectData): Promise<ApiResponse<Project>> {
    if (MOCK_CONFIG.enabled) {
      mockLog('Creating new project', data);
      await mockDelay();

      const newProject: Project = {
        id: Math.max(...mockProjects.map(p => p.id)) + 1,
        name: data.name,
        type: data.type,
        status: 'collecting',
        score: 0,
        riskLevel: 'low',
        lastUpdate: new Date().toISOString().split('T')[0],
        documents: 0,
        progress: 0
      };

      // 模拟添加到数据中
      mockProjects.push(newProject);

      return {
        success: true,
        data: newProject
      };
    }

    // 真实API调用
    return apiClient.post<Project>('/projects', data);
  }

  /**
   * 更新项目
   */
  async updateProject(id: number, data: UpdateProjectData): Promise<ApiResponse<Project>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Updating project ${id}`, data);
      await mockDelay();

      const projectIndex = mockProjects.findIndex(p => p.id === id);
      if (projectIndex === -1) {
        return {
          success: false,
          error: 'Project not found'
        };
      }

      // 更新项目数据
      mockProjects[projectIndex] = {
        ...mockProjects[projectIndex],
        ...data,
        lastUpdate: new Date().toISOString().split('T')[0]
      };

      return {
        success: true,
        data: mockProjects[projectIndex]
      };
    }

    // 真实API调用
    return apiClient.put<Project>(`/projects/${id}`, data);
  }

  /**
   * 删除项目
   */
  async deleteProject(id: number): Promise<ApiResponse<void>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Deleting project ${id}`);
      await mockDelay();

      const projectIndex = mockProjects.findIndex(p => p.id === id);
      if (projectIndex === -1) {
        return {
          success: false,
          error: 'Project not found'
        };
      }

      // 从数组中移除项目
      mockProjects.splice(projectIndex, 1);

      return {
        success: true
      };
    }

    // 真实API调用
    return apiClient.delete<void>(`/projects/${id}`);
  }
}

// 导出项目服务实例
export const projectService = new ProjectService();
