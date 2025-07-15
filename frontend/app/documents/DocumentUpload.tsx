
'use client';

import { useState, useEffect } from 'react';
import { documentService } from '@/services/documentService';
import { projectService } from '@/services/projectService';
import { Project } from '@/data/mockData';

interface DocumentUploadProps {
  selectedProject: string;
  onSuccess?: () => void;
}

export default function DocumentUpload({ selectedProject, onSuccess }: DocumentUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);

  // 加载项目列表
  useEffect(() => {
    const loadProjects = async () => {
      try {
        const response = await projectService.getProjects();
        if (response.success && response.data && Array.isArray(response.data)) {
          setProjects(response.data);
        } else {
          setProjects([]); // 确保projects始终是数组
        }
      } catch (err) {
        setProjects([]); // 确保projects始终是数组
        console.error('Load projects error:', err);
      }
    };

    loadProjects();
  }, []);

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
      // 获取选中的项目信息
      const selectedProjectData = Array.isArray(projects)
        ? projects.find(p => p.id.toString() === selectedProject)
        : undefined;
      if (!selectedProjectData) {
        throw new Error('未找到选中的项目');
      }

      // 上传每个文件
      for (const file of files) {
        // 确定文件类型
        let fileType: 'pdf' | 'excel' | 'word' | 'image' = 'pdf';
        const extension = file.name.split('.').pop()?.toLowerCase();

        if (extension === 'xlsx' || extension === 'xls') {
          fileType = 'excel';
        } else if (extension === 'docx' || extension === 'doc') {
          fileType = 'word';
        } else if (extension === 'jpg' || extension === 'jpeg' || extension === 'png') {
          fileType = 'image';
        }

        // 上传文件，立即触发列表刷新显示"上传中"状态
        const response = await documentService.uploadDocument({
          name: file.name,
          project: selectedProjectData.name,
          type: fileType,
          file: file
        });

        if (!response.success) {
          throw new Error(response.error || `上传文件 ${file.name} 失败`);
        }
      }

      // 所有文件上传完成后，一次性刷新文档列表和项目选择器
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
                支持 PDF、DOC、DOCX、XLS、XLSX、TXT 格式
              </p>
              <input
                type="file"
                multiple
                accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.jpg,.jpeg,.png"
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

      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">知识库构建</h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <i className="ri-database-2-line text-blue-600"></i>
              </div>
              <div>
                <h4 className="font-medium text-gray-800">自动构建</h4>
                <p className="text-sm text-gray-600">文档上传后自动解析并构建知识库</p>
              </div>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="auto-build"
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                defaultChecked
              />
              <label htmlFor="auto-build" className="ml-2 text-sm text-gray-700">
                启用
              </label>
            </div>
          </div>

          <button className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center whitespace-nowrap">
            <i className="ri-refresh-line mr-2"></i>
            手动重建知识库
          </button>
        </div>
      </div>
    </div>
  );
}
