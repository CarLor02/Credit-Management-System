
'use client';

import { useState, useEffect } from 'react';
import { documentService } from '@/services/documentService';
import { Document } from '@/data/mockData';

interface DocumentListProps {
  activeTab: string;
  searchQuery: string;
  refreshTrigger?: number;
}

export default function DocumentList({ activeTab, searchQuery, refreshTrigger }: DocumentListProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 加载文档数据
  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError(null);

      // 构建查询参数，过滤掉空值
      const queryParams: any = {};
      if (searchQuery) {
        queryParams.search = searchQuery;
      }
      if (activeTab === 'completed' || activeTab === 'processing' || activeTab === 'failed') {
        queryParams.status = activeTab;
      }

      const response = await documentService.getDocuments(queryParams);

      if (response.success && response.data && Array.isArray(response.data)) {
        setDocuments(response.data);
      } else {
        setError(response.error || '加载文档失败');
        setDocuments([]); // 确保documents始终是数组
      }
    } catch (err) {
      setError('网络错误，请稍后重试');
      setDocuments([]); // 确保documents始终是数组
      console.error('Load documents error:', err);
    } finally {
      setLoading(false);
    }
  };

  // 初始加载和搜索/筛选变化时重新加载
  useEffect(() => {
    loadDocuments();
  }, [activeTab, searchQuery, refreshTrigger]);

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
                onClick={loadDocuments}
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
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(doc.status)}`}>
                    {getStatusText(doc.status)}
                  </span>
                </div>
                <div className="flex items-center text-sm text-gray-600 space-x-4">
                  <span>{doc.project}</span>
                  <span>•</span>
                  <span>{doc.size}</span>
                  <span>•</span>
                  <span>{doc.uploadTime}</span>
                </div>
                
                {doc.status === 'processing' && (
                  <div className="mt-2">
                    <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                      <span>解析进度</span>
                      <span>{doc.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-1">
                      <div
                        className="bg-blue-600 h-1 rounded-full transition-all duration-300"
                        style={{ width: `${doc.progress}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>
              
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
      </div>
    </div>
  );
}
