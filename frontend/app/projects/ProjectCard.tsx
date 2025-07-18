
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Portal from '@/components/Portal';

interface Project {
  id: number;
  name: string;
  type: 'enterprise' | 'individual';
  status: 'collecting' | 'processing' | 'completed';
  score: number;
  riskLevel: 'low' | 'medium' | 'high';
  lastUpdate: string;
  documents: number;
  progress: number;
}

interface ProjectCardProps {
  project: Project;
  onDelete?: (id: number) => void;
}

export default function ProjectCard({ project, onDelete }: ProjectCardProps) {
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

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

  const handleDelete = async () => {
    if (onDelete && !isDeleting) {
      setIsDeleting(true);
      try {
        await onDelete(project.id);
        setShowDeleteModal(false);
      } catch (error) {
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
        </div>

        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">完成进度</span>
            <span className="text-sm font-medium text-gray-800">{project.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${project.progress}%` }}
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
                您确定要删除项目 "<span className="font-medium">{project.name}</span>" 吗？此操作无法撤销。
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
