/**
 * 文档服务
 * 处理文档相关的API调用和Mock数据
 */

import { apiClient, ApiResponse } from './api';
import { MOCK_CONFIG, mockLog, mockDelay } from '@/config/mock';
import { Document, mockDocuments } from '@/data/mockData';

/**
 * 文档上传数据
 */
export interface UploadDocumentData {
  name: string;
  project: string;
  type: 'pdf' | 'excel' | 'word' | 'image';
  file: File;
}

/**
 * 文档查询参数
 */
export interface DocumentQueryParams {
  project?: string;
  status?: 'completed' | 'processing' | 'failed';
  type?: 'pdf' | 'excel' | 'word' | 'image';
  search?: string;
  page?: number;
  limit?: number;
}

class DocumentService {
  /**
   * 获取文档列表
   */
  async getDocuments(params?: DocumentQueryParams): Promise<ApiResponse<Document[]>> {
    if (MOCK_CONFIG.enabled) {
      mockLog('Getting documents list', params);
      await mockDelay();

      let filteredDocuments = [...mockDocuments];

      // 应用过滤条件
      if (params) {
        if (params.project) {
          filteredDocuments = filteredDocuments.filter(d => 
            d.project.toLowerCase().includes(params.project!.toLowerCase())
          );
        }
        if (params.status) {
          filteredDocuments = filteredDocuments.filter(d => d.status === params.status);
        }
        if (params.type) {
          filteredDocuments = filteredDocuments.filter(d => d.type === params.type);
        }
        if (params.search) {
          const searchLower = params.search.toLowerCase();
          filteredDocuments = filteredDocuments.filter(d => 
            d.name.toLowerCase().includes(searchLower) ||
            d.project.toLowerCase().includes(searchLower)
          );
        }
      }

      return {
        success: true,
        data: filteredDocuments
      };
    }

    // 真实API调用
    const queryString = params ? new URLSearchParams(params as any).toString() : '';
    const endpoint = `/documents${queryString ? `?${queryString}` : ''}`;
    return apiClient.get<Document[]>(endpoint);
  }

  /**
   * 根据ID获取文档详情
   */
  async getDocumentById(id: number): Promise<ApiResponse<Document>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Getting document by ID: ${id}`);
      await mockDelay();

      const document = mockDocuments.find(d => d.id === id);
      if (!document) {
        return {
          success: false,
          error: 'Document not found'
        };
      }

      return {
        success: true,
        data: document
      };
    }

    // 真实API调用
    return apiClient.get<Document>(`/documents/${id}`);
  }

  /**
   * 上传文档
   */
  async uploadDocument(data: UploadDocumentData): Promise<ApiResponse<Document>> {
    if (MOCK_CONFIG.enabled) {
      mockLog('Uploading document', { name: data.name, project: data.project, type: data.type });
      await mockDelay(1000); // 上传需要更长时间

      const newDocument: Document = {
        id: Math.max(...mockDocuments.map(d => d.id)) + 1,
        name: data.name,
        project: data.project,
        type: data.type,
        size: `${(data.file.size / 1024 / 1024).toFixed(1)} MB`,
        status: 'processing',
        uploadTime: new Date().toLocaleString('zh-CN'),
        progress: 0
      };

      // 模拟添加到数据中
      mockDocuments.push(newDocument);

      // 模拟处理进度
      setTimeout(() => {
        const doc = mockDocuments.find(d => d.id === newDocument.id);
        if (doc) {
          doc.progress = 100;
          doc.status = 'completed';
        }
      }, 3000);

      return {
        success: true,
        data: newDocument
      };
    }

    // 真实API调用
    const formData = new FormData();
    formData.append('file', data.file);
    formData.append('name', data.name);
    formData.append('project', data.project);
    formData.append('type', data.type);

    return apiClient.request<Document>('/documents/upload', {
      method: 'POST',
      body: formData,
      headers: {} // 不设置Content-Type，让浏览器自动设置
    });
  }

  /**
   * 删除文档
   */
  async deleteDocument(id: number): Promise<ApiResponse<void>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Deleting document ${id}`);
      await mockDelay();

      const documentIndex = mockDocuments.findIndex(d => d.id === id);
      if (documentIndex === -1) {
        return {
          success: false,
          error: 'Document not found'
        };
      }

      // 从数组中移除文档
      mockDocuments.splice(documentIndex, 1);

      return {
        success: true
      };
    }

    // 真实API调用
    return apiClient.delete<void>(`/documents/${id}`);
  }

  /**
   * 下载文档
   */
  async downloadDocument(id: number): Promise<ApiResponse<Blob>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Downloading document ${id}`);
      await mockDelay();

      const document = mockDocuments.find(d => d.id === id);
      if (!document) {
        return {
          success: false,
          error: 'Document not found'
        };
      }

      // 创建一个模拟的文件blob
      const mockContent = `Mock content for ${document.name}`;
      const blob = new Blob([mockContent], { type: 'text/plain' });

      return {
        success: true,
        data: blob
      };
    }

    // 真实API调用
    return apiClient.get<Blob>(`/documents/${id}/download`);
  }
}

// 导出文档服务实例
export const documentService = new DocumentService();
