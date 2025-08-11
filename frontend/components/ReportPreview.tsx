'use client';

import React, { useState, useEffect, useRef } from 'react';
import { apiClient } from '../services/api';
import websocketService from '../services/websocketService';
import PdfViewer from './PDFViewer';

interface StreamingEvent {
  timestamp: string;
  eventType: string;
  content: string;
  color: string;
  isContent: boolean;
}

interface ReportPreviewProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: number;
  companyName: string;
  onReportDeleted?: () => void;
}

const ReportPreview: React.FC<ReportPreviewProps> = ({
  isOpen,
  onClose,
  projectId,
  companyName,
  onReportDeleted
}) => {
  const [reportContent, setReportContent] = useState<string>('');
  const [htmlContent, setHtmlContent] = useState<string>('');
  const [streamingEvents, setStreamingEvents] = useState<StreamingEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [websocketStatus, setWebsocketStatus] = useState<string>('未连接');
  const [isPdfPreview, setIsPdfPreview] = useState(false); // false=HTML预览, true=PDF预览
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [htmlLoading, setHtmlLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const streamingContentRef = useRef<HTMLDivElement>(null);
  const eventsRef = useRef<HTMLDivElement>(null);

  // 获取已生成的报告内容
  const fetchReportContent = async () => {
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
        setReportContent(response.data.content);
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

  // 获取HTML格式的报告内容
  const fetchHtmlContent = async () => {
    if (!projectId) return;

    setHtmlLoading(true);

    try {
      const response = await apiClient.get<{
        html_content: string;
        company_name: string;
        file_path: string;
      }>(`/projects/${projectId}/report/html`);

      if (response.success && response.data) {
        setHtmlContent(response.data.html_content);
      } else {
        console.error('获取HTML内容失败:', response.error);
      }
    } catch (err) {
      console.error('获取HTML内容失败:', err);
    } finally {
      setHtmlLoading(false);
    }
  };





  // WebSocket连接和流式输出 - 只在弹窗打开时连接
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    console.log('🔌 弹窗打开，开始WebSocket连接，项目ID:', projectId);

    // 不清空之前的内容和事件，保留历史以便回看
    console.log('🔁 保留之前的事件和内容，继续接收新的流式数据');

    // 按照要求的格式打印事件：时间 事件：内容，支持颜色和详细信息
    const addEvent = (eventType: string, content: string = '', eventData?: any) => {
      const timestamp = new Date().toLocaleTimeString();

      // 根据事件类型生成详细信息
      let detailInfo = content;
      let eventColor = 'text-green-400'; // 默认绿色

      switch (eventType) {
        case 'node_started':
          if (eventData?.data?.title) {
            detailInfo = `节点启动: ${eventData.data.title}`;
            eventColor = 'text-blue-400';
          } else {
            detailInfo = '节点启动';
            eventColor = 'text-blue-400';
          }
          break;
        case 'parallel_branch_started':
          detailInfo = '并行分支启动';
          eventColor = 'text-purple-400';
          break;
        case 'node_finished':
          detailInfo = '节点完成';
          eventColor = 'text-green-400';
          break;
        case 'workflow_started':
          detailInfo = '工作流开始';
          eventColor = 'text-cyan-400';
          break;
        case 'workflow_complete':
          detailInfo = '工作流完成';
          eventColor = 'text-green-500';
          break;
        case '内容块':
          eventColor = 'text-yellow-400';
          break;
        case '错误':
          eventColor = 'text-red-400';
          break;
        default:
          eventColor = 'text-gray-400';
      }

      const eventEntry = {
        timestamp,
        eventType,
        content: detailInfo,
        color: eventColor,
        isContent: eventType === '内容块'
      };

      console.log('📝 添加事件到界面:', eventEntry);
      setStreamingEvents(prev => [...prev, eventEntry]);

      // 自动滚动事件列表
      setTimeout(() => {
        if (eventsRef.current) {
          eventsRef.current.scrollTop = eventsRef.current.scrollHeight;
        }
      }, 100);
    };

    // WebSocket已在项目详情页连接，这里只需要设置状态和监听器
    const projectRoom = `project_${projectId}`;
    setWebsocketStatus(`监听房间: ${projectRoom}`);

    // 添加测试事件验证功能
    addEvent('预览窗口打开', '开始监听流式事件');

    // 接收流式内容但不实时显示，仅记录到事件中
    const addContent = (content: string) => {
      console.log('📝 收到内容块，记录到事件中:', content.substring(0, 50) + '...');
      // 不再实时累积到 reportContent，等待完成事件时一次性加载
    };

    // 定义事件处理函数，以便后续清理
    const handleWorkflowEvent = (data: any) => {
      console.log('🎯 收到workflow_event:', data);
      const eventType = data.event_type || '工作流事件';
      addEvent(eventType, '', data);

      if (eventType === 'generation_started' || eventType === 'workflow_started') {
        setGenerating(true);
        console.log('🚀 开始生成报告，设置generating为true');
      }
    };

    const handleWorkflowContent = (data: any) => {
      console.log('📄 收到workflow_content:', data);
      if (data.content_chunk) {
        addContent(data.content_chunk);
        // 显示具体内容而不是字符数
        addEvent('内容块', data.content_chunk);
      }
    };

    const handleWorkflowComplete = (data: any) => {
      console.log('✅ 收到workflow_complete:', data);
      addEvent('报告生成完成', '');
      setWebsocketStatus('生成完成');
      setGenerating(false);
      // 优先使用完成事件中的最终内容，否则从文件加载最新内容
      if (data.final_content) {
        console.log('✅ 使用完成事件中的最终内容');
        setReportContent(data.final_content);
        // 同时获取HTML内容
        fetchHtmlContent();
      } else {
        console.log('✅ 从文件加载最终报告内容');
        fetchReportContent();
        fetchHtmlContent();
      }
    };

    const handleWorkflowError = (data: any) => {
      console.log('❌ 收到workflow_error:', data);
      addEvent('错误', data.error_message || '未知错误');
      setError(data.error_message);
      setGenerating(false);
      console.log('❌ 报告生成出错，设置generating为false');
    };

    // 监听WebSocket消息 - 详细展示不同类型的事件
    websocketService.on('workflow_event', handleWorkflowEvent);
    websocketService.on('workflow_content', handleWorkflowContent);
    websocketService.on('workflow_complete', handleWorkflowComplete);
    websocketService.on('workflow_error', handleWorkflowError);

    // 清理函数 - 移除事件监听器，防止重复注册
    return () => {
      console.log('🧹 清理事件监听器（保持WebSocket连接）');

      // 移除具体的事件监听器，防止重复注册
      websocketService.off('workflow_event', handleWorkflowEvent);
      websocketService.off('workflow_content', handleWorkflowContent);
      websocketService.off('workflow_complete', handleWorkflowComplete);
      websocketService.off('workflow_error', handleWorkflowError);

      setWebsocketStatus('未连接');
    };
  }, [isOpen, projectId]); // eslint-disable-line react-hooks/exhaustive-deps

  // 获取报告内容（每次打开时都加载）
  useEffect(() => {
    if (isOpen) {
      fetchReportContent();
      fetchHtmlContent(); // 同时获取HTML内容
    }
  }, [isOpen, projectId]); // eslint-disable-line react-hooks/exhaustive-deps

  // 清理PDF URL
  useEffect(() => {
    return () => {
      if (pdfUrl) {
        window.URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [pdfUrl]);

  // 下载报告（HTML格式）
  const handleDownloadReport = async () => {
    if (!projectId || loading) return;

    try {
      setLoading(true);

      const token = localStorage.getItem('auth_token');
      if (!token) {
        alert('请先登录');
        return;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5001/api'}/projects/${projectId}/report/download-html`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      // 获取文件名
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `${companyName}_征信报告.html`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }

      // 下载文件
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error('下载HTML报告失败:', error);
      alert(error instanceof Error ? error.message : '下载HTML报告失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 下载PDF报告
  const handleDownloadPDF = async () => {
    if (!projectId || loading) return;

    try {
      setLoading(true);

      const token = localStorage.getItem('auth_token');
      if (!token) {
        alert('请先登录');
        return;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5001/api'}/projects/${projectId}/report/download-pdf`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      // 获取文件名
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `${companyName}_征信报告.pdf`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }

      // 下载文件
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error('下载PDF报告失败:', error);
      alert(error instanceof Error ? error.message : '下载PDF报告失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 删除报告
  const handleDeleteReport = async () => {
    if (!projectId || loading) return;

    if (!confirm('确定要删除这个报告吗？此操作不可撤销。')) {
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.delete(`/projects/${projectId}/report`);
      if (response.success) {
        onReportDeleted?.();
        onClose();
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

  // 转换PDF预览
  const handleConvertToPdfPreview = async () => {
    if (!projectId || pdfLoading) return;

    try {
      setPdfLoading(true);

      const token = localStorage.getItem('auth_token');
      if (!token) {
        alert('请先登录');
        return;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5001/api'}/projects/${projectId}/report/download-pdf`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      // 获取文件blob
      const blob = await response.blob();

      // 创建PDF预览URL
      const url = window.URL.createObjectURL(blob);
      setPdfUrl(url);
      setIsPdfPreview(true);

    } catch (error) {
      console.error('转换PDF预览失败:', error);
      alert(error instanceof Error ? error.message : '转换PDF预览失败，请稍后重试');
    } finally {
      setPdfLoading(false);
    }
  };

  // 切换到HTML预览
  const handleSwitchToHtml = () => {
    setIsPdfPreview(false);
    if (pdfUrl) {
      window.URL.revokeObjectURL(pdfUrl);
      setPdfUrl(null);
    }
  };

  // 不再需要自定义格式化函数，使用MarkdownPreview组件

  if (!isOpen) {
    console.log('🚫 ReportPreview: isOpen为false，不渲染弹窗');
    return null;
  }

  console.log('✅ ReportPreview: 渲染弹窗，isOpen:', isOpen);

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
            {/* 预览切换和下载按钮 */}
            {reportContent && (
              <>
                {/* 预览模式切换按钮 */}
                {isPdfPreview ? (
                  <button
                    onClick={handleSwitchToHtml}
                    className="px-4 py-2 rounded-lg text-sm font-medium transition-colors bg-gray-600 text-white hover:bg-gray-700"
                  >
                    <i className="ri-html5-line mr-2"></i>
                    返回HTML预览
                  </button>
                ) : (
                  <button
                    onClick={handleConvertToPdfPreview}
                    disabled={pdfLoading}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      pdfLoading
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-green-600 text-white hover:bg-green-700'
                    }`}
                  >
                    <i className="ri-file-pdf-line mr-2"></i>
                    {pdfLoading ? '转换中...' : '转换PDF预览'}
                  </button>
                )}

                <button
                  onClick={handleDownloadPDF}
                  disabled={loading}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    loading
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  <i className="ri-file-pdf-line mr-2"></i>
                  下载PDF
                </button>
                <button
                  onClick={handleDownloadReport}
                  disabled={loading}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    loading
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  <i className="ri-download-line mr-2"></i>
                  下载HTML
                </button>
              </>
            )}

            {/* 删除按钮 */}
            {reportContent && (
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
          {/* 左侧：流式输出 - 固定25%宽度 */}
          <div className="w-1/4 min-w-0 border-r border-gray-200 bg-black flex flex-col">
            {/* Header */}
            <div className="bg-gray-900 px-4 py-3 border-b border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-300">实时输出</h3>

              </div>
              {/* WebSocket状态 */}
              <div className="flex items-center">
                <div className={`w-2 h-2 rounded-full mr-2 ${
                  websocketStatus.includes('已加入房间') ? 'bg-green-400' :
                  websocketStatus === '已连接' ? 'bg-yellow-400' :
                  'bg-red-400'
                }`}></div>
                <span className="text-xs text-gray-400">WebSocket: {websocketStatus}</span>
              </div>
            </div>

            {/* 事件列表 */}
            <div 
              ref={eventsRef}
              className="flex-1 overflow-y-auto p-4 font-mono text-sm text-green-400 space-y-1"
            >
              {streamingEvents.length === 0 ? (
                <div className="text-gray-500 text-center mt-8">
                  暂无事件
                </div>
              ) : (
                streamingEvents.map((event, index) => (
                  <div key={index} className="animate-fade-in mb-1">
                    <span className="text-gray-400">{event.timestamp}</span>
                    <span className="mx-2">|</span>
                    <span className={event.color}>{event.eventType}</span>
                    {event.content && (
                      <>
                        <span className="text-gray-400">：</span>
                        <span className={event.isContent ? 'text-white' : 'text-gray-300'}>
                          {event.content}
                        </span>
                      </>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* 右侧：报告内容 - 固定75%宽度 */}
          <div className="w-3/4 min-w-0 flex flex-col">
            {/* 内容区域 */}
            <div 
              ref={streamingContentRef}
              className="flex-1 overflow-y-auto p-6 bg-gray-50"
            >
              {error ? (
                <div className="text-center py-12">
                  <div className="text-red-600 mb-4">
                    <i className="ri-error-warning-line text-4xl"></i>
                  </div>
                  <p className="text-red-600 font-medium">{error}</p>
                </div>
              ) : (generating || loading) ? (
                <div className="text-center py-12">
                  <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
                  <p className="text-gray-600">正在生成报告，请稍候...</p>
                  <p className="text-gray-500 text-sm mt-2">报告完成后将自动加载内容</p>
                </div>
              ) : (generating || loading) ? (
                <div className="text-center py-12">
                  <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
                  <p className="text-gray-600">加载报告内容中...</p>
                </div>
              ) : reportContent ? (
                isPdfPreview && pdfUrl ? (
                  // PDF预览模式
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden h-full">
                    <div className="bg-gradient-to-r from-gray-50 to-red-50 px-4 py-2 border-b border-gray-200">
                      <div className="flex items-center space-x-2">
                        <i className="ri-file-pdf-line text-red-600"></i>
                        <span className="text-sm font-medium text-gray-700">征信报告</span>
                        <span className="text-xs text-gray-500">• PDF格式</span>
                      </div>
                    </div>
                    <div className="h-full" style={{ height: 'calc(100% - 50px)' }}>
                      <PdfViewer
                        pdfUrl={pdfUrl}
                        title="征信报告PDF预览"
                        showControls={true}
                      />
                    </div>
                  </div>
                ) : (
                  // HTML预览模式（默认）
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden h-full">
                    <div className="bg-gradient-to-r from-gray-50 to-green-50 px-4 py-2 border-b border-gray-200">
                      <div className="flex items-center space-x-2">
                        <i className="ri-html5-line text-green-600"></i>
                        <span className="text-sm font-medium text-gray-700">征信报告</span>
                        <span className="text-xs text-gray-500">• HTML格式</span>
                      </div>
                    </div>
                    <div
                      className="overflow-y-auto px-6 h-full"
                      style={{
                        height: 'calc(100% - 50px)',
                        width: '100%'
                      }}
                    >
                      {htmlLoading ? (
                        <div className="text-center py-8">
                          <div className="animate-spin w-6 h-6 border-4 border-green-600 border-t-transparent rounded-full mx-auto mb-4"></div>
                          <p className="text-gray-600">正在转换HTML格式...</p>
                        </div>
                      ) : htmlContent ? (
                        <iframe
                          srcDoc={htmlContent}
                          style={{
                            width: '100%',
                            height: '100%',
                            border: 'none',
                            backgroundColor: 'white'
                          }}
                          title="征信报告HTML预览"
                          sandbox="allow-same-origin"
                        />
                      ) : (
                        <div className="text-center py-8 text-gray-500">
                          <i className="ri-html5-line text-4xl mb-4"></i>
                          <p>HTML内容加载失败，请刷新页面重试</p>
                        </div>
                      )}
                    </div>
                  </div>
                )
              ) : (
                <div className="text-center py-12">
                  <div className="text-gray-400 mb-4">
                    <i className="ri-file-text-line text-4xl"></i>
                  </div>
                  <p className="text-gray-600">暂无报告内容</p>
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
