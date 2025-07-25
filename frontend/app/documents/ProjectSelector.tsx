'use client';

import { useState, useEffect, useImperativeHandle, forwardRef } from 'react';
import { useRouter } from 'next/navigation';
import { projectService, Project } from '@/services/projectService';
import { knowledgeBaseService } from '@/services/knowledgeBaseService';

interface ProjectSelectorProps {
  selectedProject: string;
  onProjectChange: (projectId: string, projectData?: Project) => void;
}

export interface ProjectSelectorRef {
  refreshProjects: () => void;
}

const ProjectSelector = forwardRef<ProjectSelectorRef, ProjectSelectorProps>(({ selectedProject, onProjectChange }, ref) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRebuilding, setIsRebuilding] = useState(false);
  const router = useRouter();

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

  // 当外部传入的selectedProject发生变化时，确保组件状态同步
  useEffect(() => {
    // 当selectedProject变化且projects已加载时，通知父组件项目数据
    if (selectedProject && projects.length > 0) {
      const projectData = projects.find(p => p.id.toString() === selectedProject);
      if (projectData) {
        // 通知父组件当前选中的项目数据
        onProjectChange(selectedProject, projectData);
      }
    }
  }, [selectedProject, projects, onProjectChange]);

  const selectedProjectData = projects.find(p => p.id.toString() === selectedProject);

  // 重新构建知识库
  const handleRebuildKnowledgeBase = async () => {
    if (!selectedProject || !selectedProjectData) {
      alert('请先选择项目');
      return;
    }

    if (confirm(`确定要重新构建项目"${selectedProjectData.name}"的知识库吗？\n\n此操作将删除现有知识库并重新处理所有文档，可能需要一些时间。`)) {
      setIsRebuilding(true);
      try {
        // 调用重新构建知识库的API
        const response = await knowledgeBaseService.rebuildKnowledgeBase(selectedProject);

        if (response.success) {
          alert(response.message || '知识库重建任务已启动，请稍后查看处理结果');

          // 可选：刷新项目列表或触发文档列表刷新
          if (typeof window !== 'undefined') {
            // 发送自定义事件通知文档列表刷新
            window.dispatchEvent(new CustomEvent('knowledgeBaseRebuilt', {
              detail: { projectId: selectedProject }
            }));
          }
        } else {
          alert(response.error || '重建知识库失败，请稍后重试');
        }
      } catch (error) {
        console.error('重建知识库失败:', error);
        alert('重建知识库失败，请稍后重试');
      } finally {
        setIsRebuilding(false);
      }
    }
  };

  // 前往生成报告（项目详情页）
  const handleGoToReport = () => {
    if (!selectedProject) {
      alert('请先选择项目');
      return;
    }
    router.push(`/projects/${selectedProject}`);
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
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
              onChange={(e) => {
                const projectId = e.target.value;
                const projectData = projects.find(p => p.id.toString() === projectId);
                onProjectChange(projectId, projectData);
              }}
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
          <div className="space-y-4">
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

            {/* 功能按钮 */}
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={handleRebuildKnowledgeBase}
                disabled={isRebuilding}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center ${
                  isRebuilding
                    ? 'bg-gray-400 text-white cursor-not-allowed'
                    : 'bg-orange-600 text-white hover:bg-orange-700'
                }`}
              >
                {isRebuilding ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                    重建中...
                  </>
                ) : (
                  <>
                    <i className="ri-refresh-line mr-2"></i>
                    重新构建知识库
                  </>
                )}
              </button>

              <button
                onClick={handleGoToReport}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium flex items-center justify-center"
              >
                <i className="ri-file-text-line mr-2"></i>
                前往生成报告
              </button>
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
