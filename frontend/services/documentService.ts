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
        if (params.project_id) {
          // 需要根据project_id过滤，首先需要获取项目名称
          const { mockProjects } = await import('@/data/mockData');
          const targetProject = mockProjects.find(p => p.id == params.project_id);
          if (targetProject) {
            filteredDocuments = filteredDocuments.filter(d => 
              d.project === targetProject.name
            );
          } else {
            // 如果找不到项目，返回空数组
            filteredDocuments = [];
          }
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

    // 真实API调用 - 使用FormData上传文件
    try {
      const formData = new FormData();
      formData.append('file', data.file);
      formData.append('name', data.name);
      formData.append('project', data.project);
      formData.append('type', data.type);

      // 获取认证token
      const token = localStorage.getItem('auth_token');
      const headers: Record<string, string> = {};

      if (token) {
        // 检查token是否过期
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          const isExpired = payload.exp * 1000 < Date.now();

          if (!isExpired) {
            headers['Authorization'] = `Bearer ${token}`;
          } else {
            // Token过期，清除本地存储并抛出错误
            localStorage.removeItem('auth_token');
            localStorage.removeItem('auth_user');
            throw new Error('登录已过期，请重新登录');
          }
        } catch (error) {
          // Token格式错误，清除本地存储并抛出错误
          localStorage.removeItem('auth_token');
          localStorage.removeItem('auth_user');
          throw new Error('认证信息无效，请重新登录');
        }
      } else {
        throw new Error('请先登录');
      }

      const response = await fetch(`${apiClient['baseUrl']}/documents/upload`, {
        method: 'POST',
        headers: headers,
        body: formData,
        // 不设置Content-Type，让浏览器自动设置multipart/form-data
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const responseData = await response.json();

      // 如果后端返回的是包装格式，直接返回
      if (responseData.success !== undefined) {
        return responseData;
      }

      // 否则包装成标准格式
      return {
        success: true,
        data: responseData
      };

    } catch (error) {
      console.error('Upload error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '上传失败'
      };
    }
  }

  /**
   * 获取文档状态
   */
  async getDocumentStatus(id: number): Promise<ApiResponse<{status: string, progress: number, error_message?: string}>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Getting document status: ${id}`);
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
        data: {
          status: document.status,
          progress: document.progress || 0
        }
      };
    }

    // 真实API调用
    return apiClient.get<{status: string, progress: number, error_message?: string}>(`/documents/${id}/status`);
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
   * 重试知识库解析
   */
  async retryKnowledgeBaseParsing(id: number): Promise<ApiResponse<void>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Retrying knowledge base parsing for document ${id}`);
      await mockDelay();

      const document = mockDocuments.find(d => d.id === id);
      if (!document) {
        return {
          success: false,
          error: 'Document not found'
        };
      }

      // 模拟重试成功
      document.status = 'parsing_kb';
      document.progress = 0;

      // 模拟解析进度
      setTimeout(() => {
        const doc = mockDocuments.find(d => d.id === id);
        if (doc) {
          doc.progress = 100;
          doc.status = 'completed';
        }
      }, 3000);

      return {
        success: true
      };
    }

    // 真实API调用
    return apiClient.post<void>(`/documents/${id}/retry`, {});
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

    // 真实API调用 - 下载原始文件
    return apiClient.getBlob(`/documents/${id}/download`);
  }

  /**
   * 下载处理后的文档
   */
  async downloadProcessedDocument(id: number): Promise<ApiResponse<Blob>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Downloading processed document ${id}`);
      await mockDelay();

      const document = mockDocuments.find(d => d.id === id);
      if (!document) {
        return {
          success: false,
          error: 'Document not found'
        };
      }

      // 创建一个模拟的Markdown文件blob
      const mockContent = `# ${document.name}\n\n这是处理后的Markdown内容示例。\n\n## 文档信息\n- 项目: ${document.project}\n- 大小: ${document.size}\n- 上传时间: ${document.uploadTime}`;
      const blob = new Blob([mockContent], { type: 'text/markdown' });

      return {
        success: true,
        data: blob
      };
    }

    // 真实API调用 - 下载处理后的文件
    return apiClient.getBlob(`/documents/${id}/processed-file`);
  }

  /**
   * 预览文档内容
   */
  async previewDocument(id: number): Promise<ApiResponse<{
    content: string;
    document_name: string;
    original_filename: string;
    file_type: string;
    processed_at: string | null;
  }>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Previewing document ${id}`);
      await mockDelay();

      const document = mockDocuments.find(d => d.id === id);
      if (!document) {
        return {
          success: false,
          error: 'Document not found'
        };
      }

      // 创建模拟的预览内容
      const mockContent = `# ${document.name}

这是文档的预览内容示例。

## 文档信息
- **项目**: ${document.project}
- **文件大小**: ${document.size}
- **上传时间**: ${document.uploadTime}
- **处理状态**: ${document.status}

## 内容概要

这里是文档的主要内容。在实际应用中，这里会显示经过AI处理后的Markdown格式内容。

### 表格示例

| 项目 | 值 |
|------|-----|
| 文档类型 | ${document.type} |
| 处理进度 | ${document.progress}% |

### 列表示例

- 项目一
- 项目二
- 项目三

> 注意：这是模拟数据，实际内容会根据文档处理结果显示。
`;

      return {
        success: true,
        data: {
          content: mockContent,
          document_name: document.name,
          original_filename: document.name,
          file_type: document.type,
          processed_at: new Date().toISOString()
        }
      };
    }

    // 真实API调用
    return apiClient.get<{
      content: string;
      document_name: string;
      original_filename: string;
      file_type: string;
      processed_at: string | null;
    }>(`/documents/${id}/preview`);
  }
}

// 导出文档服务实例
export const documentService = new DocumentService();
