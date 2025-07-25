
'use client';

import { useState } from 'react';
import { documentService } from '@/services/documentService';
import { Project } from '@/services/projectService';

interface DocumentUploadProps {
  selectedProject: string;
  selectedProjectData?: Project;  // 直接传递项目数据
  onSuccess?: () => void;
}

export default function DocumentUpload({ selectedProject, selectedProjectData, onSuccess }: DocumentUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    handleFiles(files);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      handleFiles(files);
      // 重置文件input，允许选择相同文件
      e.target.value = '';
    }
  };

  const handleFiles = async (files: File[]) => {
    if (!selectedProject) {
      alert('请先选择关联项目');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      // 检查是否有选中的项目
      if (!selectedProjectData) {
        throw new Error('请先选择项目');
      }

      // 上传每个文件
      for (const file of files) {
        // 确定文件类型
        let fileType: 'pdf' | 'excel' | 'word' | 'image' | 'markdown' = 'pdf';
        const extension = file.name.split('.').pop()?.toLowerCase();

        if (extension === 'xlsx' || extension === 'xls') {
          fileType = 'excel';
        } else if (extension === 'docx' || extension === 'doc') {
          fileType = 'word';
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
          throw new Error(response.error || `上传文件 ${file.name} 失败`);
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

    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败');
      setIsUploading(false);
      console.error('Upload error:', err);
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
                accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.jpg,.jpeg,.png,.md"
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


    </div>
  );
}
