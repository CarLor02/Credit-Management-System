'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import MarkdownPreview from '@uiw/react-markdown-preview';
import { apiClient } from '../services/api';
import websocketService from '../services/websocketService';
import PdfViewer from './PDFViewer';
import { streamingContentService, StreamingEvent, ProjectStreamingData } from '../services/streamingContentService';
import { useNotification } from '@/contexts/NotificationContext';
import { useConfirm } from '@/contexts/ConfirmContext';


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
  // hasStreamingContent 已删除，我们只依据 generating 状态
  const streamingContentRef = useRef<HTMLDivElement>(null);
  const eventsRef = useRef<HTMLDivElement>(null);
  const { addNotification } = useNotification();
  const { showConfirm } = useConfirm();

  // 注意：fixHeadingFormat 函数已被移除，因为预处理逻辑已简化

  // 简化的Markdown预处理，只处理关键问题
  const preprocessMarkdown = (content: string): string => {
    if (!content) return content;

    let processedContent = content;

    // 1. 清理Markdown代码块标记
    processedContent = processedContent
      .replace(/```markdown\s*\n/gi, '')
      .replace(/```\s*$/gm, '')
      .replace(/```[\w]*\s*\n/gi, '')
      .replace(/```\s*\n/gi, '');

    // 2. 确保标题前有换行符（核心修复）
    processedContent = processedContent
      // 在标题前添加双换行符（除了文档开头）
      .replace(/([^\n])(#{1,6}\s)/g, '$1\n\n$2')
      // 确保#号后面有空格
      .replace(/^(#{1,6})([^#\s])/gm, '$1 $2');

    // 3. 处理没有#号的标题行
    processedContent = processedContent.replace(/^(\s*)(第[一二三四五六七八九十\d]+[节章][^\n]*)/gm, (match, spaces, title) => {
      if (!title.startsWith('#')) {
        return `${spaces}\n\n### ${title}`;
      }
      return match;
    });

    // 4. 强化表格格式修复
    processedContent = processedContent
      // 修复表格单元格格式
      .replace(/\|([^|\n]*)\|/g, (_, content) => `| ${content.trim()} |`)
      // 确保表格前后有空行
      .replace(/([^\n])\n(\|)/g, '$1\n\n$2')
      .replace(/(\|[^\n]*)\n([^|\n])/g, '$1\n\n$2')
      // 修复可能缺失的表格分隔行
      .replace(/(\|[^|\n]*\|)\n(\|[^|\n]*\|)/g, (match, header, firstRow) => {
        // 如果表格头后面直接跟数据行，插入分隔行
        if (!firstRow.includes('---') && !firstRow.includes(':--') && !header.includes('---')) {
          const columnCount = (header.match(/\|/g) || []).length - 1;
          if (columnCount > 0) {
            const separator = '|' + ' --- |'.repeat(columnCount);
            return header + '\n' + separator + '\n' + firstRow;
          }
        }
        return match;
      });

    // 5. 清理过多的连续空行
    processedContent = processedContent.replace(/\n{4,}/g, '\n\n\n');

    return processedContent.trim();

    // 调试：打印处理前后的标题行
    if (content !== processedContent) {
      const originalTitles = content.match(/^#{1,6}.*$/gm) || [];
      const processedTitles = processedContent.match(/^#{1,6}.*$/gm) || [];
      const allTitleLikeLines = processedContent.match(/^.*第[一二三四五六七八九十\d]+[节章].*$/gm) || [];
      const unprocessedTitleLike = content.match(/^[^#]*第[一二三四五六七八九十\d]+[节章].*$/gm) || [];

      console.log('📝 Markdown标题预处理 (分段生成优化版):', {
        原始标题数量: originalTitles.length,
        处理后标题数量: processedTitles.length,
        所有标题样式行数量: allTitleLikeLines.length,
        未处理的标题样式: unprocessedTitleLike.length,
        原始标题: originalTitles.slice(0, 5),
        处理后标题: processedTitles.slice(0, 5),
        标题样式行示例: allTitleLikeLines.slice(0, 5),
        未处理标题示例: unprocessedTitleLike.slice(0, 3)
      });
    }

    return processedContent;
  };

  // 从流式内容服务加载数据
  useEffect(() => {
    if (projectId) {
      const streamingData = streamingContentService.getProjectData(projectId);
      if (streamingData) {
        setStreamingEvents(streamingData.events);
        setGenerating(streamingData.isGenerating);
        if (streamingData.reportContent) {
          setReportContent(streamingData.reportContent);
        }
        // hasStreamingContent 已删除，不再使用
      }

      // 添加监听器
      const handleStreamingUpdate = (data: ProjectStreamingData) => {
        setStreamingEvents(data.events);
        setGenerating(data.isGenerating);
        if (data.reportContent) {
          setReportContent(data.reportContent);
        }
        // hasStreamingContent 已删除，不再使用
      };

      streamingContentService.addListener(projectId, handleStreamingUpdate);

      return () => {
        streamingContentService.removeListener(projectId, handleStreamingUpdate);
      };
    }
  }, [projectId]);

  // 防抖和缓存相关状态
  const [lastFetchTime, setLastFetchTime] = useState<number>(0);
  const fetchDebounceRef = useRef<NodeJS.Timeout | null>(null);
  const FETCH_COOLDOWN = 2000; // 2秒冷却时间，防止频繁请求

  // 使用useCallback稳定函数引用，避免useEffect过度触发
  const fetchReportContent = useCallback(async (force: boolean = false) => {
    if (!projectId) return;
    // 🔧 修复：只有在真正生成中时才跳过获取报告内容，不应该因为有历史流式内容就跳过
    if (generating) {
      console.log('📄 跳过获取报告内容，正在生成中');
      return;
    }
    // 防抖机制：短时间内的重复调用只执行最后一次
    if (fetchDebounceRef.current) {
      clearTimeout(fetchDebounceRef.current);
    }

    // 缓存机制：2秒内不重复请求（除非强制刷新）
    const now = Date.now();
    if (!force && (now - lastFetchTime) < FETCH_COOLDOWN) {
      console.log('📄 跳过频繁请求，距离上次请求:', now - lastFetchTime, 'ms');
      return;
    }

    fetchDebounceRef.current = setTimeout(async () => {
      setLoading(true);
      setError(null);
      setLastFetchTime(Date.now());

      try {
        const response = await apiClient.get<{
          success: boolean;
          content: string;
          file_path: string;
          company_name: string;
          has_report: boolean;
        }>(`/projects/${projectId}/report`);

        if (response.success) {
          if (response.data?.has_report) {
            setReportContent(response.data.content || '');
            setError(null); // 清除错误状态
          } else {
            // 只有在报告不在生成过程中时才清空内容和显示错误信息
            if (!generating) {
              setReportContent('');
              setError('该项目尚未生成报告');
            } else {
              // 生成过程中不清空内容，保持流式内容
              setError(null); // 生成过程中不显示错误
            }
          }
        } else {
          setError(response.error || '获取报告内容失败');
        }
      } catch (err) {
        // 对于404错误（报告不存在），使用info级别日志
        const errorMessage = err instanceof Error ? err.message : String(err);
        if (errorMessage.includes('该项目尚未生成报告') || errorMessage.includes('404')) {
          console.info('项目暂无报告:', errorMessage);
          setError('该项目尚未生成报告');
        } else {
          console.error('获取报告内容失败:', err);
          setError('获取报告内容失败，请稍后重试');
        }
      } finally {
        setLoading(false);
      }
    }, 300); // 300ms防抖延迟
  }, [projectId, generating, lastFetchTime]);

  // 获取HTML格式的报告内容
  const fetchHtmlContent = useCallback(async () => {
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
        // 对于404错误（报告不存在），使用info级别日志
        const errorMessage = response.error || '';
        if (errorMessage.includes('该项目尚未生成报告') || errorMessage.includes('404')) {
          console.info('项目暂无HTML报告:', errorMessage);
        } else {
          console.error('获取HTML内容失败:', response.error);
        }
      }
    } catch (err) {
      // 对于404错误（报告不存在），使用info级别日志
      const errorMessage = err instanceof Error ? err.message : String(err);
      if (errorMessage.includes('该项目尚未生成报告') || errorMessage.includes('404')) {
        console.info('项目暂无HTML报告:', errorMessage);
      } else {
        console.error('获取HTML内容失败:', err);
      }
    } finally {
      setHtmlLoading(false);
    }
  }, [projectId]);





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
          // 根据Dify API格式，节点信息在event_data.data中
          const nodeTitle = eventData?.event_data?.data?.title || eventData?.data?.title;
          const nodeId = eventData?.event_data?.data?.node_id || eventData?.data?.node_id;

          if (nodeTitle) {
            detailInfo = `[${nodeId || '节点'}] ${nodeTitle}`;
            eventColor = 'text-blue-400';
          } else if (nodeId) {
            detailInfo = `节点启动: ${nodeId}`;
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
          // 根据Dify API格式，节点信息在event_data.data中
          const finishedNodeTitle = eventData?.event_data?.data?.title || eventData?.data?.title;
          const finishedNodeId = eventData?.event_data?.data?.node_id || eventData?.data?.node_id;

          if (finishedNodeTitle) {
            detailInfo = `[${finishedNodeId || '节点'}] ${finishedNodeTitle}`;
            eventColor = 'text-green-400';
          } else if (finishedNodeId) {
            detailInfo = `节点完成: ${finishedNodeId}`;
            eventColor = 'text-green-400';
          } else {
            detailInfo = '节点完成';
            eventColor = 'text-green-400';
          }
          break;
        case 'workflow_started':
          detailInfo = '工作流开始';
          eventColor = 'text-cyan-400';
          break;
        case 'workflow_complete':
          detailInfo = '工作流完成';
          eventColor = 'text-green-500';
          setGenerating(false);
          break;
        case 'start_generating':
          detailInfo = '开始生成报告';
          eventColor = 'text-blue-500';
          setGenerating(true);
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

      // 区分事件类型处理
      if (eventType === 'content_generated' || eventType === 'markdown_content') {
        // 内容事件直接更新报告内容，并自动滚动
        setReportContent(prev => {
          let processedContent = content.replace(/\r?\n/g, '\n');

          // 特殊处理：如果新内容以标题开始，确保前面有足够的换行符
          const trimmedContent = processedContent.trim();
          if (trimmedContent.match(/^#{1,6}\s/) || trimmedContent.match(/^第[一二三四五六七八九十\d]+[节章]/)) {
            // 如果前面有内容且不是以换行结尾，添加双换行
            if (prev && !prev.endsWith('\n\n')) {
              if (prev.endsWith('\n')) {
                processedContent = '\n' + processedContent;
              } else {
                processedContent = '\n\n' + processedContent;
              }
            }
          }

          // 如果内容看起来像标题但没有#号，添加###
          if (trimmedContent.match(/^第[一二三四五六七八九十\d]+[节章]/) && !trimmedContent.startsWith('#')) {
            processedContent = processedContent.replace(/^(\s*)(第[一二三四五六七八九十\d]+[节章][^\n]*)/m, '$1### $2');
          }

          const newContent = prev ? prev + processedContent : processedContent;

          // 立即滚动，然后再延迟滚动确保DOM更新完成
          const scrollToBottom = () => {
            if (streamingContentRef.current) {
              streamingContentRef.current.scrollTop = streamingContentRef.current.scrollHeight;
            }
          };

          // 立即执行一次
          scrollToBottom();

          // 延迟执行确保DOM完全更新
          setTimeout(scrollToBottom, 10);
          setTimeout(scrollToBottom, 100);
          return newContent;
        });
        return;
      }

      // 节点状态事件添加到事件列表
      const eventEntry = {
        timestamp,
        eventType,
        content: detailInfo,
        color: eventColor,
        isContent: false
      };

      console.log('📝 添加节点事件到界面:', eventEntry);

      // 保存到流式内容服务
      if (projectId) {
        streamingContentService.addEvent(projectId, eventEntry);
      }

      setStreamingEvents(prev => [...prev, eventEntry]);

      // 自动滚动事件列表
      setTimeout(() => {
        if (eventsRef.current) {
          eventsRef.current.scrollTop = eventsRef.current.scrollHeight;
        }
      }, 100);
    };

    // WebSocket已在项目详情页连接，这里需要加入项目房间并设置监听器
    const projectRoom = `project_${projectId}`;
    console.log('🏠 加入项目房间:', projectRoom);
    websocketService.joinWorkflow(projectRoom);
    setWebsocketStatus(`监听房间: ${projectRoom}`);

    // 添加测试事件验证功能
    addEvent('预览窗口打开', '开始监听流式事件');



    // 定义事件处理函数，以便后续清理
    const handleWorkflowEvent = (data: any) => {
      console.log('🎯 收到workflow_event:', data);

      // 调试：打印所有事件的详细信息
      console.log('📊 收到事件详情:', {
        event_type: data.event_type,
        event_data: data.event_data,
        data: data.data,
        raw_data: JSON.stringify(data, null, 2)
      });

      // 特别关注节点事件
      if (data.event_type === 'node_started' || data.event_type === 'node_finished') {
        console.log('🎯 节点事件解析:', {
          title_from_event_data_data: data.event_data?.data?.title,
          title_from_event_data: data.event_data?.title,
          title_from_data: data.data?.title,
          node_id_from_event_data_data: data.event_data?.data?.node_id,
          node_id_from_event_data: data.event_data?.node_id,
          node_id_from_data: data.data?.node_id
        });
      }

      const eventType = data.event_type || '工作流事件';
      addEvent(eventType, '', data);

      // 处理章节完成事件
      if (projectId) {
        streamingContentService.handleChapterComplete(projectId, data);
      }

      if (eventType === 'generation_started' || eventType === 'workflow_started') {
        setGenerating(true);
        // 清空旧的报告内容，确保显示生成状态
        setReportContent('');
        // 不要立即设置hasStreamingContent为false，避免触发报告获取
        // setHasStreamingContent(false);
        setError(null);

        if (projectId) {
          streamingContentService.setGeneratingStatus(projectId, true);
          // 清空流式内容服务中的旧内容
          streamingContentService.updateReportContent(projectId, '');
        }
        console.log('🚀 开始生成报告，设置generating为true，清空旧内容');
      }
    };

    const handleWorkflowContent = (data: any) => {
      console.log('📄 收到workflow_content:', data);
      if (data.content_chunk) {
        // 调试：打印原始内容块
        console.log('📄 原始content_chunk:', JSON.stringify(data.content_chunk));
        console.log('📄 content_chunk长度:', data.content_chunk.length);

        // hasStreamingContent 已删除，不再使用
        // 直接更新报告内容到右侧显示区域
        setReportContent(prev => {
          // 保持原始内容，不进行任何替换
          const newContent = prev ? prev + data.content_chunk : data.content_chunk;
          console.log('✅ 更新报告内容，新长度:', newContent.length);
          console.log('✅ 最新添加的内容:', JSON.stringify(data.content_chunk));

          // 保存到流式内容服务
          if (projectId) {
            streamingContentService.updateReportContent(projectId, newContent);
          }

          // 立即滚动，然后再延迟滚动确保DOM更新完成
          const scrollToBottom = () => {
            if (streamingContentRef.current) {
              streamingContentRef.current.scrollTop = streamingContentRef.current.scrollHeight;
            }
          };

          // 立即执行一次
          scrollToBottom();

          // 延迟执行确保DOM完全更新
          setTimeout(scrollToBottom, 10);
          setTimeout(scrollToBottom, 100);
          return newContent;
        });
        // 清除错误状态，确保内容能够显示
        setError(null);
        // 同时也在左侧事件列表中显示内容块信息
        //addEvent('内容块', `${data.content_chunk}`);
      }
    };

    const handleWorkflowComplete = (data: any) => {
      console.log('✅ 收到workflow_complete:', data);

      // 验证事件是否属于当前项目
      const eventProjectId = data.project_id;
      if (eventProjectId && eventProjectId !== projectId) {
        console.log(`🚫 ReportPreview忽略其他项目(${eventProjectId})的workflow_complete事件，当前项目ID: ${projectId}`);
        return;
      }

      addEvent('报告生成完成', '');
      setWebsocketStatus('生成完成');
      setGenerating(false);

      // 更新流式内容服务状态
      if (projectId) {
        streamingContentService.setGeneratingStatus(projectId, false);
      }

      // 优先使用完成事件中的最终内容，否则从文件加载最新内容
      if (data.final_content) {
        console.log('✅ 使用完成事件中的最终内容');
        setReportContent(data.final_content);
        if (projectId) {
          streamingContentService.updateReportContent(projectId, data.final_content);
        }
        // 同时获取HTML内容
        fetchHtmlContent();
      } else {
        console.log('✅ 从文件加载最终报告内容');
        fetchReportContent(true); // 强制刷新，获取最新内容
        fetchHtmlContent();
      }
    };

    const handleWorkflowError = (data: any) => {
      console.log('❌ 收到workflow_error:', data);

      // 验证事件是否属于当前项目
      const eventProjectId = data.project_id;
      if (eventProjectId && eventProjectId !== projectId) {
        console.log(`🚫 ReportPreview忽略其他项目(${eventProjectId})的workflow_error事件，当前项目ID: ${projectId}`);
        return;
      }

      addEvent('错误', data.error_message || '未知错误');
      setError(data.error_message);
      setGenerating(false);

      // 更新流式内容服务状态
      if (projectId) {
        streamingContentService.setGeneratingStatus(projectId, false);
      }

      console.log('❌ 报告生成出错，设置generating为false');
    };

    const handleGenerationCancelled = (data: any) => {
      console.log('🚫 收到generation_cancelled:', data);

      // 验证事件是否属于当前项目
      const eventProjectId = data.project_id;
      if (eventProjectId && eventProjectId !== projectId) {
        console.log(`🚫 ReportPreview忽略其他项目(${eventProjectId})的generation_cancelled事件，当前项目ID: ${projectId}`);
        return;
      }

      addEvent('报告生成已取消', '用户手动停止了报告生成');
      setGenerating(false);
      setWebsocketStatus('已取消');
      setError('报告生成已取消');

      // 更新流式内容服务状态
      if (projectId) {
        streamingContentService.setGeneratingStatus(projectId, false);
      }

      console.log('🚫 报告生成已取消，设置generating为false');
    };

    // 监听WebSocket连接状态
    const handleWebSocketDisconnected = (data: any) => {
      console.log('WebSocket连接断开，原因:', data.reason);
      setWebsocketStatus('连接断开');
    };

    const handleWebSocketReconnected = async (data: any) => {
      console.log('WebSocket重连成功，尝试次数:', data.attemptNumber);
      setWebsocketStatus('已重连');

      // 重新加入项目房间
      if (projectId) {
        const projectRoom = `project_${projectId}`;
        websocketService.joinWorkflow(projectRoom);

        // 检查是否有正在进行的生成任务需要恢复
        if (generating) {
          console.log('🔄 检测到生成任务，尝试恢复状态');
          try {
            // 检查后端是否还有活跃的工作流
            const response = await apiClient.get(`/projects/${projectId}/generation_status`);

            if (response.success && (response as any).data?.isGenerating) {
              console.log('✅ 后端确认生成仍在进行，保持生成状态');
              setGenerating(true);
              setWebsocketStatus('生成中(已恢复)');
            } else {
              console.log('❌ 后端确认生成已停止，更新前端状态');
              setGenerating(false);
              setWebsocketStatus('已重连');
              // 更新流式内容服务状态
              if (projectId) {
                streamingContentService.setGeneratingStatus(projectId, false);
              }
            }
          } catch (error) {
            console.error('检查生成状态失败:', error);
            // 如果检查失败，保持当前状态
          }
        }
      }
    };

    const handleReconnectAttempt = (data: any) => {
      console.log('WebSocket重连尝试:', data.attemptNumber);
      setWebsocketStatus(`重连中(${data.attemptNumber})`);
    };

    // 监听WebSocket消息 - 详细展示不同类型的事件
    websocketService.on('workflow_event', handleWorkflowEvent);
    websocketService.on('workflow_content', handleWorkflowContent);
    websocketService.on('workflow_complete', handleWorkflowComplete);
    websocketService.on('workflow_error', handleWorkflowError);
    websocketService.on('generation_cancelled', handleGenerationCancelled);

    // 监听连接状态事件
    websocketService.on('disconnected', handleWebSocketDisconnected);
    websocketService.on('reconnected', handleWebSocketReconnected);
    websocketService.on('reconnect_attempt', handleReconnectAttempt);

    // 清理函数 - 移除事件监听器，防止重复注册
    return () => {
      console.log('🧹 清理事件监听器（保持WebSocket连接）');

      // 移除具体的事件监听器，防止重复注册
      websocketService.off('workflow_event', handleWorkflowEvent);
      websocketService.off('workflow_content', handleWorkflowContent);
      websocketService.off('workflow_complete', handleWorkflowComplete);
      websocketService.off('workflow_error', handleWorkflowError);
      websocketService.off('generation_cancelled', handleGenerationCancelled);
      websocketService.off('disconnected', handleWebSocketDisconnected);
      websocketService.off('reconnected', handleWebSocketReconnected);
      websocketService.off('reconnect_attempt', handleReconnectAttempt);

      // 离开项目房间
      const projectRoom = `project_${projectId}`;
      console.log('🚪 离开项目房间:', projectRoom);
      websocketService.leaveWorkflow(projectRoom);

      setWebsocketStatus('未连接');
    };
  }, [isOpen, projectId]); // eslint-disable-line react-hooks/exhaustive-deps

  // 统一的报告获取逻辑：避免多重触发和同时请求
  useEffect(() => {
    if (!isOpen) {
      // 清理防抖定时器
      if (fetchDebounceRef.current) {
        clearTimeout(fetchDebounceRef.current);
      }
      return;
    }

    // 使用单一定时器，避免状态变化时多次触发
    const timer = setTimeout(() => {
      // 🔧 修复：只有在真正生成中时才不获取报告内容
      const shouldFetch = !generating;
      
      console.log('📄 统一报告获取检查:', {
        isOpen,
        generating,
        shouldFetch,
        projectId
      });

      if (shouldFetch) {
        console.log('📄 开始获取报告内容');
        fetchReportContent();
        // 延迟获取HTML内容，避免同时请求造成负载
        setTimeout(() => {
          fetchHtmlContent();
        }, 500); // 500ms间隔
      }
    }, 200); // 200ms延迟避免状态快速变化
    
    return () => clearTimeout(timer);
  }, [isOpen, projectId, generating, fetchReportContent, fetchHtmlContent]);

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
        addNotification('请先登录', 'error');
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
      addNotification(error instanceof Error ? error.message : '下载HTML报告失败，请稍后重试', 'error');
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
        addNotification('请先登录', 'error');
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
      addNotification(error instanceof Error ? error.message : '下载PDF报告失败，请稍后重试', 'error');
    } finally {
      setLoading(false);
    }
  };

  // 删除报告
  const handleDeleteReport = async () => {
    if (!projectId || loading) return;

    const confirmed = await showConfirm({
      title: '确认删除报告',
      message: '确定要删除这个报告吗？<br><br><strong>此操作不可恢复。</strong>',
      confirmText: '确认删除',
      cancelText: '取消',
      type: 'danger'
    });

    if (!confirmed) {
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.delete(`/projects/${projectId}/report`);
      if (response.success) {
        addNotification('报告删除成功', 'success');
        onReportDeleted?.();
        onClose();
      } else {
        addNotification(response.error || '删除报告失败', 'error');
      }
    } catch (error) {
      console.error('删除报告失败:', error);
      addNotification('删除报告失败，请稍后重试', 'error');
    } finally {
      setLoading(false);
    }
  };

  // 停止报告生成
  const handleStopGeneration = async () => {
    if (!projectId) return;

    try {
      // 发送API请求停止生成
      const apiResponse = await apiClient.post(`/stop_report_generation`, { project_id: projectId });

      if (apiResponse.success) {
        setGenerating(false);

        // 更新流式内容服务状态
        streamingContentService.setGeneratingStatus(projectId, false);

        const stopEvent = {
          timestamp: new Date().toLocaleTimeString(),
          eventType: '报告生成已停止',
          content: '用户手动停止了报告生成',
          color: 'text-red-500',
          isContent: false
        };

        setStreamingEvents(prev => [...prev, stopEvent]);
        streamingContentService.addEvent(projectId, stopEvent);

        // 不要强制断开WebSocket连接，让后端处理停止逻辑
        // websocketService.disconnect();
        setWebsocketStatus('已停止');
      } else {
        throw new Error(apiResponse.error || '停止请求失败');
      }
    } catch (error) {
      console.error('停止报告生成失败:', error);

      const errorEvent = {
        timestamp: new Date().toLocaleTimeString(),
        eventType: '停止失败',
        content: error instanceof Error ? error.message : '停止报告生成失败',
        color: 'text-red-500',
        isContent: false
      };

      setStreamingEvents(prev => [...prev, errorEvent]);
      streamingContentService.addEvent(projectId, errorEvent);
    }
  };

  // 转换PDF预览
  const handleConvertToPdfPreview = async () => {
    if (!projectId || pdfLoading) return;

    try {
      setPdfLoading(true);

      const token = localStorage.getItem('auth_token');
      if (!token) {
        addNotification('请先登录', 'error');
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
      addNotification(error instanceof Error ? error.message : '转换PDF预览失败，请稍后重试', 'error');
    } finally {
      setPdfLoading(false);
    }
  };

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

  console.log('✅ ReportPreview: 渲染弹窗，isOpen:', isOpen, 'projectId:', projectId, 'companyName:', companyName);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <style>{`
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

            {/* 操作按钮组 */}
            <div className="flex items-center gap-2">
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
              {/* 停止生成按钮 - 只在真正生成过程中显示 */}
              {generating && (
                <button
                  onClick={handleStopGeneration}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors bg-orange-600 text-white hover:bg-orange-700`}
                >
                  <i className="ri-stop-circle-line mr-2"></i>
                  停止生成
                </button>
              )}
            </div>
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
                <h3 className="text-sm font-medium text-gray-300">节点工作情况</h3>

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
            {error && !generating && !reportContent ? (
              // 错误提示
              <div className="text-center py-12">
                <div className="text-red-600 mb-4">
                  <i className="ri-error-warning-line text-4xl"></i>
                </div>
                <p className="text-red-600 font-medium">{error}</p>
              </div>
            ) : loading ? (
              // 加载提示
              <div className="text-center py-12">
                <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
                <p className="text-gray-600">加载报告内容中...</p>
              </div>
            ) : isPdfPreview ? (
              // PDF预览
              pdfUrl ? (
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
                <div className="text-center py-12">
                  <div className="text-gray-400 mb-4">
                    <i className="ri-file-pdf-line text-4xl"></i>
                  </div>
                  <p className="text-gray-600">PDF加载中...</p>
                </div>
              )
            ) : (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden h-full">
                <div className="bg-gradient-to-r from-gray-50 to-green-50 px-4 py-2 border-b border-gray-200">
                  <div className="flex items-center space-x-2">
                    <i className="ri-html5-line text-green-600"></i>
                    <span className="text-sm font-medium text-gray-700">征信报告</span>
                    <span className="text-xs text-gray-500">• HTML格式</span>
                  </div>
                </div>
                <div className="overflow-y-auto h-full" style={{ height: 'calc(100% - 50px)' }}>
                  {htmlLoading ? (
                    <div className="text-center py-8">正在转换HTML格式...</div>
                  ) : htmlContent ? (
                    <iframe srcDoc={htmlContent} style={{
                      width: '100%',
                      height: '100%',
                      border: 'none',
                      backgroundColor: 'white'
                    }} title="征信报告HTML预览" sandbox="allow-same-origin" />
                  ) : generating ? (
                    // 生成过程中，优先显示流式输出
                    <div className="px-6 py-6 pb-12 bg-white min-h-full" ref={streamingContentRef}>
                      {reportContent ? (
                        <div className="report-container" style={{ backgroundColor: 'white', padding: '20px', minHeight: '100%' }}>
                          <MarkdownPreview
                            source={preprocessMarkdown(reportContent)}
                            className="max-w-none markdown-content"
                            style={{
                              backgroundColor: 'transparent',
                              color: '#374151'
                            }}
                            data-color-mode="light"
                            wrapperElement={{
                              'data-color-mode': 'light'
                            }}
                            rehypeRewrite={(node) => {
                              // 确保标题元素正确渲染
                              if (node.type === 'element' && /^h[1-6]$/.test(node.tagName)) {
                                node.properties = {
                                  ...node.properties,
                                  style: 'display: block; font-weight: 600;'
                                };
                              }
                              // 确保表格元素正确渲染
                              if (node.type === 'element' && node.tagName === 'table') {
                                node.properties = {
                                  ...node.properties,
                                  style: 'display: table; width: 100%; border-collapse: collapse;'
                                };
                              }
                            }}
                          />
                          <style jsx>{`
                            .markdown-content h1,
                            .markdown-content h2,
                            .markdown-content h3,
                            .markdown-content h4,
                            .markdown-content h5,
                            .markdown-content h6 {
                              margin-top: 1.5em !important;
                              margin-bottom: 0.5em !important;
                              line-height: 1.3 !important;
                              font-weight: 600 !important;
                              color: #1f2937 !important;
                              display: block !important;
                              border: none !important;
                              border-bottom: none !important;
                              padding-bottom: 0 !important;
                            }
                            .markdown-content h1 {
                              font-size: 1.8em !important;
                            }
                            .markdown-content h2 {
                              font-size: 1.5em !important;
                            }
                            .markdown-content h3 {
                              font-size: 1.3em !important;
                              font-weight: 600 !important;
                              color: #374151 !important;
                            }
                            .markdown-content h4 {
                              font-size: 1.1em !important;
                              font-weight: 600 !important;
                            }
                            .markdown-content p {
                              margin-bottom: 1em;
                              line-height: 1.6;
                              color: #374151 !important;
                            }
                            .markdown-content ul,
                            .markdown-content ol {
                              margin-bottom: 1em;
                              padding-left: 1.5em;
                            }
                            .markdown-content li {
                              margin-bottom: 0.3em;
                              color: #374151 !important;
                            }
                            /* 强制表格渲染 */
                            .markdown-content table {
                              border-collapse: collapse !important;
                              width: 100% !important;
                              margin: 1em 0 !important;
                              background-color: white !important;
                              border: 1px solid #d1d5db !important;
                              display: table !important;
                              font-family: inherit !important;
                            }
                            .markdown-content thead {
                              display: table-header-group !important;
                            }
                            .markdown-content tbody {
                              display: table-row-group !important;
                            }
                            .markdown-content tr {
                              display: table-row !important;
                            }
                            .markdown-content th,
                            .markdown-content td {
                              border: 1px solid #d1d5db !important;
                              padding: 8px 12px !important;
                              text-align: left !important;
                              background-color: white !important;
                              color: #374151 !important;
                              display: table-cell !important;
                              vertical-align: top !important;
                              word-wrap: break-word !important;
                              max-width: none !important;
                            }
                            .markdown-content th {
                              background-color: #f9fafb !important;
                              font-weight: 600 !important;
                              color: #1f2937 !important;
                            }
                            .markdown-content tbody tr:nth-child(even) td {
                              background-color: #f8fafc !important;
                            }
                            .markdown-content tbody tr:nth-child(odd) td {
                              background-color: white !important;
                            }

                            /* 隐藏代码块和引用块 */
                            .markdown-content pre,
                            .markdown-content code {
                              display: none !important;
                            }
                            .markdown-content blockquote {
                              display: none !important;
                            }

                            /* 确保所有内容在同一个白色背景上 */
                            .markdown-content {
                              background-color: white !important;
                              color: #374151 !important;
                            }

                            /* 移除任何可能的框架样式 */
                            .markdown-content > * {
                              border: none !important;
                              box-shadow: none !important;
                              background-color: transparent !important;
                            }

                            /* 特殊处理：确保表格不被包裹在框中 */
                            .markdown-content table {
                              box-shadow: none !important;
                              border-radius: 0 !important;
                            }
                          `}</style>
                          <div className="mt-6 mb-6 text-center">
                            <p className="text-gray-400">报告生成中，内容持续更新...</p>
                          </div>
                        </div>
                      ) : (
                        <div className="text-center py-12">
                          <div className="animate-spin w-8 h-8 border-4 border-green-600 border-t-transparent rounded-full mx-auto mb-4"></div>
                          <p className="text-gray-600">正在生成报告，请稍候...</p>
                          <p className="text-sm text-gray-400 mt-2">生成过程将在左侧实时显示</p>
                        </div>
                      )}
                    </div>
                  ) : reportContent ? (
                    // 非生成状态，显示已有报告内容
                    <div className="px-6 py-6 pb-12 bg-white min-h-full" ref={streamingContentRef}>
                      <MarkdownPreview
                        source={preprocessMarkdown(reportContent)}
                        className="max-w-none markdown-content"
                        style={{
                          backgroundColor: 'transparent',
                          color: '#374151'
                        }}
                        data-color-mode="light"
                        wrapperElement={{
                          'data-color-mode': 'light'
                        }}
                        rehypeRewrite={(node) => {
                          // 确保标题元素正确渲染
                          if (node.type === 'element' && /^h[1-6]$/.test(node.tagName)) {
                            node.properties = {
                              ...node.properties,
                              style: 'display: block; font-weight: 600;'
                            };
                          }
                          // 确保表格元素正确渲染
                          if (node.type === 'element' && node.tagName === 'table') {
                            node.properties = {
                              ...node.properties,
                              style: 'display: table; width: 100%; border-collapse: collapse;'
                            };
                          }
                        }}
                      />
                      <style jsx>{`
                        .markdown-content h1,
                        .markdown-content h2,
                        .markdown-content h3,
                        .markdown-content h4,
                        .markdown-content h5,
                        .markdown-content h6 {
                          margin-top: 1.5em !important;
                          margin-bottom: 0.5em !important;
                          line-height: 1.3 !important;
                          font-weight: 600 !important;
                          color: #1f2937 !important;
                          display: block !important;
                          border: none !important;
                          border-bottom: none !important;
                          padding-bottom: 0 !important;
                        }
                        .markdown-content h1 {
                          font-size: 1.8em !important;
                        }
                        .markdown-content h2 {
                          font-size: 1.5em !important;
                        }
                        .markdown-content h3 {
                          font-size: 1.3em !important;
                          font-weight: 600 !important;
                          color: #374151 !important;
                        }
                        .markdown-content h4 {
                          font-size: 1.1em !important;
                          font-weight: 600 !important;
                        }
                        .markdown-content p {
                          margin-bottom: 1em;
                          line-height: 1.6;
                          color: #374151 !important;
                        }
                        .markdown-content ul,
                        .markdown-content ol {
                          margin-bottom: 1em;
                          padding-left: 1.5em;
                        }
                        .markdown-content li {
                          margin-bottom: 0.3em;
                          color: #374151 !important;
                        }
                        /* 强制表格渲染 */
                        .markdown-content table {
                          border-collapse: collapse !important;
                          width: 100% !important;
                          margin: 1em 0 !important;
                          background-color: white !important;
                          border: 1px solid #d1d5db !important;
                          display: table !important;
                          font-family: inherit !important;
                        }
                        .markdown-content thead {
                          display: table-header-group !important;
                        }
                        .markdown-content tbody {
                          display: table-row-group !important;
                        }
                        .markdown-content tr {
                          display: table-row !important;
                        }
                        .markdown-content th,
                        .markdown-content td {
                          border: 1px solid #d1d5db !important;
                          padding: 8px 12px !important;
                          text-align: left !important;
                          background-color: white !important;
                          color: #374151 !important;
                          display: table-cell !important;
                          vertical-align: top !important;
                          word-wrap: break-word !important;
                          max-width: none !important;
                        }
                        .markdown-content th {
                          background-color: #f9fafb !important;
                          font-weight: 600 !important;
                          color: #1f2937 !important;
                        }
                        .markdown-content tbody tr:nth-child(even) td {
                          background-color: #f8fafc !important;
                        }
                        .markdown-content tbody tr:nth-child(odd) td {
                          background-color: white !important;
                        }

                        /* 隐藏代码块和引用块 */
                        .markdown-content pre,
                        .markdown-content code {
                          display: none !important;
                        }
                        .markdown-content blockquote {
                          display: none !important;
                        }

                        /* 确保所有内容在同一个白色背景上 */
                        .markdown-content {
                          background-color: white !important;
                          color: #374151 !important;
                        }

                        /* 移除任何可能的框架样式 */
                        .markdown-content > * {
                          border: none !important;
                          box-shadow: none !important;
                          background-color: transparent !important;
                        }

                        /* 特殊处理：确保表格不被包裹在框中 */
                        .markdown-content table {
                          box-shadow: none !important;
                          border-radius: 0 !important;
                        }
                      `}</style>
                    </div>
                  ) : (
                    <div className="text-center py-12">暂无报告内容</div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportPreview;
