'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Header from '@/components/Header';
import DocumentUpload from './DocumentUpload';
import DocumentList from './DocumentList';
import ProjectSelector, { ProjectSelectorRef } from './ProjectSelector';

// 内部组件，使用 useSearchParams
function DocumentsContent() {

  const [searchQuery, setSearchQuery] = useState('');
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [selectedProject, setSelectedProject] = useState('');
  const [selectedProjectData, setSelectedProjectData] = useState<any>(null);
  const [documentListHeight, setDocumentListHeight] = useState(400);
  const [isProjectSelectorLoaded, setIsProjectSelectorLoaded] = useState(false); // 新增状态跟踪项目选择器加载完成
  const projectSelectorRef = useRef<ProjectSelectorRef>(null);
  const leftPanelRef = useRef<HTMLDivElement>(null);
  const searchParams = useSearchParams();

  // 从URL参数获取项目ID并自动选择
  useEffect(() => {
    const projectId = searchParams.get('project_id');
    if (projectId) {
      setSelectedProject(projectId);
      // 项目数据会在ProjectSelector加载完成后通过onProjectChange回调设置
    }
  }, [searchParams]);

  // 动态计算文档列表高度，使其底边与左侧面板对齐
  useEffect(() => {
    const calculateHeight = () => {
      if (leftPanelRef.current) {
        const leftPanelHeight = leftPanelRef.current.offsetHeight;
        // 减去搜索栏的高度和间距 (约120px)
        const calculatedHeight = leftPanelHeight - 120;
        setDocumentListHeight(Math.max(400, Math.min(600, calculatedHeight)));
      }
    };

    // 初始计算
    calculateHeight();

    // 监听窗口大小变化
    window.addEventListener('resize', calculateHeight);

    // 延迟计算，确保DOM完全渲染
    const timer = setTimeout(calculateHeight, 100);

    return () => {
      window.removeEventListener('resize', calculateHeight);
      clearTimeout(timer);
    };
  }, [selectedProject, selectedProjectData]);

  // 刷新文档列表的函数
  const refreshDocuments = () => {
    setRefreshTrigger(prev => prev + 1);
    // 同时刷新项目选择器以更新文档数量
    if (projectSelectorRef.current) {
      projectSelectorRef.current.refreshProjects();
    }
  };

  // 文档发生变化时的回调（如删除文档）
  const handleDocumentChange = () => {
    // 刷新项目选择器以更新文档数量
    if (projectSelectorRef.current) {
      projectSelectorRef.current.refreshProjects();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="p-6 animate-fadeIn">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-800 mb-2">文档管理</h1>
            <p className="text-gray-600">管理征信项目相关文档和构建知识库</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* 左侧面板 */}
          <div className="space-y-6" ref={leftPanelRef}>
            <ProjectSelector
              ref={projectSelectorRef}
              selectedProject={selectedProject}
              onProjectChange={(projectId, projectData) => {
                setSelectedProject(projectId);
                setSelectedProjectData(projectData || null);
                // 标记项目选择器已加载完成
                setIsProjectSelectorLoaded(true);
              }}
            />
            <DocumentUpload
              selectedProject={selectedProject}
              selectedProjectData={selectedProjectData}
              onSuccess={refreshDocuments}
            />
          </div>

          {/* 右侧面板 */}
          <div className="lg:col-span-2">
            {/* 搜索栏 */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 mb-6">
              <div className="p-6 border-b border-gray-100">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
                  {/* 只保留搜索框，移除状态筛选 */}
                  <div className="relative">
                    <i className="ri-search-line absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
                    <input
                      type="text"
                      placeholder="搜索文档..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-full sm:w-64"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* 文档列表 - 动态高度滑窗 */}
            <div style={{ height: `${documentListHeight}px` }}>
              {/* 只有当项目选择器加载完成时才渲染文档列表 */}
              {isProjectSelectorLoaded && (
                <DocumentList
                  activeTab={''} // 传空字符串，后端不做状态筛选
                  searchQuery={searchQuery}
                  selectedProject={selectedProject}
                  refreshTrigger={refreshTrigger}
                  onDocumentChange={handleDocumentChange}
                />
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

// 主导出组件，使用 Suspense 包装
export default function DocumentsPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>}>
      <DocumentsContent />
    </Suspense>
  );
}