'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { documentService, Document } from '@/services/documentService';
import DocumentPreview from '@/components/DocumentPreview';

interface DocumentListProps {
  activeTab: string;
  searchQuery: string;
  selectedProject: string;
  refreshTrigger?: number;
  onDocumentChange?: () => void; // 新增：文档变化时的回调
}

export default function DocumentList({ activeTab, searchQuery, selectedProject, refreshTrigger, onDocumentChange }: DocumentListProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const previousDataRef = useRef<Document[]>([]);

  // 预览相关状态
  const [previewDocument, setPreviewDocument] = useState<{ id: number; name: string } | null>(null);

  // 智能更新函数 - 只更新真正改变的数据
  const updateDocuments = useCallback((newDocuments: Document[]) => {
    const prevDocs = previousDataRef.current;
    
    // 如果是首次加载，直接更新
    if (prevDocs.length === 0) {
      setDocuments(newDocuments);
      previousDataRef.current = newDocuments;
      return;
    }

    // 如果文档数量变化，直接更新
    if (prevDocs.length !== newDocuments.length) {
      setDocuments(newDocuments);
      previousDataRef.current = newDocuments;
      return;
    }

    // 创建ID映射以便快速查找
    const prevDocsMap = new Map(prevDocs.map(doc => [doc.id, doc]));
    const newDocsMap = new Map(newDocuments.map(doc => [doc.id, doc]));

    // 检查是否有实质性变化
    let hasChanges = false;
    
    // 检查新文档是否有变化
    for (const newDoc of newDocuments) {
      const oldDoc = prevDocsMap.get(newDoc.id);
      if (!oldDoc || 
          oldDoc.status !== newDoc.status ||
          oldDoc.progress !== newDoc.progress ||
          oldDoc.name !== newDoc.name ||
          oldDoc.type !== newDoc.type) {
        hasChanges = true;
        break;
      }
    }

    // 如果没有变化，不更新
    if (!hasChanges) {
      return;
    }

    // 使用requestAnimationFrame确保在下一帧更新，减少闪烁
    requestAnimationFrame(() => {
      setDocuments(newDocuments);
      previousDataRef.current = newDocuments;
    });
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
        queryParams.project_id = selectedProject; // 使用 project_id 参数
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

  // 监听知识库重建事件
  useEffect(() => {
    const handleKnowledgeBaseRebuilt = (event: CustomEvent) => {
      const { projectId } = event.detail;
      // 如果重建的是当前选中的项目，刷新文档列表
      if (projectId === selectedProject) {
        console.log('知识库重建完成，刷新文档列表');
        loadDocuments(true);
      }
    };

    window.addEventListener('knowledgeBaseRebuilt', handleKnowledgeBaseRebuilt as EventListener);

    return () => {
      window.removeEventListener('knowledgeBaseRebuilt', handleKnowledgeBaseRebuilt as EventListener);
    };
  }, [selectedProject, loadDocuments]);

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
    const processingDocs = documents.filter(doc => 
      doc.status === 'uploading' || 
      doc.status === 'processing' || 
      doc.status === 'uploading_to_kb' || 
      doc.status === 'parsing_kb'
    );
    
    if (processingDocs.length === 0) {
      return;
    }

    const intervalId = setInterval(() => {
      // 静默刷新文档列表以获取最新状态
      loadDocuments(false);
    }, 2000); // 每2秒检查一次

    return () => clearInterval(intervalId);
  }, [documents, loadDocuments]);

  // 重试知识库解析
  const handleRetryKnowledgeBaseParsing = async (documentId: number) => {
    try {
      const response = await documentService.retryKnowledgeBaseParsing(documentId);
      if (response.success) {
        // 重试成功，立即刷新文档状态
        loadDocuments(false);
      } else {
        alert(response.error || '重试失败');
      }
    } catch (err) {
      alert('重试失败，请稍后重试');
      console.error('Retry knowledge base parsing error:', err);
    }
  };

  // 删除文档
  const handleDeleteDocument = async (id: number) => {
    // 确认删除
    if (!window.confirm('确定要删除这个文档吗？此操作不可恢复。')) {
      return;
    }

    try {
      // 乐观更新：立即从UI中移除文档
      const docToDelete = documents.find(doc => doc.id === id);
      if (!docToDelete) return;

      const updatedDocuments = documents.filter(doc => doc.id !== id);
      updateDocuments(updatedDocuments);

      const response = await documentService.deleteDocument(id);
      if (response.success) {
        // 删除成功，通知父组件文档数据发生变化（不重新加载文档列表）
        if (onDocumentChange) {
          onDocumentChange();
        }
      } else {
        // 删除失败，恢复文档
        const restoredDocuments = [...updatedDocuments, docToDelete].sort((a, b) => a.id - b.id);
        updateDocuments(restoredDocuments);
        alert(response.error || '删除文档失败');
      }
    } catch (err) {
      // 网络错误，恢复文档
      const docToDelete = documents.find(doc => doc.id === id);
      if (docToDelete) {
        const restoredDocuments = [...documents.filter(doc => doc.id !== id), docToDelete].sort((a, b) => a.id - b.id);
        updateDocuments(restoredDocuments);
      }
      alert('删除文档失败，请稍后重试');
      console.error('Delete document error:', err);
    }
  };

  // 下载文档
  const handleDownloadDocument = async (id: number, name: string, type: string) => {
    try {
      const response = await documentService.downloadDocument(id);
      if (response.success && response.data) {
        // 创建下载链接
        const url = window.URL.createObjectURL(response.data);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;

        // 确保文件名包含正确的扩展名
        let filename = name;
        if (filename && !filename.includes('.')) {
          // 根据文件类型添加扩展名
          switch (type) {
            case 'pdf':
              filename += '.pdf';
              break;
            case 'excel':
              filename += '.xlsx';
              break;
            case 'word':
              filename += '.docx';
              break;
            case 'image':
              filename += '.jpg';
              break;
            case 'markdown':
              filename += '.md';
              break;
            default:
              // 保持原文件名
              break;
          }
        }

        a.download = filename;
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

  // 预览文档
  const handlePreviewDocument = (id: number, name: string) => {
    setPreviewDocument({ id, name });
  };

  // 关闭预览
  const handleClosePreview = () => {
    setPreviewDocument(null);
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
      case 'markdown':
        return 'ri-markdown-line text-orange-600';
      default:
        return 'ri-file-line text-gray-600';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'uploading':
        return 'bg-yellow-100 text-yellow-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'uploading_to_kb':
        return 'bg-purple-100 text-purple-800';
      case 'parsing_kb':
        return 'bg-indigo-100 text-indigo-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'kb_parse_failed':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '知识库解析成功';
      case 'uploading':
        return '本地上传中';
      case 'processing':
        return '处理文件中';
      case 'uploading_to_kb':
        return '上传知识库中';
      case 'parsing_kb':
        return '知识库解析中';
      case 'failed':
        return '失败';
      case 'kb_parse_failed':
        return '知识库解析失败';
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
              <div className="space-y-4 animate-fadeIn">
                {filteredDocuments.map((doc) => (
            <div key={doc.id} className="flex items-center space-x-4 p-4 border border-gray-100 rounded-lg hover:bg-gray-50 transition-all duration-200 ease-in-out transform hover:scale-[1.01] hover:shadow-md">
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
                
                {(doc.status === 'uploading' || doc.status === 'processing' || doc.status === 'uploading_to_kb' || doc.status === 'parsing_kb') && (
                  <div className="mt-2 flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-blue-600"></div>
                    <span className="text-xs text-gray-600">
                      {doc.status === 'uploading' && '正在上传...'}
                      {doc.status === 'processing' && '正在处理文件...'}
                      {doc.status === 'uploading_to_kb' && '正在上传到知识库...'}
                      {doc.status === 'parsing_kb' && '正在知识库中解析...'}
                    </span>
                  </div>
                )}
                
                {doc.status === 'kb_parse_failed' && (
                  <div className="mt-2 flex items-center space-x-2">
                    <button
                      onClick={() => handleRetryKnowledgeBaseParsing(doc.id)}
                      className="text-xs bg-orange-600 text-white px-2 py-1 rounded hover:bg-orange-700 transition-colors"
                    >
                      重试解析
                    </button>
                  </div>
                )}
              </div>
              
              <div className="flex items-center space-x-3">
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(doc.status)}`}>
                  {getStatusText(doc.status)}
                </span>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleDownloadDocument(doc.id, doc.name, doc.type)}
                    className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-200 transition-all duration-200 btn-hover-scale"
                    title="下载原始文档"
                  >
                    <i className="ri-download-line text-gray-600"></i>
                  </button>
                  <button
                    onClick={() => handlePreviewDocument(doc.id, doc.name)}
                    className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-blue-100 transition-all duration-200 btn-hover-scale"
                    title="预览文档"
                    disabled={doc.status !== 'completed'}
                  >
                    <i className={`ri-eye-line ${doc.status === 'completed' ? 'text-blue-600' : 'text-gray-400'}`}></i>
                  </button>
                  <button
                    onClick={() => handleDeleteDocument(doc.id)}
                    className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-red-100 transition-all duration-200 btn-hover-scale"
                    title="删除文档"
                  >
                    <i className="ri-delete-bin-line text-red-600"></i>
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

      {/* 文档预览模态框 */}
      {previewDocument && (
        <DocumentPreview
          documentId={previewDocument.id}
          documentName={previewDocument.name}
          isOpen={!!previewDocument}
          onClose={handleClosePreview}
        />
      )}
    </div>
  );
}
