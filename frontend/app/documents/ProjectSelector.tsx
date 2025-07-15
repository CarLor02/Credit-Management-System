'use client';

import { useState, useEffect, useImperativeHandle, forwardRef } from 'react';
import { projectService } from '@/services/projectService';
import { Project } from '@/data/mockData';

interface ProjectSelectorProps {
  selectedProject: string;
  onProjectChange: (projectId: string) => void;
}

export interface ProjectSelectorRef {
  refreshProjects: () => void;
}

const ProjectSelector = forwardRef<ProjectSelectorRef, ProjectSelectorProps>(({ selectedProject, onProjectChange }, ref) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 加载项目列表
  const loadProjects = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      const response = await projectService.getProjects();
      if (response.success && response.data && Array.isArray(response.data)) {
        setProjects(response.data);
        setError(null);
      } else {
        setProjects([]);
        setError('加载项目列表失败');
      }
    } catch (err) {
      setProjects([]);
      setError('网络错误，请稍后重试');
      console.error('Load projects error:', err);
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  // 暴露刷新函数给父组件（静默刷新，不显示loading）
  useImperativeHandle(ref, () => ({
    refreshProjects: () => loadProjects(false)
  }));

  // 加载项目列表
  useEffect(() => {
    loadProjects();
  }, []);

  const selectedProjectData = projects.find(p => p.id.toString() === selectedProject);

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">项目选择</h2>
      
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <div className="flex items-center">
            <i className="ri-error-warning-line text-red-600 mr-2"></i>
            <span className="text-red-800 text-sm">{error}</span>
          </div>
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            当前项目 *
          </label>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              <span className="ml-2 text-gray-600">加载中...</span>
            </div>
          ) : (
            <select
              value={selectedProject}
              onChange={(e) => onProjectChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">请选择项目</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          )}
        </div>

        {selectedProjectData && (
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <i className="ri-folder-line text-blue-600"></i>
              </div>
              <div>
                <h4 className="font-medium text-gray-800">{selectedProjectData.name}</h4>
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <span>类型: {selectedProjectData.type === 'enterprise' ? '企业' : '个人'}</span>
                  <span>•</span>
                  <span>文档: {selectedProjectData.documents} 个</span>
                  <span>•</span>
                  <div className="flex items-center space-x-1">
                    <span>状态:</span>
                    {selectedProjectData.status === 'processing' && (
                      <div className="animate-spin rounded-full h-3 w-3 border-2 border-gray-300 border-t-blue-600"></div>
                    )}
                    <span>
                      {selectedProjectData.status === 'processing' ? '处理中' : 
                       selectedProjectData.status === 'completed' ? '已完成' : 
                       selectedProjectData.status === 'collecting' ? '收集中' : '未知'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {!selectedProject && (
          <div className="text-center py-8 text-gray-500">
            <i className="ri-folder-add-line text-3xl mb-2"></i>
            <p>请选择一个项目以查看和上传文档</p>
          </div>
        )}
      </div>
    </div>
  );
});

ProjectSelector.displayName = 'ProjectSelector';

export default ProjectSelector;
