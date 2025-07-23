'use client';

import React, { useState, useEffect, useRef } from 'react';
import { apiClient } from '../services/api';

interface ReportPreviewProps {
  isOpen: boolean;
  onClose: () => void;
  workflowRunId: string | null;
  companyName: string;
  projectId?: number;
  isGenerating?: boolean; // 新增：是否正在生成报告
  onReportDeleted?: () => void; // 新增：报告删除后的回调
}

interface WorkflowData {
  exists: boolean;
  events: string[];
  content: string;
  metadata: any;
  company_name: string;
  timestamp: number;
}

const ReportPreview: React.FC<ReportPreviewProps> = ({
  isOpen,
  onClose,
  workflowRunId,
  companyName,
  projectId,
  isGenerating = false,
  onReportDeleted
}) => {
  const [workflowData, setWorkflowData] = useState<WorkflowData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const streamingContentRef = useRef<HTMLDivElement>(null);

  // 获取项目报告内容
  const fetchProjectReport = async () => {
    if (!projectId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<{
        success: boolean;
        content: string;
        file_path: string;
        company_name: string;
      }>(`/projects/${projectId}/report`);

      if (response.success && response.data) {
        // 将报告数据转换为工作流数据格式，不显示假的事件信息
        setWorkflowData({
          exists: true,
          events: [], // 不显示假的事件信息
          content: response.data.content,
          metadata: { file_path: response.data.file_path },
          company_name: response.data.company_name,
          timestamp: Date.now() / 1000
        });
      } else {
        setError(response.error || '获取报告内容失败');
      }
    } catch (err) {
      console.error('获取报告内容失败:', err);
      setError('获取报告内容失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 获取工作流事件和内容
  const fetchWorkflowData = async () => {
    if (!workflowRunId) {
      console.log('fetchWorkflowData: workflowRunId为空，跳过请求');
      return;
    }

    console.log('fetchWorkflowData: 开始获取工作流数据，workflowRunId:', workflowRunId);
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<WorkflowData>(`/api/check_workflow_events/${workflowRunId}`);
      console.log('fetchWorkflowData: API响应:', response);

      if (response.success && response.data) {
        console.log('fetchWorkflowData: 成功获取数据，事件数量:', response.data.events?.length || 0);
        setWorkflowData(response.data);
      } else {
        console.log('fetchWorkflowData: API返回失败:', response.error);
        setError(response.error || '获取工作流数据失败');
      }
    } catch (err) {
      console.error('获取工作流数据失败:', err);
      setError('获取工作流数据失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 当弹窗打开时获取数据
  useEffect(() => {
    console.log('ReportPreview useEffect触发:', { isOpen, isGenerating, workflowRunId, projectId });

    if (isOpen) {
      if (isGenerating) {
        console.log('ReportPreview: 正在生成模式，workflowRunId:', workflowRunId);

        // 如果正在生成，初始化空的事件列表
        setWorkflowData({
          exists: true,
          events: [],
          content: "",
          metadata: {},
          company_name: companyName,
          timestamp: Date.now() / 1000
        });

        // 如果有workflowRunId，开始轮询获取实时进度
        if (workflowRunId) {
          console.log('ReportPreview: 开始轮询，workflowRunId:', workflowRunId);
          const interval = setInterval(fetchWorkflowData, 2000); // 更频繁的轮询
          return () => {
            console.log('ReportPreview: 清理轮询');
            clearInterval(interval);
          };
        } else {
          console.log('ReportPreview: workflowRunId为空，无法开始轮询');
        }
      } else if (projectId) {
        console.log('ReportPreview: 非生成模式，从项目API获取数据');
        // 如果不是生成中，优先从项目报告API获取数据
        fetchProjectReport();
      } else if (workflowRunId) {
        console.log('ReportPreview: 从工作流API获取数据');
        // 如果没有项目ID，则从工作流API获取数据
        fetchWorkflowData();
      }
    }
  }, [isOpen, projectId, workflowRunId, isGenerating]);

  // 自动滚动到底部，当有新的流式输出时
  useEffect(() => {
    if (streamingContentRef.current) {
      streamingContentRef.current.scrollTop = streamingContentRef.current.scrollHeight;
    }
  }, [workflowData?.events, isGenerating]);

  // 下载报告
  const handleDownloadReport = () => {
    if (!workflowData?.content) {
      alert('报告内容为空，无法下载');
      return;
    }

    try {
      const blob = new Blob([workflowData.content], { type: 'text/markdown' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // 清理文件名中的特殊字符
      const sanitizedCompanyName = companyName.replace(/[<>:"/\\|?*]/g, '_');
      const fileName = `${sanitizedCompanyName}_征信分析报告_${new Date().toISOString().split('T')[0]}.md`;
      link.download = fileName;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('下载失败:', error);
      alert('下载失败，请稍后重试');
    }
  };

  // 删除报告
  const handleDeleteReport = async () => {
    if (!projectId) {
      alert('项目ID不存在，无法删除报告');
      return;
    }

    const confirmed = window.confirm('确定要删除这个报告吗？此操作不可撤销。');
    if (!confirmed) {
      return;
    }

    try {
      setLoading(true);
      const response = await apiClient.delete(`/api/projects/${projectId}/report`);

      if (response.success) {
        alert('报告删除成功');
        onClose(); // 关闭预览弹窗
        // 可以触发父组件刷新数据
        if (onReportDeleted) {
          onReportDeleted();
        }
      } else {
        alert(response.error || '删除报告失败');
      }
    } catch (error) {
      console.error('删除报告失败:', error);
      alert('删除报告失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 渲染Markdown内容
  const renderMarkdown = (content: string) => {
    // 改进的Markdown渲染
    return content
      .split('\n')
      .map((line, index) => {
        // 处理标题
        if (line.startsWith('# ')) {
          return (
            <h1 key={index} className="text-3xl font-bold mb-6 text-gray-900 border-b-2 border-blue-200 pb-2">
              {line.substring(2)}
            </h1>
          );
        }
        if (line.startsWith('## ')) {
          return (
            <h2 key={index} className="text-2xl font-semibold mb-4 text-gray-800 mt-6">
              {line.substring(3)}
            </h2>
          );
        }
        if (line.startsWith('### ')) {
          return (
            <h3 key={index} className="text-xl font-medium mb-3 text-gray-700 mt-4">
              {line.substring(4)}
            </h3>
          );
        }

        // 处理列表项
        if (line.trim().match(/^\d+\.\s/)) {
          return (
            <li key={index} className="mb-1 text-gray-600 leading-relaxed ml-4">
              {line.trim().substring(line.trim().indexOf('.') + 1).trim()}
            </li>
          );
        }

        if (line.trim().startsWith('- ')) {
          return (
            <li key={index} className="mb-1 text-gray-600 leading-relaxed ml-4 list-disc">
              {line.trim().substring(2)}
            </li>
          );
        }

        // 处理空行
        if (line.trim() === '') {
          return <div key={index} className="mb-3" />;
        }

        // 处理普通段落
        const processedLine = line
          .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-800">$1</strong>')
          .replace(/\*(.*?)\*/g, '<em class="italic text-gray-700">$1</em>')
          .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>');

        return (
          <p
            key={index}
            className="mb-3 text-gray-600 leading-relaxed"
            dangerouslySetInnerHTML={{ __html: processedLine }}
          />
        );
      });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <style jsx>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }
      `}</style>
      <div className="bg-white rounded-lg w-full max-w-7xl h-full max-h-[90vh] flex flex-col">
        {/* 头部 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">征信报告预览</h2>
            <p className="text-sm text-gray-500 mt-1">公司：{companyName}</p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleDownloadReport}
              disabled={!workflowData?.content}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                workflowData?.content
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              <i className="ri-download-line mr-2"></i>
              下载报告
            </button>
            {projectId && (
              <button
                onClick={handleDeleteReport}
                disabled={loading}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  loading
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-red-600 text-white hover:bg-red-700'
                }`}
              >
                <i className="ri-delete-bin-line mr-2"></i>
                删除报告
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <i className="ri-close-line text-xl"></i>
            </button>
          </div>
        </div>

        {/* 内容区域 */}
        <div className="flex-1 flex overflow-hidden">
          {/* 左侧：流式输出 */}
          <div className="w-1/3 border-r border-gray-200 bg-black flex flex-col">
            {/* Header */}
            <div className="bg-gray-900 px-4 py-3 border-b border-gray-700 flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-300">实时输出</h3>
              {isGenerating && (
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2"></div>
                  <span className="text-xs text-green-400">生成中</span>
                </div>
              )}
            </div>

            {/* Content - 固定高度的滚动窗口 */}
            <div className="flex-1 flex flex-col bg-black">
              <div
                ref={streamingContentRef}
                className="flex-1 overflow-y-auto p-4 font-mono text-sm"
                style={{minHeight: '400px', maxHeight: '400px'}}
              >
                {loading && workflowData?.events?.length === 0 && (
                  <div className="text-cyan-400 mb-1">
                    <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span>
                    <span className="text-cyan-400 ml-2">初始化中...</span>
                  </div>
                )}

                {error && (
                  <div className="text-red-400 mb-1">
                    <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span>
                    <span className="text-red-400 ml-2">错误:</span>
                    <span className="text-white ml-2">{error}</span>
                  </div>
                )}

                {/* 流式输出 - 每行固定高度 */}
                {workflowData?.events && workflowData.events.map((event, index) => (
                  <div key={index} className="mb-1 leading-tight animate-fade-in">
                    <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span>
                    <span className="text-white ml-2">{event}</span>
                  </div>
                ))}

                {/* 生成中指示器 - 固定位置 */}
                {isGenerating && (
                  <div className="flex items-center mb-1">
                    <div className="flex space-x-1">
                      <div className="w-1 h-4 bg-green-400 animate-pulse"></div>
                      <div className="w-1 h-4 bg-green-400 animate-pulse" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-1 h-4 bg-green-400 animate-pulse" style={{animationDelay: '0.2s'}}></div>
                    </div>
                    <span className="text-green-400 ml-2 animate-pulse">处理中...</span>
                  </div>
                )}

                {/* 完成状态 - 固定高度 */}
                {!isGenerating && workflowData?.events && workflowData.events.length > 0 && (
                  <div className="border-t border-gray-700 pt-1 mt-1">
                    <div className="text-green-400 mb-1">
                      <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span>
                      <span className="text-green-400 ml-2">报告生成完成</span>
                    </div>
                  </div>
                )}

                {/* 空状态 - 居中显示 */}
                {(!workflowData?.events || workflowData.events.length === 0) && !isGenerating && !loading && (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-gray-500 text-center">
                      <div>等待开始...</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 右侧：报告内容预览 */}
          <div className="flex-1 flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <h3 className="font-medium text-gray-900">报告内容</h3>
              <p className="text-sm text-gray-500 mt-1">Markdown格式预览</p>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              {isGenerating ? (
                // 生成过程中显示等待状态
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent mx-auto mb-4"></div>
                    <p className="text-gray-600 text-lg font-medium mb-2">正在生成报告内容</p>
                    <p className="text-gray-500 text-sm">AI正在分析数据并生成征信报告，请稍候...</p>
                  </div>
                </div>
              ) : workflowData?.content ? (
                // 生成完成后显示报告内容
                <div className="prose prose-sm max-w-none">
                  {renderMarkdown(workflowData.content)}
                </div>
              ) : (
                // 无内容状态
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <i className="ri-file-text-line text-4xl text-gray-300 mb-4"></i>
                    <p className="text-gray-500">
                      {loading ? '正在加载报告内容...' : '暂无报告内容'}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportPreview;
