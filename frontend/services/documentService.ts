/**
 * 文档服务
 * 处理文档相关的API调用
 */

import { apiClient, ApiResponse } from './api';

// 文档接口定义
export interface Document {
  id: number;
  name: string;
  project: string;
  project_id: number;
  type: 'pdf' | 'excel' | 'word' | 'image' | 'markdown';
  size: string;
  status: 'uploading' | 'processing' | 'uploading_to_kb' | 'parsing_kb' | 'completed' | 'failed' | 'kb_parse_failed';
  uploadTime: string;
  progress: number;
}

/**
 * 文档上传数据
 */
export interface UploadDocumentData {
  name: string;
  project: string;
  project_id: number;
  type: 'pdf' | 'excel' | 'word' | 'image' | 'markdown';
  file: File;
}

/**
 * 文档查询参数
 */
export interface DocumentQueryParams {
  project?: string;
  project_id?: number | string;
  status?: 'uploading' | 'processing' | 'uploading_to_kb' | 'parsing_kb' | 'completed' | 'failed' | 'kb_parse_failed';
  type?: 'pdf' | 'excel' | 'word' | 'image' | 'markdown';
  search?: string;
  page?: number;
  limit?: number;
}

class DocumentService {
  /**
   * 获取文档列表
   */
  async getDocuments(params?: DocumentQueryParams): Promise<ApiResponse<Document[]>> {
    try {
      // 构建查询参数
      const queryParams = new URLSearchParams();

      if (params) {
        if (params.project_id) {
          queryParams.append('project_id', params.project_id.toString());
        }
        if (params.status) {
          queryParams.append('status', params.status);
        }
        if (params.type) {
          queryParams.append('type', params.type);
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

      const url = queryParams.toString() ? `/documents?${queryParams.toString()}` : '/documents';
      return await apiClient.request<Document[]>(url, { method: 'GET' });
    } catch (error) {
      console.error('获取文档列表失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '获取文档列表失败'
      };
    }
  }

  /**
   * 上传文档
   */
  async uploadDocument(data: UploadDocumentData): Promise<ApiResponse<Document>> {
    try {
      // 使用FormData上传文件
      const formData = new FormData();
      formData.append('file', data.file);
      formData.append('name', data.name);
      formData.append('project', data.project);
      formData.append('project_id', data.project_id.toString());
      formData.append('type', data.type);

      const token = localStorage.getItem('auth_token');
      const headers: Record<string, string> = {};

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      } else {
        throw new Error('请先登录');
      }

      const response = await fetch(`${apiClient['baseUrl']}/documents/upload`, {
        method: 'POST',
        headers: headers,
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const responseData = await response.json();
      return responseData.success !== undefined ? responseData : { success: true, data: responseData };

    } catch (error) {
      console.error('上传文档失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '上传文档失败'
      };
    }
  }

  /**
   * 删除文档
   */
  async deleteDocument(id: number): Promise<ApiResponse<void>> {
    try {
      return await apiClient.request<void>(`/documents/${id}`, { method: 'DELETE' });
    } catch (error) {
      console.error('删除文档失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '删除文档失败'
      };
    }
  }

  /**
   * 下载文档
   */
  async downloadDocument(id: number): Promise<ApiResponse<Blob>> {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('请先登录');
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5001/api'}/documents/${id}/download`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('下载失败');
      }

      const blob = await response.blob();
      return {
        success: true,
        data: blob
      };
    } catch (error) {
      console.error('下载文档失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '下载文档失败'
      };
    }
  }

  /**
   * 重试知识库解析
   */
  async retryKnowledgeBaseParsing(documentId: number): Promise<ApiResponse<void>> {
    try {
      return await apiClient.request<void>(`/documents/${documentId}/retry-parsing`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('重试知识库解析失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '重试知识库解析失败'
      };
    }
  }
}

// 创建并导出服务实例
export const documentService = new DocumentService();