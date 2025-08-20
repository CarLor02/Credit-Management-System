
'use client';

import { useState, useEffect } from 'react';
import { documentService } from '@/services/documentService';
import { Project } from '@/services/projectService';
import Portal from '@/components/Portal';

interface DocumentUploadProps {
  selectedProject: string;
  selectedProjectData?: Project;  // 直接传递项目数据
  onSuccess?: () => void;
}

export default function DocumentUpload({ selectedProject, selectedProjectData, onSuccess }: DocumentUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);

  // ESC键关闭弹窗
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showConfirmModal && !isUploading) {
        setShowConfirmModal(false);
        setPendingFiles([]);
      }
    };

    if (showConfirmModal) {
      document.addEventListener('keydown', handleEscape);
      // 防止页面滚动
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [showConfirmModal, isUploading]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    showUploadConfirmation(files);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      showUploadConfirmation(files);
      // 重置文件input，允许选择相同文件
      e.target.value = '';
    }
  };

  const showUploadConfirmation = (files: File[]) => {
    if (!selectedProject) {
      alert('请先选择关联项目');
      return;
    }

    // 检查文件格式，拦截doc/docx格式
    for (const file of files) {
      const extension = file.name.split('.').pop()?.toLowerCase();
      if (extension === 'doc' || extension === 'docx') {
        setError(`文件 ${file.name}: 暂不支持该格式，请转化成PDF格式上传`);
        return;
      }
    }

    setError(null);
    setPendingFiles(files);
    setShowConfirmModal(true);
  };

  const handleConfirmUpload = async () => {
    setIsUploading(true);
    setShowConfirmModal(false);

    try {
      // 检查是否有选中的项目
      if (!selectedProjectData) {
        throw new Error('请先选择项目');
      }

      // 上传每个文件
      for (const file of pendingFiles) {
        // 确定文件类型
        const extension = file.name.split('.').pop()?.toLowerCase();
        let fileType: 'pdf' | 'excel' | 'word' | 'image' | 'markdown' = 'pdf';

        if (extension === 'xlsx' || extension === 'xls') {
          fileType = 'excel';
        } else if (extension === 'jpg' || extension === 'jpeg' || extension === 'png') {
          fileType = 'image';
        } else if (extension === 'md') {
          fileType = 'markdown';
        }

        // 上传文件，立即触发列表刷新显示"本地上传中"状态
        const response = await documentService.uploadDocument({
          name: file.name,
          project: selectedProjectData.name,
          project_id: selectedProjectData.id,  // 添加项目ID
          type: fileType,
          file: file
        });

        if (!response.success) {
          // 处理不同类型的错误响应
          const errorMessage = response.error || response.message || `上传文件 ${file.name} 失败`;
          throw new Error(errorMessage);
        }

        // 立即触发列表刷新，显示"本地上传中"状态
        if (onSuccess) {
          onSuccess();
        }
      }

      // 所有文件上传完成后，最终刷新文档列表
      if (onSuccess) {
        onSuccess();
      }

      // 上传完成，重置状态（保持项目选择）
      setIsUploading(false);
      setPendingFiles([]);

    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败');
      setIsUploading(false);
      setPendingFiles([]);
      console.error('Upload error:', err);
    }
  };

  const handleCancelUpload = () => {
    setShowConfirmModal(false);
    setPendingFiles([]);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();

    switch (extension) {
      case 'pdf':
        return { icon: 'ri-file-pdf-line', color: 'text-red-600', bg: 'bg-red-100' };
      case 'xlsx':
      case 'xls':
        return { icon: 'ri-file-excel-line', color: 'text-green-600', bg: 'bg-green-100' };
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
      case 'bmp':
      case 'webp':
        return { icon: 'ri-image-line', color: 'text-purple-600', bg: 'bg-purple-100' };
      case 'md':
      case 'markdown':
        return { icon: 'ri-markdown-line', color: 'text-blue-600', bg: 'bg-blue-100' };
      case 'txt':
        return { icon: 'ri-file-text-line', color: 'text-gray-600', bg: 'bg-gray-100' };
      case 'doc':
      case 'docx':
        return { icon: 'ri-file-word-line', color: 'text-blue-600', bg: 'bg-blue-100' };
      default:
        return { icon: 'ri-file-line', color: 'text-gray-600', bg: 'bg-gray-100' };
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">文档上传</h2>
        
        <div className="space-y-4">
          {/* 错误提示 */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <div className="flex items-center">
                <i className="ri-error-warning-line text-red-600 mr-2"></i>
                <span className="text-red-800 text-sm">{error}</span>
              </div>
            </div>
          )}

          {!selectedProject ? (
            <div className="text-center py-8 text-gray-500">
              <i className="ri-folder-add-line text-3xl mb-2"></i>
              <p>请先在上方选择一个项目</p>
            </div>
          ) : (
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                isDragOver
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="w-12 h-12 mx-auto mb-4 flex items-center justify-center rounded-full bg-gray-100">
                <i className="ri-upload-cloud-2-line text-2xl text-gray-600"></i>
              </div>
              <p className="text-gray-600 mb-2">拖拽文件到此处或点击上传</p>
              <p className="text-sm text-gray-500 mb-4">
                支持 PDF、XLS、XLSX、MD 格式
              </p>
              <input
                type="file"
                multiple
                accept=".pdf,.xls,.xlsx,.txt,.jpg,.jpeg,.png,.md"
                onChange={handleFileSelect}
                className="hidden"
                id="file-upload"
                disabled={isUploading}
              />
              <label
                htmlFor="file-upload"
                className={`inline-flex items-center px-4 py-2 rounded-lg transition-colors cursor-pointer whitespace-nowrap ${
                  isUploading
                    ? 'bg-gray-400 text-white cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                <i className="ri-folder-open-line mr-2"></i>
                {isUploading ? '上传中...' : '选择文件'}
              </label>
            </div>
          )}
        </div>
      </div>

      {/* 上传确认弹窗 */}
      {showConfirmModal && (
        <Portal>
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-[9999] flex items-center justify-center p-4"
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              zIndex: 9999
            }}
            onClick={(e) => {
              // 点击遮罩层关闭弹窗
              if (e.target === e.currentTarget && !isUploading) {
                handleCancelUpload();
              }
            }}
          >
            <div
              className="bg-white rounded-xl p-6 max-w-lg w-full shadow-xl animate-fadeIn"
              style={{
                maxHeight: '90vh',
                overflow: 'auto'
              }}
              onClick={(e) => e.stopPropagation()} // 防止点击弹窗内容时关闭
            >
              <div className="flex items-center justify-center w-12 h-12 mx-auto bg-blue-100 rounded-full mb-4">
                <i className="ri-upload-cloud-2-line text-blue-600 text-xl"></i>
              </div>
              <h3 className="text-lg font-medium text-gray-800 text-center mb-2">确认上传文件</h3>
              <p className="text-gray-600 text-center mb-4">
                您选择了 <span className="font-medium">{pendingFiles.length}</span> 个文件，确认上传到项目 &ldquo;<span className="font-medium">{selectedProjectData?.name}</span>&rdquo; 吗？
              </p>

              {/* 文件列表 */}
              <div className="max-h-60 overflow-y-auto mb-6 border border-gray-200 rounded-lg">
                {pendingFiles.map((file, index) => {
                  const fileIcon = getFileIcon(file.name);
                  return (
                    <div key={index} className="flex items-center justify-between p-3 border-b border-gray-100 last:border-b-0">
                      <div className="flex items-center space-x-3 flex-1 min-w-0">
                        <div className={`w-8 h-8 flex items-center justify-center rounded ${fileIcon.bg}`}>
                          <i className={`${fileIcon.icon} ${fileIcon.color}`}></i>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-800 truncate" title={file.name}>
                            {file.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {formatFileSize(file.size)}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={handleCancelUpload}
                  disabled={isUploading}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  取消
                </button>
                <button
                  onClick={handleConfirmUpload}
                  disabled={isUploading}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {isUploading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                      上传中...
                    </>
                  ) : (
                    <>
                      <i className="ri-upload-cloud-2-line mr-2"></i>
                      确认上传
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </Portal>
      )}
    </div>
  );
}
