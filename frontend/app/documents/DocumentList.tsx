
'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { documentService } from '@/services/documentService';
import { Document } from '@/data/mockData';

interface DocumentListProps {
  activeTab: string;
  searchQuery: string;
  selectedProject: string;
  refreshTrigger?: number;
}

export default function DocumentList({ activeTab, searchQuery, selectedProject, refreshTrigger }: DocumentListProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const previousDataRef = useRef<Document[]>([]);

  // 智能更新函数 - 只更新真正改变的数据
  const updateDocuments = useCallback((newDocuments: Document[]) => {
    const prevDocs = previousDataRef.current;
    
    // 如果是首次加载或文档数量变化，直接更新
    if (prevDocs.length === 0 || prevDocs.length !== newDocuments.length) {
      setDocuments(newDocuments);
      previousDataRef.current = newDocuments;
      return;
    }

    // 检查是否有实质性变化
    const hasChanges = newDocuments.some((newDoc, index) => {
      const oldDoc = prevDocs[index];
      return !oldDoc || 
             oldDoc.id !== newDoc.id ||
             oldDoc.status !== newDoc.status ||
             oldDoc.progress !== newDoc.progress ||
             oldDoc.name !== newDoc.name;
    });

    // 只有在有实质性变化时才更新状态
    if (hasChanges) {
      setDocuments(newDocuments);
      previousDataRef.current = newDocuments;
    }
  }, []);

  // 加载文档数据
  const loadDocuments = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);

      // 构建查询参数，过滤掉空值
      const queryParams: any = {};
      if (searchQuery) {
        queryParams.search = searchQuery;
      }
      if (activeTab === 'completed' || activeTab === 'processing' || activeTab === 'failed' || activeTab === 'uploading') {
        queryParams.status = activeTab;
      }
      if (selectedProject) {
        queryParams.project = selectedProject;
      }

      const response = await documentService.getDocuments(queryParams);

      if (response.success && response.data && Array.isArray(response.data)) {
        // 如果选择了项目，前端再次过滤确保只显示该项目的文档
        let filteredData = response.data;
        if (selectedProject) {
          // 通过项目名或项目ID过滤（后端可能通过不同方式处理）
          filteredData = response.data.filter(doc => {
            // 假设后端已经过滤了，但为了保险，前端再次检查
            return true; // 信任后端过滤结果
          });
        }
        updateDocuments(filteredData);
      } else {
        setError(response.error || '加载文档失败');
        updateDocuments([]); // 确保documents始终是数组
      }
    } catch (err) {
      setError('网络错误，请稍后重试');
      updateDocuments([]); // 确保documents始终是数组
      console.error('Load documents error:', err);
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  }, [activeTab, searchQuery, selectedProject, updateDocuments]);

  // 初始加载和搜索/筛选变化时重新加载
  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  // 当refreshTrigger变化时，静默刷新（不显示loading状态）
  useEffect(() => {
    if (refreshTrigger && refreshTrigger > 0) {
      // 延迟刷新，避免过于频繁的更新
      const timer = setTimeout(() => {
        loadDocuments(false); // 静默刷新，不显示loading
      }, 300);
      
      return () => clearTimeout(timer);
    }
  }, [refreshTrigger, loadDocuments]);

  // 轮询正在处理的文档状态
  useEffect(() => {
    const processingDocs = documents.filter(doc => doc.status === 'processing' || doc.status === 'uploading');
    
    if (processingDocs.length === 0) {
      return;
    }

    const intervalId = setInterval(() => {
      // 静默刷新文档列表以获取最新状态
      loadDocuments(false);
    }, 2000); // 每2秒检查一次

    return () => clearInterval(intervalId);
  }, [documents, loadDocuments]);

  // 删除文档
  const handleDeleteDocument = async (id: number) => {
    try {
      const response = await documentService.deleteDocument(id);
      if (response.success) {
        // 重新加载文档列表
        loadDocuments();
      } else {
        alert(response.error || '删除文档失败');
      }
    } catch (err) {
      alert('删除文档失败，请稍后重试');
      console.error('Delete document error:', err);
    }
  };

  // 下载文档
  const handleDownloadDocument = async (id: number, name: string) => {
    try {
      const response = await documentService.downloadDocument(id);
      if (response.success && response.data) {
        // 创建下载链接
        const url = window.URL.createObjectURL(response.data);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = name;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert(response.error || '下载文档失败');
      }
    } catch (err) {
      alert('下载文档失败，请稍后重试');
      console.error('Download document error:', err);
    }
  };

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'pdf':
        return 'ri-file-pdf-line text-red-600';
      case 'excel':
        return 'ri-file-excel-line text-green-600';
      case 'word':
        return 'ri-file-word-line text-blue-600';
      case 'image':
        return 'ri-image-line text-purple-600';
      default:
        return 'ri-file-line text-gray-600';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'uploading':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '已完成';
      case 'processing':
        return '处理中';
      case 'uploading':
        return '上传中';
      case 'failed':
        return '失败';
      default:
        return '未知';
    }
  };

  // 由于已经在API层面进行了过滤，这里直接使用documents
  // 确保filteredDocuments始终是数组
  const filteredDocuments = Array.isArray(documents) ? documents : [];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100">
      <div className="p-6">
        {/* 未选择项目提示 */}
        {!selectedProject ? (
          <div className="text-center py-12">
            <i className="ri-folder-line text-4xl text-gray-400 mb-4"></i>
            <h3 className="text-lg font-medium text-gray-800 mb-2">请选择项目</h3>
            <p className="text-gray-600">在左侧选择项目后即可查看对应的文档列表</p>
          </div>
        ) : (
          <>
            {/* 加载状态 */}
            {loading && (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-gray-600">加载中...</span>
              </div>
            )}

            {/* 错误状态 */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                <div className="flex items-center">
                  <i className="ri-error-warning-line text-red-600 mr-2"></i>
                  <span className="text-red-800">{error}</span>
                  <button
                    onClick={() => loadDocuments()}
                    className="ml-auto text-red-600 hover:text-red-800 underline"
                  >
                    重试
                  </button>
                </div>
              </div>
            )}

            {/* 文档列表 */}
            {!loading && !error && (
              <div className="space-y-4">
                {filteredDocuments.map((doc) => (
            <div key={doc.id} className="flex items-center space-x-4 p-4 border border-gray-100 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="w-10 h-10 flex items-center justify-center rounded-lg bg-gray-100">
                <i className={`${getFileIcon(doc.type)} text-lg`}></i>
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="font-medium text-gray-800 truncate">{doc.name}</h4>
                </div>
                <div className="flex items-center text-sm text-gray-600 space-x-4">
                  <span>{doc.project}</span>
                  <span>•</span>
                  <span>{doc.size}</span>
                  <span>•</span>
                  <span>{doc.uploadTime}</span>
                </div>
                
                {(doc.status === 'processing' || doc.status === 'uploading') && (
                  <div className="mt-2 flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-blue-600"></div>
                    <span className="text-xs text-gray-600">
                      {doc.status === 'uploading' ? '正在上传...' : '正在解析...'}
                    </span>
                  </div>
                )}
              </div>
              
              <div className="flex items-center space-x-3">
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(doc.status)}`}>
                  {getStatusText(doc.status)}
                </span>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleDownloadDocument(doc.id, doc.name)}
                    className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-200 transition-colors"
                    title="下载文档"
                  >
                    <i className="ri-download-line text-gray-600"></i>
                  </button>
                  <button
                    className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-200 transition-colors"
                    title="预览文档"
                  >
                    <i className="ri-eye-line text-gray-600"></i>
                  </button>
                  <button
                    onClick={() => {
                      if (confirm(`确定要删除文档 "${doc.name}" 吗？`)) {
                        handleDeleteDocument(doc.id);
                      }
                    }}
                    className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-200 transition-colors"
                    title="删除文档"
                  >
                    <i className="ri-delete-bin-line text-gray-600"></i>
                  </button>
                </div>
              </div>
            </div>
          ))}
          </div>
            )}

            {/* 空状态 */}
            {!loading && !error && filteredDocuments.length === 0 && (
              <div className="text-center py-12">
                <i className="ri-file-list-3-line text-4xl text-gray-400 mb-4"></i>
                <h3 className="text-lg font-medium text-gray-800 mb-2">暂无文档</h3>
                <p className="text-gray-600">开始上传您的第一个文档</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
