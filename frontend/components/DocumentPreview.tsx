'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { documentService } from '../services/documentService';
import { parseApiError } from '../utils/errorMessages';

// 动态导入 Markdown 预览组件，避免 SSR 错误
const MarkdownPreview = dynamic(() => import('@uiw/react-markdown-preview'), { ssr: false });

interface DocumentPreviewProps {
  documentId: number;
  documentName: string;
  isOpen: boolean;
  onClose: () => void;
}

interface PreviewData {
  content: string;
  document_name: string;
  original_filename: string;
  display_name?: string;  // 添加用于显示的文件名
  file_type: string;
  processed_at: string | null;
}

export default function DocumentPreview({ documentId, documentName, isOpen, onClose }: DocumentPreviewProps) {
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 加载预览内容
  const loadPreviewContent = async () => {
    if (!documentId) return;

    try {
      setLoading(true);
      setError(null);

      const response = await documentService.previewDocument(documentId);
      
      if (response.success && response.data) {
        setPreviewData(response.data);
      } else {
        setError(response.error || '加载预览内容失败');
      }
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setLoading(false);
    }
  };

  // 当模态框打开时加载内容
  useEffect(() => {
    if (isOpen && documentId) {
      loadPreviewContent();
    }
  }, [isOpen, documentId]); // eslint-disable-line react-hooks/exhaustive-deps

  // 下载处理后的文件
  const handleDownloadProcessed = async () => {
    try {
      const response = await documentService.downloadProcessedDocument(documentId);
      if (response.success && response.data) {
        // 创建下载链接
        const url = window.URL.createObjectURL(response.data);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;

        // 使用后端提供的display_name，确保包含中文字符和正确扩展名
        let filename = previewData?.display_name || previewData?.document_name || documentName || 'document';

        // 如果display_name不可用，手动构建文件名
        if (!previewData?.display_name) {
          filename = previewData?.document_name || documentName || 'document';
          // 确保文件名包含扩展名
          if (filename && !filename.includes('.')) {
            const fileType = previewData?.file_type;
            switch (fileType) {
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
                break;
            }
          }
        }

        const baseName = filename.includes('.') ? filename.substring(0, filename.lastIndexOf('.')) : filename;
        a.download = `${baseName}_processed.md`;

        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert(response.error || '下载失败');
      }
    } catch (err) {
      alert(parseApiError(err));
    }
  };

  // 下载原始文件
  const handleDownloadOriginal = async () => {
    try {
      const response = await documentService.downloadDocument(documentId);
      if (response.success && response.data) {
        // 创建下载链接
        const url = window.URL.createObjectURL(response.data);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;

        // 使用后端提供的display_name，确保包含中文字符和正确扩展名
        let filename = previewData?.display_name || previewData?.document_name || documentName || 'document';

        // 如果display_name不可用，手动构建文件名
        if (!previewData?.display_name) {
          filename = previewData?.document_name || documentName || 'document';
          // 确保文件名包含扩展名
          if (filename && !filename.includes('.')) {
            const fileType = previewData?.file_type;
            switch (fileType) {
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
                break;
            }
          }
        }

        a.download = filename;

        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert(response.error || '下载失败');
      }
    } catch (err) {
      alert(parseApiError(err));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-start justify-center z-50 p-4 pt-8">
      <div className="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[85vh] flex flex-col overflow-hidden border border-gray-200 mt-4">
        {/* 头部 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-semibold text-gray-800 truncate">
              📄 {documentName}
            </h2>
            {previewData && (
              <p className="text-sm text-gray-600 mt-1">
                原始文件: {previewData.original_filename} • 类型: {previewData.file_type}
                {previewData.processed_at && (
                  <span> • 处理时间: {new Date(previewData.processed_at).toLocaleString('zh-CN')}</span>
                )}
              </p>
            )}
          </div>
          
          <div className="flex items-center space-x-3 ml-4">
            {/* 下载按钮 */}
            {previewData && (
              <>
                <button
                  onClick={handleDownloadProcessed}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  title="下载处理后的Markdown文件"
                >
                  <i className="ri-download-line"></i>
                  <span>下载MD</span>
                </button>
                <button
                  onClick={handleDownloadOriginal}
                  className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                  title="下载原始文件"
                >
                  <i className="ri-file-download-line"></i>
                  <span>下载原文件</span>
                </button>
              </>
            )}
            
            {/* 关闭按钮 */}
            <button
              onClick={onClose}
              className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors"
              title="关闭预览"
            >
              <i className="ri-close-line text-xl text-gray-600"></i>
            </button>
          </div>
        </div>

        {/* 内容区域 */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {loading && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">正在加载预览内容...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <i className="ri-error-warning-line text-4xl text-red-500 mb-4"></i>
                <h3 className="text-lg font-medium text-gray-800 mb-2">预览失败</h3>
                <p className="text-gray-600 mb-4">{error}</p>
                <button
                  onClick={loadPreviewContent}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  重试
                </button>
              </div>
            </div>
          )}

          {previewData && !loading && !error && (
            <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
              <div className="max-w-none prose prose-lg prose-slate" data-color-mode="light">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                  <div className="bg-gradient-to-r from-gray-50 to-blue-50 px-4 py-2 border-b border-gray-200">
                    <div className="flex items-center space-x-2">
                      <i className="ri-file-text-line text-blue-600"></i>
                      <span className="text-sm font-medium text-gray-700">文档预览</span>
                      <span className="text-xs text-gray-500">• Markdown格式</span>
                    </div>
                  </div>
                  <div className="p-6">
                    <MarkdownPreview
                      source={previewData.content || '# 文档内容为空\n\n此文档没有可预览的内容。'}
                      style={{
                        backgroundColor: 'transparent',
                        color: '#374151',
                        lineHeight: '1.7',
                        fontSize: '16px'
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 底部提示 */}
        {previewData && !loading && !error && (
          <div className="px-6 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 border-t border-gray-200 text-sm text-gray-600">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <i className="ri-information-line text-blue-500"></i>
                <span>
                  这是经过AI处理后的Markdown格式预览，可能与原始文件格式有所不同
                </span>
              </div>
              <span className="text-xs text-gray-500">
                文档ID: {documentId}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
