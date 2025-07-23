
'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Header from '@/components/Header';
import CreateProjectModal from '../CreateProjectModal';
import DocumentPreview from '@/components/DocumentPreview';
import ReportPreview from '@/components/ReportPreview';
import { projectService } from '@/services/projectService';
import { documentService } from '@/services/documentService';
import { BusinessStatus, TimelineEvent } from '@/services/projectDetailService';
import { apiClient } from '@/services/api';
import { Project } from '@/services/projectService';

interface ProjectDetailProps {
  projectId: string;
}

export default function ProjectDetail({ projectId }: ProjectDetailProps) {
  const [activeTab, setActiveTab] = useState('overview');
  const [showDownloadModal, setShowDownloadModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);

  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 项目文档状态
  const [documents, setDocuments] = useState<any[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(true);
  const [documentPolling, setDocumentPolling] = useState<NodeJS.Timeout | null>(null);

  // 预览相关状态
  const [previewDocument, setPreviewDocument] = useState<{ id: number; name: string } | null>(null);

  // 项目详情数据状态
  const [financialData, setFinancialData] = useState<any>(null);
  const [businessStatus, setBusinessStatus] = useState<BusinessStatus | null>(null);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [financialLoading, setFinancialLoading] = useState(false);
  const [businessLoading, setBusinessLoading] = useState(false);
  const [timelineLoading, setTimelineLoading] = useState(false);

  const router = useRouter();

  // 加载项目数据
  useEffect(() => {
    const fetchProject = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // 添加最小加载时间，避免闪烁
        const [response] = await Promise.all([
          projectService.getProjectById(parseInt(projectId)),
          new Promise(resolve => setTimeout(resolve, 300)) // 最小300ms加载时间
        ]);
        
        if (response.success && response.data) {
          setProject(response.data);
        } else {
          setError(response.error || '加载项目失败');
        }
      } catch (err) {
        setError('网络错误，请稍后重试');
        console.error('Load project error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchProject();
  }, [projectId]);

  // 加载项目文档
  useEffect(() => {
    const fetchDocuments = async () => {
      if (!project?.id) return; // 如果没有项目ID，不加载文档
      
      try {
        setDocumentsLoading(true);
        const response = await documentService.getDocuments({
          project_id: project.id
        });

        if (response.success && response.data) {
          setDocuments(response.data);
          
          // 检查是否有处理中的文档，如果有则启动轮询
          const processingDocs = response.data.filter(doc => 
            doc.status === 'processing' || doc.status === 'uploading' || 
            doc.status === 'uploading_to_kb' || doc.status === 'parsing_kb'
          );
          
          if (processingDocs.length > 0) {
            startDocumentPolling();
          } else {
            stopDocumentPolling();
          }
        }
      } catch (err) {
        console.error('Load documents error:', err);
        setDocuments([]);
      } finally {
        setDocumentsLoading(false);
      }
    };

    fetchDocuments();
  }, [project?.id]); // 依赖项目ID而不是整个项目对象

  // 启动文档轮询
  const startDocumentPolling = () => {
    if (documentPolling) {
      clearInterval(documentPolling);
    }
    
    const interval = setInterval(async () => {
      try {
        if (!project?.id) return; // 如果没有项目ID，停止轮询
        
        const response = await documentService.getDocuments({
          project_id: project.id
        });
        
        if (response.success && response.data) {
          setDocuments(response.data);
          
          // 检查是否还有处理中的文档
          const processingDocs = response.data.filter(doc => 
            doc.status === 'processing' || doc.status === 'uploading' ||
            doc.status === 'uploading_to_kb' || doc.status === 'parsing_kb'
          );
          
          if (processingDocs.length === 0) {
            stopDocumentPolling();
          }
        }
      } catch (err) {
        console.error('Polling documents error:', err);
      }
    }, 2000); // 每2秒轮询一次
    
    setDocumentPolling(interval);
  };

  // 停止文档轮询
  const stopDocumentPolling = () => {
    if (documentPolling) {
      clearInterval(documentPolling);
      setDocumentPolling(null);
    }
  };

  // 组件卸载时停止轮询
  useEffect(() => {
    return () => {
      stopDocumentPolling();
    };
  }, [documentPolling]);



  // 加载财务分析数据
  const loadFinancialData = async () => {
    if (!project || project.type !== 'enterprise') return;

    try {
      setFinancialLoading(true);

      // TODO: 暂时使用默认数据，后续实现真实API调用
      // const response = await projectDetailService.getFinancialAnalysis(project.id);

      // 使用默认财务数据
      const defaultFinancialData = {
        revenue: { current: 0, previous: 0, growth: 0 },
        profit: { current: 0, previous: 0, growth: 0 },
        assets: { current: 0, previous: 0, growth: 0 },
        liabilities: { current: 0, previous: 0, growth: 0 }
      };

      setFinancialData(defaultFinancialData);
    } catch (err) {
      console.error('Load financial data error:', err);
    } finally {
      setFinancialLoading(false);
    }
  };

  // 加载经营状况数据
  const loadBusinessStatus = async () => {
    if (!project || project.type !== 'enterprise') return;

    try {
      setBusinessLoading(true);

      // TODO: 暂时使用默认数据，后续实现真实API调用
      // const response = await projectDetailService.getBusinessStatus(project.id);

      // 使用默认经营状况数据
      const defaultBusinessStatus = {
        operatingStatus: 'normal' as const,
        creditRating: 'A',
        riskLevel: 'low' as const,
        complianceScore: 85,
        marketPosition: '行业领先',
        businessScope: ['金融服务', '投资管理', '风险控制']
      };

      setBusinessStatus(defaultBusinessStatus);
    } catch (err) {
      console.error('Load business status error:', err);
    } finally {
      setBusinessLoading(false);
    }
  };

  // 加载时间轴数据
  const loadTimelineData = async () => {
    if (!project) return;

    try {
      setTimelineLoading(true);

      // TODO: 暂时使用默认数据，后续实现真实API调用
      // const response = await projectDetailService.getTimeline(project.id);

      // 使用默认时间轴数据
      const defaultTimelineEvents = [
        {
          id: 1,
          date: new Date().toISOString().split('T')[0],
          type: 'milestone' as const,
          title: '项目创建',
          description: '项目已成功创建并开始收集资料',
          status: 'completed' as const
        },
        {
          id: 2,
          date: new Date().toISOString().split('T')[0],
          type: 'document' as const,
          title: '文档上传',
          description: '开始上传相关文档资料',
          status: 'processing' as const
        }
      ];

      setTimelineEvents(defaultTimelineEvents);
    } catch (err) {
      console.error('Load timeline data error:', err);
      setTimelineEvents([]);
    } finally {
      setTimelineLoading(false);
    }
  };

  // 检查项目是否已有报告
  const checkExistingReport = async () => {
    if (!project?.id) return;

    try {
      const response = await apiClient.get<{
        success: boolean;
        content: string;
        file_path: string;
        company_name: string;
        error?: string;
      }>(`/projects/${project.id}/report`);

      if (response.success && response.data?.success && response.data?.content) {
        // 如果已有报告且内容不为空，设置按钮为可用状态
        setReportGenerated(true);
        console.log('发现已存在的报告，启用预览按钮');
      } else {
        // 如果没有报告或内容为空，保持默认状态（按钮禁用）
        setReportGenerated(false);
        console.log('项目暂无报告，保持按钮禁用状态');
      }
    } catch (error: any) {
      // 静默处理错误，不显示错误信息
      setReportGenerated(false);
      console.log('检查报告时出现错误，保持按钮禁用状态:', error?.message || error);

      // 不要显示错误提示，因为这是正常的检查流程
      // 项目没有报告是正常情况，不应该报错
    }
  };

  // 当项目数据加载完成后，加载详情数据
  useEffect(() => {
    if (project) {
      loadFinancialData();
      loadBusinessStatus();
      loadTimelineData();
      checkExistingReport(); // 检查是否已有报告
    }
  }, [project]);

  // 获取编辑数据
  const getEditData = () => {
    if (!project) return null;
    


    return {
      id: project.id,
      name: project.name,
      type: project.type,
      description: '', // 需要后端提供此字段
      category: 'other', // 需要后端提供此字段
      priority: 'medium'
    };
  };

  // 生成征信报告状态
  const [reportGenerating, setReportGenerating] = useState(false);
  const [reportGenerated, setReportGenerated] = useState(false);
  const [workflowRunId, setWorkflowRunId] = useState<string | null>(null);
  const [showReportPreview, setShowReportPreview] = useState(false);

  const handleDownloadReport = async () => {
    if (!project) {
      alert('项目信息不完整，无法生成报告');
      return;
    }

    // 检查必要的项目信息
    if (!project.dataset_id && !project.knowledge_base_name) {
      alert('项目尚未创建知识库，请先上传文档并等待处理完成');
      return;
    }

    try {
      setReportGenerating(true);

      // 立即打开预览弹窗，让用户看到流式输出
      setShowReportPreview(true);

      // 调用后端API生成报告
      const response = await apiClient.post<{
        success: boolean;
        message?: string;
        workflow_run_id?: string;
        content?: string;
        file_path?: string;
        parsing_complete?: boolean;
        error?: string;
        metadata?: any;
        events?: string[];
      }>('/generate_report', {
        dataset_id: project.dataset_id, // 使用dataset_id作为fallback
        company_name: project.name,
        knowledge_name: project.knowledge_base_name, // knowledge_base_name
        project_id: project.id // 添加项目ID
      });

      console.log('API Response:', response); // 调试日志

      if (response.success && response.data?.success) {
        // 报告生成成功
        const workflowId = response.data.workflow_run_id;
        const hasContent = response.data.content && response.data.content.length > 0;

        console.log('Report generated successfully, workflow ID:', workflowId); // 调试日志
        console.log('Has content:', hasContent); // 调试日志

        // 立即设置workflow ID以启动轮询
        if (workflowId) {
          setWorkflowRunId(workflowId);
          console.log('立即设置workflow_run_id以启动轮询:', workflowId); // 调试日志
        }

        // 无论是否有workflow ID，只要有内容就认为成功
        if (workflowId || hasContent) {
          setReportGenerated(true);

          console.log('报告生成完成，包含Dify流式事件:', response.data?.events?.length || 0); // 调试日志

          // 预览弹窗已经打开，显示最终结果
          // 报告内容和Dify事件会通过ReportPreview组件自动加载和显示
        } else {
          alert('报告生成成功，但未获取到内容');
        }
      } else {
        const errorMsg = response.data?.error || response.error || '生成报告失败，请稍后重试';
        alert(errorMsg);
        // 生成失败时关闭预览弹窗
        setShowReportPreview(false);
      }
    } catch (error) {
      console.error('Generate report error:', error);

      // 根据错误类型提供更具体的错误信息
      let errorMessage = '生成报告失败，请稍后重试';

      if (error instanceof Error) {
        if (error.message.includes('network') || error.message.includes('fetch')) {
          errorMessage = '网络连接失败，请检查网络连接后重试';
        } else if (error.message.includes('timeout')) {
          errorMessage = '请求超时，请稍后重试';
        } else if (error.message.includes('401') || error.message.includes('unauthorized')) {
          errorMessage = '认证失败，请重新登录后重试';
        } else if (error.message.includes('403') || error.message.includes('forbidden')) {
          errorMessage = '权限不足，无法生成报告';
        } else if (error.message.includes('500')) {
          errorMessage = '服务器内部错误，请联系管理员';
        }
      }

      alert(errorMessage);
      // 生成失败时关闭预览弹窗
      setShowReportPreview(false);
    } finally {
      setReportGenerating(false);
    }
  };

  const handleAddDocument = () => {
    // 使用 Next.js 路由跳转到文档页面，并传递项目ID参数
    router.push(`/documents?project=${project?.id}`);
  };

  // 加载中状态
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        
        {/* 头部面包屑 */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Link href="/projects" className="hover:text-blue-600">
                项目管理
              </Link>
              <i className="ri-arrow-right-s-line"></i>
              <span className="text-gray-400">加载中...</span>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent mb-4"></div>
              <p className="text-gray-600">加载项目数据...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 错误状态
  if (error || !project) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        
        {/* 头部面包屑 */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Link href="/projects" className="hover:text-blue-600">
                项目管理
              </Link>
              <i className="ri-arrow-right-s-line"></i>
              <span className="text-gray-400">加载失败</span>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-center h-64">
            <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100 max-w-md w-full">
              <div className="text-center mb-6">
                <div className="inline-block rounded-full h-12 w-12 bg-red-100 flex items-center justify-center mb-4">
                  <i className="ri-error-warning-line text-red-600 text-xl"></i>
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">加载失败</h2>
                <p className="text-gray-600">{error || '无法加载项目数据'}</p>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => router.push('/projects')}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  返回项目列表
                </button>
                <button
                  onClick={() => router.refresh()}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  重试
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 定义标签页
  const tabs = project.type === 'enterprise'
    ? [
        { id: 'overview', name: '企业概览', icon: 'ri-building-line' },
        { id: 'financial', name: '财务分析', icon: 'ri-bar-chart-line' },
        { id: 'business', name: '经营状况', icon: 'ri-briefcase-line' },
        { id: 'documents', name: '相关文档', icon: 'ri-file-list-line' },
        { id: 'timeline', name: '时间轴', icon: 'ri-time-line' }
      ]
    : [
        { id: 'overview', name: '个人概览', icon: 'ri-user-line' },
        { id: 'credit', name: '信用记录', icon: 'ri-credit-card-line' },
        { id: 'income', name: '收入分析', icon: 'ri-money-dollar-circle-line' },
        { id: 'documents', name: '相关文档', icon: 'ri-file-list-line' },
        { id: 'timeline', name: '时间轴', icon: 'ri-time-line' }
      ];





  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'collecting': return 'text-yellow-600 bg-yellow-50';
      case 'processing': return 'text-blue-600 bg-blue-50';
      case 'completed': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  // 获取风险级别颜色
  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-green-600 bg-green-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'high': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  // 获取状态文本
  const getStatusText = (status: string) => {
    switch (status) {
      case 'collecting': return '收集中';
      case 'processing': return '处理中';
      case 'completed': return '已完成';
      default: return status;
    }
  };

  // 获取风险级别文本
  const getRiskText = (risk: string) => {
    switch (risk) {
      case 'low': return '低风险';
      case 'medium': return '中风险';
      case 'high': return '高风险';
      default: return risk;
    }
  };

  // 获取文档状态颜色
  const getDocumentStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'uploading':
        return 'bg-yellow-100 text-yellow-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'uploading_to_kb':
        return 'bg-purple-100 text-purple-800';
      case 'parsing_kb':
        return 'bg-indigo-100 text-indigo-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'kb_parse_failed':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // 获取文档状态文本
  const getDocumentStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '知识库解析成功';
      case 'uploading': return '本地上传中';
      case 'processing': return '处理文件中';
      case 'uploading_to_kb': return '上传知识库中';
      case 'parsing_kb': return '知识库解析中';
      case 'failed': return '失败';
      case 'kb_parse_failed': return '知识库解析失败';
      default: return '未知';
    }
  };

  // 获取文件图标
  const getFileIcon = (type: string) => {
    switch (type) {
      case 'pdf':
        return 'ri-file-pdf-line text-red-600';
      case 'excel':
        return 'ri-file-excel-line text-green-600';
      case 'word':
        return 'ri-file-word-line text-blue-600';
      case 'image':
        return 'ri-image-line text-purple-600';
      case 'markdown':
        return 'ri-markdown-line text-orange-600';
      default:
        return 'ri-file-line text-gray-600';
    }
  };

  // 下载文档
  const handleDownloadDocument = async (id: number, name: string) => {
    try {
      const response = await documentService.downloadDocument(id);
      if (response.success && response.data) {
        const url = window.URL.createObjectURL(response.data);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = name;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert(response.error || '下载文档失败');
      }
    } catch (err) {
      alert('下载文档失败，请稍后重试');
      console.error('Download document error:', err);
    }
  };

  // 重试文档处理
  const handleRetryDocument = async (documentId: number, documentName: string) => {
    if (!confirm(`确定要重试处理文档"${documentName}"吗？\n\n此操作将重新开始文档处理流程。`)) {
      return;
    }

    try {
      const response = await documentService.retryDocumentProcessing(documentId);
      if (response.success) {
        alert(response.message || '文档重试处理任务已启动');
        // 重试成功，立即刷新文档状态
        const updatedResponse = await documentService.getDocuments({
          project_id: project?.id || 0
        });
        if (updatedResponse.success && updatedResponse.data) {
          setDocuments(updatedResponse.data);
        }
      } else {
        alert(response.error || '重试失败');
      }
    } catch (err) {
      alert('重试失败，请稍后重试');
      console.error('Retry document processing error:', err);
    }
  };

  // 删除文档
  const handleDeleteDocument = async (id: number) => {
    // 确认删除
    if (!window.confirm('确定要删除这个文档吗？此操作不可恢复。')) {
      return;
    }

    try {
      // 乐观更新：立即从UI中移除文档
      const docToDelete = documents.find(doc => doc.id === id);
      if (!docToDelete) return;

      const updatedDocuments = documents.filter(doc => doc.id !== id);
      setDocuments(updatedDocuments);

      const response = await documentService.deleteDocument(id);
      if (response.success) {
        // 删除成功，不需要额外处理
      } else {
        // 删除失败，恢复文档
        const restoredDocuments = [...updatedDocuments, docToDelete].sort((a, b) => a.id - b.id);
        setDocuments(restoredDocuments);
        alert(response.error || '删除文档失败');
      }
    } catch (err) {
      // 网络错误，恢复文档
      const docToDelete = documents.find(doc => doc.id === id);
      if (docToDelete) {
        const restoredDocuments = [...documents.filter(doc => doc.id !== id), docToDelete].sort((a, b) => a.id - b.id);
        setDocuments(restoredDocuments);
      }
      alert('删除文档失败，请稍后重试');
      console.error('Delete document error:', err);
    }
  };

  // 预览文档
  const handlePreviewDocument = (id: number, name: string) => {
    setPreviewDocument({ id, name });
  };

  // 关闭预览
  const handleClosePreview = () => {
    setPreviewDocument(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      {/* 头部面包屑 */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Link href="/projects" className="hover:text-blue-600">
              项目管理
            </Link>
            <i className="ri-arrow-right-s-line"></i>
            <span className="text-gray-900 font-medium">{project.name}</span>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 animate-fadeIn">
        {/* 项目标题区域 */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-8">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-4">
                <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(project.status)}`}>
                  {getStatusText(project.status)}
                </span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(project.riskLevel)}`}>
                  {getRiskText(project.riskLevel)}
                </span>
              </div>
              <p className="text-gray-600 mb-4">项目描述</p>
              <div className="flex items-center space-x-6 text-sm text-gray-500">
                <span>类型：{project.type === 'enterprise' ? '企业征信' : '个人征信'}</span>
                <span>创建时间：{project.lastUpdate}</span>
                <span>更新时间：{project.lastUpdate}</span>
                <span>信用评分：<span className="font-semibold text-blue-600">{project.score}</span></span>
              </div>
            </div>
            <div className="flex space-x-3 ml-6">
              <button
                onClick={() => setShowEditModal(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium whitespace-nowrap"
              >
                <i className="ri-edit-line mr-2"></i>
                编辑项目
              </button>
              <button
                onClick={handleDownloadReport}
                disabled={reportGenerating}
                className={`px-4 py-2 text-white rounded-lg transition-colors text-sm font-medium whitespace-nowrap ${
                  reportGenerating
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-green-600 hover:bg-green-700'
                }`}
              >
                {reportGenerating ? (
                  <>
                    <div className="inline-block animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                    生成中...
                  </>
                ) : (
                  <>
                    <i className="ri-file-text-line mr-2"></i>
                    生成征信报告
                  </>
                )}
              </button>
              <button
                onClick={() => setShowReportPreview(true)}
                disabled={!reportGenerated}
                className={`px-4 py-2 text-white rounded-lg transition-colors text-sm font-medium whitespace-nowrap ${
                  !reportGenerated
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                <i className="ri-eye-line mr-2"></i>
                预览报告及下载
              </button>
            </div>
          </div>

          {/* 进度条 */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">项目进度</span>
              <span className="text-sm text-gray-500">{project.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${project.progress}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* 标签页导航 */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <i className={`${tab.icon} mr-2`}></i>
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>

          {/* 标签页内容 */}
          <div className="p-6">
            {activeTab === 'overview' && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                  {/* 关键指标 */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-blue-50 rounded-lg p-4">
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                          <i className="ri-trophy-line text-white text-sm"></i>
                        </div>
                        <div className="ml-3">
                          <p className="text-sm text-gray-600">信用评分</p>
                          <p className="text-xl font-bold text-blue-600">{project.score}</p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4">
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center">
                          <i className="ri-shield-check-line text-white text-sm"></i>
                        </div>
                        <div className="ml-3">
                          <p className="text-sm text-gray-600">风险等级</p>
                          <p className="text-lg font-bold text-green-600">{project.riskLevel}</p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-purple-50 rounded-lg p-4">
                      <div className="flex items-center">
                        <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
                          <i className="ri-bar-chart-line text-white text-sm"></i>
                        </div>
                        <div className="ml-3">
                          <p className="text-sm text-gray-600">完成度</p>
                          <p className="text-xl font-bold text-purple-600">{project.progress}%</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 详细信息 - 企业/个人不同展示 */}
                  {project.type === 'enterprise' ? (
                    <div className="bg-gray-50 rounded-lg p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">企业基本信息</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-gray-600">注册资本</p>
                          <p className="font-medium text-gray-900">暂无数据</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">成立日期</p>
                          <p className="font-medium text-gray-900">暂无数据</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">所属行业</p>
                          <p className="font-medium text-gray-900">暂无数据</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">员工规模</p>
                          <p className="font-medium text-gray-900">暂无数据</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">法定代表人</p>
                          <p className="font-medium text-gray-900">暂无数据</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">经营范围</p>
                          <p className="font-medium text-gray-900">暂无数据</p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-gray-50 rounded-lg p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">个人基本信息</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-gray-600">年龄</p>
                          <p className="font-medium text-gray-900">暂无数据</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">学历</p>
                          <p className="font-medium text-gray-900">暂无数据</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">职业</p>
                          <p className="font-medium text-gray-900">暂无数据</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">工作年限</p>
                          <p className="font-medium text-gray-900">暂无数据</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">月收入</p>
                          <p className="font-medium text-gray-900">暂无数据</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">婚姻状况</p>
                          <p className="font-medium text-gray-900">暂无数据</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* 侧边栏 */}
                <div className="space-y-6">
                  {/* 报告下载状态 */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">征信报告</h4>
                    {project.progress >= 75 ? (
                      <div className="space-y-3">
                        <div className="flex items-center text-green-600">
                          <i className="ri-checkbox-circle-fill mr-2"></i>
                          <span className="text-sm">报告已生成</span>
                        </div>
                        <button
                          onClick={handleDownloadReport}
                          className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium whitespace-nowrap"
                        >
                          <i className="ri-download-line mr-2"></i>
                          立即下载
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div className="flex items-center text-yellow-600">
                          <i className="ri-time-line mr-2"></i>
                          <span className="text-sm">报告生成中...</span>
                        </div>
                        <div className="text-xs text-gray-500">
                          预计还需 {Math.ceil((100 - project.progress) / 25)} 个工作日完成
                        </div>
                        <button
                          onClick={() => setShowDownloadModal(true)}
                          className="w-full px-4 py-2 bg-gray-300 text-gray-500 rounded-lg cursor-not-allowed text-sm font-medium whitespace-nowrap"
                          disabled
                        >
                          <i className="ri-download-line mr-2"></i>
                          暂不可下载
                        </button>
                      </div>
                    )}
                  </div>

                  {/* 快速操作 */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-900 mb-3">快速操作</h4>
                    <div className="space-y-2">
                      <button
                        onClick={handleAddDocument}
                        className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-white rounded-md transition-colors"
                      >
                        <i className="ri-file-add-line mr-2"></i>添加文档
                      </button>
                      <button className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-white rounded-md transition-colors">
                        <i className="ri-refresh-line mr-2"></i>更新数据
                      </button>
                      <button className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-white rounded-md transition-colors">
                        <i className="ri-calendar-line mr-2"></i>设置提醒
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 企业特有标签页 */}
            {project.type === 'enterprise' && activeTab === 'financial' && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900">财务指标</h3>
                  {financialLoading ? (
                    <div className="bg-gray-50 rounded-lg p-4 flex items-center justify-center h-32">
                      <p className="text-gray-500">加载财务数据中...</p>
                    </div>
                  ) : financialData ? (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-gray-600">资产总额</p>
                          <p className="text-xl font-bold text-blue-600">
                            {financialData.assets?.current ? `${(financialData.assets.current / 10000).toFixed(1)}万元` : '暂无数据'}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">营业收入</p>
                          <p className="text-xl font-bold text-green-600">
                            {financialData.revenue?.current ? `${(financialData.revenue.current / 10000).toFixed(1)}万元` : '暂无数据'}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">净利润</p>
                          <p className="text-xl font-bold text-purple-600">
                            {financialData.profit?.current ? `${financialData.profit.current}万元` : '暂无数据'}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">负债总额</p>
                          <p className="text-xl font-bold text-yellow-600">
                            {financialData.liabilities?.current ? `${(financialData.liabilities.current / 10000).toFixed(1)}万元` : '暂无数据'}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">收入增长率</p>
                          <p className="text-xl font-bold text-indigo-600">
                            {financialData.revenue?.growth ? `${financialData.revenue.growth}%` : '暂无数据'}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">利润增长率</p>
                          <p className="text-xl font-bold text-pink-600">
                            {financialData.profit?.growth ? `${financialData.profit.growth}%` : '暂无数据'}
                          </p>
                        </div>
                      </div>
                      <div className="mt-4 pt-4 border-t border-gray-200">
                        <p className="text-xs text-gray-500">
                          财务数据概览（暂时使用默认数据）
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-gray-50 rounded-lg p-4 flex items-center justify-center h-32">
                      <p className="text-gray-500">暂无财务数据</p>
                    </div>
                  )}
                </div>
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900">财务比率分析</h3>
                  {financialData ? (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">资产增长率</span>
                          <span className="font-medium">{financialData.assets?.growth ? `${financialData.assets.growth}%` : '暂无数据'}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">收入增长率</span>
                          <span className={`font-medium ${financialData.revenue?.growth && financialData.revenue.growth > 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {financialData.revenue?.growth ? `${financialData.revenue.growth}%` : '暂无数据'}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">利润增长率</span>
                          <span className={`font-medium ${financialData.profit?.growth && financialData.profit.growth > 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {financialData.profit?.growth ? `${financialData.profit.growth}%` : '暂无数据'}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">负债增长率</span>
                          <span className={`font-medium ${financialData.liabilities?.growth && financialData.liabilities.growth > 0 ? 'text-red-600' : 'text-green-600'}`}>
                            {financialData.liabilities?.growth ? `${financialData.liabilities.growth}%` : '暂无数据'}
                          </span>
                        </div>

                      </div>
                    </div>
                  ) : (
                    <div className="bg-gray-50 rounded-lg p-4 h-64 flex items-center justify-center">
                      <p className="text-gray-500">暂无财务比率数据</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {project.type === 'enterprise' && activeTab === 'business' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-6">经营状况分析</h3>
                {businessLoading ? (
                  <div className="flex items-center justify-center h-32">
                    <p className="text-gray-500">加载经营状况数据中...</p>
                  </div>
                ) : businessStatus ? (
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="border border-gray-200 rounded-lg p-4">
                        <h4 className="font-semibold text-gray-900 mb-3">经营状态</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">运营状态</span>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${businessStatus.operatingStatus === 'normal' ? 'bg-green-100 text-green-800' : businessStatus.operatingStatus === 'warning' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                              {businessStatus.operatingStatus === 'normal' ? '正常' : businessStatus.operatingStatus === 'warning' ? '预警' : '风险'}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">信用评级</span>
                            <span className="font-medium text-blue-600">{businessStatus.creditRating}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">风险等级</span>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${businessStatus.riskLevel === 'low' ? 'bg-green-100 text-green-800' : businessStatus.riskLevel === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                              {businessStatus.riskLevel === 'low' ? '低风险' : businessStatus.riskLevel === 'medium' ? '中风险' : '高风险'}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="border border-gray-200 rounded-lg p-4">
                        <h4 className="font-semibold text-gray-900 mb-3">合规评估</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">合规评分</span>
                            <span className="text-lg font-bold text-blue-600">{businessStatus.complianceScore}/100</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">市场地位</span>
                            <span className="font-medium text-green-600">{businessStatus.marketPosition}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-semibold text-gray-900 mb-3">业务范围</h4>
                      <div className="flex flex-wrap gap-2">
                        {businessStatus.businessScope.map((scope, index) => (
                          <span key={index} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                            {scope}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="text-xs text-gray-500 text-center">
                      经营状况概览（暂时使用默认数据）
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-32">
                    <p className="text-gray-500">暂无经营状况数据</p>
                  </div>
                )}
              </div>
            )}

            {/* 个人特有标签页 */}
            {project.type === 'individual' && activeTab === 'credit' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-6">信用记录详情</h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-semibold text-gray-900 mb-3">信贷记录</h4>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">信用卡数量</span>
                          <span className="font-medium">3张</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">贷款笔数</span>
                          <span className="font-medium">1笔</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">逾期次数</span>
                          <span className="font-medium text-green-600">0次</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">征信查询次数</span>
                          <span className="font-medium">12次/年</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-semibold text-gray-900 mb-3">还款能力</h4>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">月收入</span>
                          <span className="font-medium">暂无数据</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">月支出</span>
                          <span className="font-medium">12000元</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">负债收入比</span>
                          <span className="font-medium text-green-600">25%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">可贷额度</span>
                          <span className="font-medium text-blue-600">80万元</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {project.type === 'individual' && activeTab === 'income' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-6">收入分析报告</h3>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-2">
                    <div className="bg-gray-50 rounded-lg p-6 h-64 flex items-center justify-center">
                      <p className="text-gray-500">收入趋势图表</p>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-semibold text-gray-900 mb-3">收入构成</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">工资收入</span>
                          <span className="font-medium">85%</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">投资收益</span>
                          <span className="font-medium">10%</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">其他收入</span>
                          <span className="font-medium">5%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 通用标签页 */}
            {activeTab === 'documents' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-gray-900">项目文档</h3>
                  <button 
                    onClick={handleAddDocument}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium whitespace-nowrap"
                  >
                    <i className="ri-upload-line mr-2"></i>
                    上传文档
                  </button>
                </div>
                {documentsLoading ? (
                  <div className="flex items-center justify-center h-32">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-2"></div>
                      <p className="text-gray-600 text-sm">加载文档列表...</p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {documents.length > 0 ? documents.map((doc) => (
                      <div key={doc.id} className="flex items-center space-x-4 p-4 border border-gray-100 rounded-lg hover:bg-gray-50 transition-all duration-200 ease-in-out transform hover:scale-[1.01] hover:shadow-md">
                        <div className="w-10 h-10 flex items-center justify-center rounded-lg bg-gray-100">
                          <i className={`${getFileIcon(doc.type)} text-lg`}></i>
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <h4 className="font-medium text-gray-800 truncate">{doc.name}</h4>
                          </div>
                          <div className="flex items-center text-sm text-gray-600 space-x-4">
                            <span>{doc.project}</span>
                            <span>•</span>
                            <span>{doc.size}</span>
                            <span>•</span>
                            <span>{doc.uploadTime}</span>
                          </div>
                          
                          {(doc.status === 'uploading' || doc.status === 'processing' || doc.status === 'uploading_to_kb' || doc.status === 'parsing_kb') && (
                            <div className="mt-2 flex items-center space-x-2">
                              <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-blue-600"></div>
                              <span className="text-xs text-gray-600">
                                {doc.status === 'uploading' && '正在上传...'}
                                {doc.status === 'processing' && '正在处理文件...'}
                                {doc.status === 'uploading_to_kb' && '正在上传到知识库...'}
                                {doc.status === 'parsing_kb' && '正在知识库中解析...'}
                              </span>
                            </div>
                          )}
                          
                          {(doc.status === 'failed' || doc.status === 'kb_parse_failed') && (
                            <div className="mt-2 flex items-center space-x-2">
                              <button
                                onClick={() => handleRetryDocument(doc.id, doc.name)}
                                className="text-xs bg-orange-600 text-white px-2 py-1 rounded hover:bg-orange-700 transition-colors"
                              >
                                重试处理
                              </button>
                            </div>
                          )}
                        </div>
                        
                        <div className="flex items-center space-x-3">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getDocumentStatusColor(doc.status)}`}>
                            {getDocumentStatusText(doc.status)}
                          </span>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => handleDownloadDocument(doc.id, doc.name)}
                              className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-200 transition-all duration-200 btn-hover-scale"
                              title="下载文档"
                            >
                              <i className="ri-download-line text-gray-600"></i>
                            </button>
                            <button
                              onClick={() => handlePreviewDocument(doc.id, doc.name)}
                              className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-blue-100 transition-all duration-200 btn-hover-scale"
                              title="预览文档"
                              disabled={doc.status !== 'completed'}
                            >
                              <i className={`ri-eye-line ${doc.status === 'completed' ? 'text-blue-600' : 'text-gray-400'}`}></i>
                            </button>
                            <button
                              onClick={() => handleDeleteDocument(doc.id)}
                              className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-red-100 transition-all duration-200 btn-hover-scale"
                              title="删除文档"
                            >
                              <i className="ri-delete-bin-line text-red-600"></i>
                            </button>
                          </div>
                        </div>
                      </div>
                    )) : (
                      <div className="text-center py-8">
                        <i className="ri-file-list-line text-4xl text-gray-300 mb-2"></i>
                        <p className="text-gray-500">暂无文档</p>
                        <p className="text-sm text-gray-400 mt-1">点击上传文档按钮添加项目相关文档</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'timeline' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-6">项目时间轴</h3>
                {timelineLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <span className="ml-2 text-gray-600">加载时间轴数据...</span>
                  </div>
                ) : (timelineEvents && timelineEvents.length > 0) ? (
                  <div className="space-y-4">
                    {timelineEvents.map((item, index) => (
                      <div key={item.id || index} className="flex items-start">
                        <div
                          className={`w-3 h-3 rounded-full mt-2 mr-4 flex-shrink-0 ${
                            item.status === 'completed' ? 'bg-green-500' :
                            item.status === 'processing' ? 'bg-blue-500' : 'bg-gray-300'
                          }`}
                        ></div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <h4 className="font-medium text-gray-900">{item.title || '未命名事件'}</h4>
                            <span className="text-sm text-gray-500">
                              {item.date ? new Date(item.date).toLocaleDateString('zh-CN') : '未知日期'}
                            </span>
                          </div>
                          {item.description && (
                            <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                          )}
                          <div className="flex items-center justify-between mt-2">
                            <div
                              className={`inline-flex px-2 py-1 rounded-full text-xs ${
                                item.status === 'completed'
                                  ? 'bg-green-100 text-green-800'
                                  : item.status === 'processing'
                                  ? 'bg-blue-100 text-blue-800'
                                  : 'bg-gray-100 text-gray-600'
                              }`}
                            >
                              {item.status === 'completed' ? '已完成' :
                               item.status === 'processing' ? '进行中' : '待处理'}
                            </div>

                          </div>

                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <i className="ri-time-line text-4xl mb-2 block"></i>
                    <p>暂无时间轴数据</p>
                    <p className="text-sm mt-1">项目创建后，相关事件将在此处显示</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'progress' && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-6">进度详情</h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-3">任务进度</h4>
                      <div className="space-y-3">
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>数据收集</span>
                            <span>100%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div className="bg-green-500 h-2 rounded-full" style={{ width: '100%' }}></div>
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>风险分析</span>
                            <span>85%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div className="bg-blue-500 h-2 rounded-full" style={{ width: '85%' }}></div>
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>报告生成</span>
                            <span>60%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div className="bg-yellow-500 h-2 rounded-full" style={{ width: '60%' }}></div>
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>审核验证</span>
                            <span>30%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div className="bg-red-500 h-2 rounded-full" style={{ width: '30%' }}></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-3">里程碑</h4>
                      <div className="space-y-3">
                        <div className="flex items-center">
                          <i className="ri-checkbox-circle-fill text-green-500 mr-3"></i>
                          <span className="text-sm">项目启动</span>
                        </div>
                        <div className="flex items-center">
                          <i className="ri-checkbox-circle-fill text-green-500 mr-3"></i>
                          <span className="text-sm">数据收集完成</span>
                        </div>
                        <div className="flex items-center">
                          <i className="ri-checkbox-circle-line text-blue-500 mr-3"></i>
                          <span className="text-sm">初步分析完成</span>
                        </div>
                        <div className="flex items-center">
                          <i className="ri-checkbox-circle-line text-gray-400 mr-3"></i>
                          <span className="text-sm text-gray-500">最终报告提交</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 编辑项目弹窗 */}
      {showEditModal && (
        <CreateProjectModal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          onSuccess={() => {
            setShowEditModal(false);
            // 重新加载项目数据
            router.refresh();
          }}
          editData={getEditData()}
        />
      )}

      {/* 下载提示弹窗 */}
      {showDownloadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center">
                <i className="ri-information-line text-yellow-600"></i>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 ml-3">征信报告暂未完成</h3>
            </div>
            <p className="text-gray-600 mb-6">
              当前项目进度为 {project.progress}%，征信分析报告正在处理中。请等待项目完成度达到75%以上后再下载完整报告。
            </p>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowDownloadModal(false)}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 文档预览模态框 */}
      {previewDocument && (
        <DocumentPreview
          documentId={previewDocument.id}
          documentName={previewDocument.name}
          isOpen={!!previewDocument}
          onClose={handleClosePreview}
        />
      )}

      {/* 报告预览模态框 */}
      <ReportPreview
        isOpen={showReportPreview}
        onClose={() => setShowReportPreview(false)}
        workflowRunId={workflowRunId}
        companyName={project?.name || ''}
        projectId={project?.id}
        isGenerating={reportGenerating}
        onReportDeleted={() => {
          // 报告删除后的回调
          setReportGenerated(false);
          setWorkflowRunId(null);
          // 刷新页面以更新项目数据
          window.location.reload();
        }}
      />
    </div>
  );
}
