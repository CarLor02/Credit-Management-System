
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Portal from '@/components/Portal';
import { Project } from '@/services/projectService';
import { streamingContentService } from '@/services/streamingContentService';

interface ProjectCardProps {
  project: Project;
  onDelete?: (id: number) => void;
}

export default function ProjectCard({ project, onDelete }: ProjectCardProps) {
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [currentProgress, setCurrentProgress] = useState(project.progress || 0);
  const [reportStatus, setReportStatus] = useState(project.report_status || 'not_generated');

  // 监听流式内容服务的进度更新
  useEffect(() => {
    const handleProgressUpdate = (data: any) => {
      if (data.progress !== undefined) {
        setCurrentProgress(data.progress);
      }
      if (data.isGenerating !== undefined) {
        // 根据生成状态和进度确定报告状态
        if (data.isGenerating) {
          setReportStatus('generating');
        } else {
          // 如果不在生成中，根据进度判断状态
          setReportStatus(data.progress === 100 ? 'generated' : 'not_generated');
        }
      }
    };

    // 添加监听器
    streamingContentService.addListener(project.id, handleProgressUpdate);

    // 获取当前状态并初始化
    const streamingData = streamingContentService.getProjectData(project.id);
    if (streamingData) {
      setCurrentProgress(streamingData.progress || project.progress || 0);
      if (streamingData.isGenerating) {
        setReportStatus('generating');
      } else {
        // 优先使用项目的报告状态，如果没有则根据进度判断
        const finalStatus = project.report_status ||
          (streamingData.progress === 100 ? 'generated' : 'not_generated');
        setReportStatus(finalStatus);
      }
    } else {
      // 没有流式数据时，使用项目的状态
      setCurrentProgress(project.progress || 0);
      setReportStatus(project.report_status || 'not_generated');
    }

    return () => {
      streamingContentService.removeListener(project.id, handleProgressUpdate);
    };
  }, [project.id, project.progress, project.report_status]);

  // ESC键关闭弹窗
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showDeleteModal && !isDeleting) {
        setShowDeleteModal(false);
      }
    };

    if (showDeleteModal) {
      document.addEventListener('keydown', handleEscape);
      // 防止页面滚动
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [showDeleteModal, isDeleting]);

  // ESC键关闭弹窗
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showDeleteModal && !isDeleting) {
        setShowDeleteModal(false);
      }
    };

    if (showDeleteModal) {
      document.addEventListener('keydown', handleEscape);
      // 防止页面滚动
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [showDeleteModal, isDeleting]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'collecting':
        return 'bg-yellow-100 text-yellow-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'collecting':
        return '资料收集中';
      case 'processing':
        return '处理中';
      case 'completed':
        return '已完成';
      default:
        return '未知';
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low':
        return 'text-green-600';
      case 'medium':
        return 'text-yellow-600';
      case 'high':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getRiskText = (level: string) => {
    switch (level) {
      case 'low':
        return '低风险';
      case 'medium':
        return '中风险';
      case 'high':
        return '高风险';
      default:
        return '未知';
    }
  };

  // 获取报告状态文本和颜色
  const getReportStatusInfo = (status: string) => {
    switch (status) {
      case 'generating':
        return {
          text: '报告生成中...',
          color: 'text-blue-600',
          bgColor: 'bg-blue-100',
          icon: 'ri-loader-4-line animate-spin'
        };
      case 'generated':
        return {
          text: '报告已生成',
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          icon: 'ri-file-check-line'
        };

      case 'not_generated':
      default:
        return {
          text: '未生成报告',
          color: 'text-gray-600',
          bgColor: 'bg-gray-100',
          icon: 'ri-file-line'
        };
    }
  };

  const handleDelete = async () => {
    if (onDelete && !isDeleting) {
      setIsDeleting(true);
      try {
        await onDelete(project.id);
        setShowDeleteModal(false);
      } catch {
        // 错误处理由父组件处理，这里不需要额外操作
      } finally {
        setIsDeleting(false);
      }
    }
  };

  return (
    <>
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              project.type === 'enterprise' ? 'bg-blue-100' : 'bg-purple-100'
            }`}>
              <i className={`${project.type === 'enterprise' ? 'ri-building-line text-blue-600' : 'ri-user-line text-purple-600'} text-lg`}></i>
            </div>
            <div>
              <h3 className="font-semibold text-gray-800 text-lg">{project.name}</h3>
              <p className="text-sm text-gray-600">
                {project.type === 'enterprise' ? '企业征信' : '个人征信'}
              </p>
            </div>
          </div>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(project.status)}`}>
            {getStatusText(project.status)}
          </span>
        </div>

        <div className="space-y-3 mb-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">征信评分</span>
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-gray-800">{project.score}</span>
              <span className={`text-sm font-medium ${getRiskColor(project.riskLevel)}`}>
                {getRiskText(project.riskLevel)}
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">文档数量</span>
            <span className="text-sm font-medium text-gray-800">{project.documents} 个</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">最后更新</span>
            <span className="text-sm font-medium text-gray-800">{project.lastUpdate}</span>
          </div>

          {/* 报告状态显示 */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">征信报告</span>
            <div className="flex items-center space-x-1">
              <i className={`${getReportStatusInfo(reportStatus).icon} text-sm ${getReportStatusInfo(reportStatus).color}`}></i>
              <span className={`text-sm font-medium ${getReportStatusInfo(reportStatus).color}`}>
                {getReportStatusInfo(reportStatus).text}
              </span>
            </div>
          </div>
        </div>

        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">
              {reportStatus === 'generating' ? '生成进度' : '完成进度'}
            </span>
            <span className="text-sm font-medium text-gray-800">{currentProgress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                reportStatus === 'generating' ? 'bg-blue-600' : 'bg-green-600'
              }`}
              style={{ width: `${currentProgress}%` }}
            ></div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Link
            href={`/projects/${project.id}`}
            className="flex-1 bg-blue-600 text-white text-center py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium whitespace-nowrap"
          >
            查看详情
          </Link>
          <button
            onClick={() => setShowDeleteModal(true)}
            className="w-10 h-10 flex items-center justify-center rounded-lg border border-red-300 hover:bg-red-50 hover:border-red-400 transition-colors group"
            title="删除项目"
          >
            <i className="ri-delete-bin-line text-red-500 group-hover:text-red-600"></i>
          </button>
        </div>
      </div>

      {showDeleteModal && (
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
              if (e.target === e.currentTarget && !isDeleting) {
                setShowDeleteModal(false);
              }
            }}
          >
            <div 
              className="bg-white rounded-xl p-6 max-w-md w-full shadow-xl animate-fadeIn"
              style={{
                maxHeight: '90vh',
                overflow: 'auto'
              }}
              onClick={(e) => e.stopPropagation()} // 防止点击弹窗内容时关闭
            >
              <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
                <i className="ri-error-warning-line text-red-600 text-xl"></i>
              </div>
              <h3 className="text-lg font-medium text-gray-800 text-center mb-2">确认删除项目</h3>
              <p className="text-gray-600 text-center mb-6">
                您确定要删除项目 &ldquo;<span className="font-medium">{project.name}</span>&rdquo; 吗？<br /><br /><strong>此操作不可恢复。</strong>
              </p>
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowDeleteModal(false)}
                  disabled={isDeleting}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  取消
                </button>
                <button
                  onClick={handleDelete}
                  disabled={isDeleting}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {isDeleting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                      删除中...
                    </>
                  ) : (
                    '确认删除'
                  )}
                </button>
              </div>
            </div>
          </div>
        </Portal>
      )}
    </>
  );
}
