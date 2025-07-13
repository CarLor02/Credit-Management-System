
'use client';

import { useState, useEffect } from 'react';
import Header from '@/components/Header';
import ProjectCard from './ProjectCard';
import CreateProjectModal from './CreateProjectModal';
import { projectService } from '@/services/projectService';
import { Project } from '@/data/mockData';

export default function ProjectsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [projects, setProjects] = useState<Project[]>([]);
  const [allProjects, setAllProjects] = useState<Project[]>([]); // 存储所有项目，用于计算标签数量
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 加载所有项目数据（用于计算标签数量）
  const loadAllProjects = async () => {
    try {
      const response = await projectService.getProjects({}); // 不传任何过滤参数
      if (response.success && response.data && Array.isArray(response.data)) {
        setAllProjects(response.data);
      }
    } catch (err) {
      console.error('Load all projects error:', err);
    }
  };

  // 加载项目数据
  const loadProjects = async () => {
    try {
      setLoading(true);
      setError(null);

      // 构建查询参数，过滤掉空值
      const queryParams: any = {};

      // 搜索参数
      if (searchQuery && searchQuery.trim()) {
        queryParams.search = searchQuery.trim();
      }

      // 根据activeTab设置过滤条件
      switch (activeTab) {
        case 'enterprise':
          queryParams.type = 'enterprise';
          break;
        case 'individual':
          queryParams.type = 'individual';
          break;
        case 'processing':
          queryParams.status = 'processing';
          break;
        case 'all':
        default:
          // 不设置任何过滤条件，显示所有项目
          break;
      }

      const response = await projectService.getProjects(queryParams);

      if (response.success && response.data && Array.isArray(response.data)) {
        setProjects(response.data);
      } else {
        setError(response.error || '加载项目失败');
        setProjects([]); // 确保projects始终是数组
      }
    } catch (err) {
      setError('网络错误，请稍后重试');
      setProjects([]); // 确保projects始终是数组
      console.error('Load projects error:', err);
    } finally {
      setLoading(false);
    }
  };

  // 初始加载时获取所有项目
  useEffect(() => {
    loadAllProjects();
  }, []);

  // 搜索/筛选变化时重新加载过滤后的项目
  useEffect(() => {
    loadProjects();
  }, [activeTab, searchQuery]);

  // 删除项目
  const handleDeleteProject = async (id: number) => {
    try {
      const response = await projectService.deleteProject(id);
      if (response.success) {
        // 重新加载项目列表
        loadProjects();
      } else {
        alert(response.error || '删除项目失败');
      }
    } catch (err) {
      alert('删除项目失败，请稍后重试');
      console.error('Delete project error:', err);
    }
  };

  // 由于已经在API层面进行了过滤，这里直接使用projects
  // 确保filteredProjects始终是数组
  const filteredProjects = Array.isArray(projects) ? projects : [];

  // 计算各标签的项目数量（基于所有项目）
  const getTabCount = (tabKey: string) => {
    if (!Array.isArray(allProjects)) return 0;

    switch (tabKey) {
      case 'all':
        return allProjects.length;
      case 'enterprise':
        return allProjects.filter(p => p.type === 'enterprise').length;
      case 'individual':
        return allProjects.filter(p => p.type === 'individual').length;
      case 'processing':
        return allProjects.filter(p => p.status === 'processing').length;
      default:
        return 0;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="p-6">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-800 mb-2">征信项目管理</h1>
            <p className="text-gray-600">管理企业和个人征信项目</p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center whitespace-nowrap"
          >
            <i className="ri-add-line mr-2"></i>
            新建项目
          </button>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 mb-6">
          <div className="p-6 border-b border-gray-100">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
              <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
                {[
                  { key: 'all', label: '全部' },
                  { key: 'enterprise', label: '企业' },
                  { key: 'individual', label: '个人' },
                  { key: 'processing', label: '处理中' }
                ].map((tab) => {
                  const count = getTabCount(tab.key);
                  return (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key)}
                      className={`px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap ${
                        activeTab === tab.key
                          ? 'bg-white text-blue-600 shadow-sm'
                          : 'text-gray-600 hover:text-gray-800'
                      }`}
                    >
                      {tab.label}
                      {!loading && (
                        <span className={`ml-1 text-xs ${
                          activeTab === tab.key ? 'text-blue-500' : 'text-gray-500'
                        }`}>
                          ({count})
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
              
              <div className="relative">
                <i className="ri-search-line absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
                <input
                  type="text"
                  placeholder="搜索项目..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-full sm:w-64"
                />
              </div>
            </div>
          </div>
        </div>



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
                onClick={loadProjects}
                className="ml-auto text-red-600 hover:text-red-800 underline"
              >
                重试
              </button>
            </div>
          </div>
        )}

        {/* 项目列表 */}
        {!loading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProjects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onDelete={handleDeleteProject}
              />
            ))}
          </div>
        )}

        {/* 空状态 */}
        {!loading && !error && filteredProjects.length === 0 && (
          <div className="text-center py-12">
            <i className="ri-folder-open-line text-4xl text-gray-400 mb-4"></i>
            <h3 className="text-lg font-medium text-gray-800 mb-2">暂无项目</h3>
            <p className="text-gray-600 mb-4">开始创建您的第一个征信项目</p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors whitespace-nowrap"
            >
              新建项目
            </button>
          </div>
        )}
      </main>

      <CreateProjectModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={loadProjects}
      />
    </div>
  );
}
