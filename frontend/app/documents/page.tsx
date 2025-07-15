
'use client';

import { useState, useEffect, useRef } from 'react';
import Header from '@/components/Header';
import DocumentUpload from './DocumentUpload';
import DocumentList from './DocumentList';
import ProjectSelector, { ProjectSelectorRef } from './ProjectSelector';

export default function DocumentsPage() {
  const [activeTab, setActiveTab] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [selectedProject, setSelectedProject] = useState('');
  const projectSelectorRef = useRef<ProjectSelectorRef>(null);

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
      
      <main className="p-6">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-800 mb-2">文档管理</h1>
            <p className="text-gray-600">管理征信项目相关文档和构建知识库</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div>
            <ProjectSelector 
              ref={projectSelectorRef}
              selectedProject={selectedProject}
              onProjectChange={setSelectedProject}
            />
            <DocumentUpload 
              selectedProject={selectedProject}
              onSuccess={refreshDocuments} 
            />
          </div>
          
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 mb-6">
              <div className="p-6 border-b border-gray-100">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
                  <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
                    {[
                      { key: 'all', label: '全部文档' },
                      { key: 'uploading', label: '上传中' },
                      { key: 'processing', label: '处理中' },
                      { key: 'completed', label: '已完成' },
                      { key: 'failed', label: '失败' }
                    ].map((tab) => (
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
                      </button>
                    ))}
                  </div>
                  
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
            
            <DocumentList
              activeTab={activeTab}
              searchQuery={searchQuery}
              selectedProject={selectedProject}
              refreshTrigger={refreshTrigger}
              onDocumentChange={handleDocumentChange}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
