/**
 * 知识库服务
 * 处理知识库相关的API调用
 */

import { apiClient } from './api';

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

class KnowledgeBaseService {
  /**
   * 重建项目的知识库
   */
  async rebuildKnowledgeBase(projectId: string | number): Promise<ApiResponse<void>> {
    try {
      return await apiClient.request<void>(`/projects/${projectId}/rebuild-knowledge-base`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('重建知识库失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '重建知识库失败'
      };
    }
  }

  /**
   * 获取知识库状态
   */
  async getKnowledgeBaseStatus(projectId: string | number): Promise<ApiResponse<any>> {
    try {
      return await apiClient.request<any>(`/projects/${projectId}/knowledge-base-status`, {
        method: 'GET'
      });
    } catch (error) {
      console.error('获取知识库状态失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取知识库状态失败'
      };
    }
  }
}

// 创建并导出服务实例
export const knowledgeBaseService = new KnowledgeBaseService();
