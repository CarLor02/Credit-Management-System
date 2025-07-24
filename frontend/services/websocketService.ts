/**
 * WebSocket服务
 * 用于实时接收流式输出
 */

import { io, Socket } from 'socket.io-client';

interface WorkflowEvent {
  event_type: string;
  workflow_run_id: string;
  timestamp: number;
  event_data?: any;
  content?: string;
}

interface WorkflowContent {
  workflow_run_id: string;
  content_chunk: string;
  timestamp: number;
}

interface WorkflowComplete {
  workflow_run_id: string;
  final_content: string;
  timestamp: number;
}

interface WorkflowError {
  workflow_run_id: string;
  error_message: string;
  timestamp: number;
}

type EventCallback = (data: any) => void;

class WebSocketService {
  private socket: Socket | null = null;
  private isConnected = false;
  private currentWorkflowId: string | null = null;
  private eventCallbacks: Map<string, EventCallback[]> = new Map();

  constructor() {
    // 不在构造函数中自动连接，改为手动连接
  }

  /**
   * 连接到WebSocket服务器
   */
  connect() {
    if (this.socket) {
      return;
    }

    // 从API URL中提取基础URL，移除/api后缀
    const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5001/api';
    const serverUrl = apiUrl.replace('/api', '');

    console.log('WebSocket连接URL:', serverUrl);

    this.socket = io(serverUrl, {
      transports: ['websocket', 'polling'],
      timeout: 20000,
      forceNew: true,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket连接成功，连接ID:', this.socket?.id);
      this.isConnected = true;
      this.emit('connected', { connected: true });
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket连接断开');
      this.isConnected = false;
      this.emit('disconnected', { connected: false });
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket连接错误:', error);
      this.emit('error', { error: error.message });
    });

    // 监听工作流事件
    this.socket.on('workflow_event', (data: WorkflowEvent) => {
      console.log('收到工作流事件:', data);
      this.emit('workflow_event', data);
    });

    // 监听工作流内容
    this.socket.on('workflow_content', (data: WorkflowContent) => {
      console.log('收到工作流内容:', data.content_chunk.substring(0, 50) + '...');
      this.emit('workflow_content', data);
    });

    // 监听工作流完成
    this.socket.on('workflow_complete', (data: WorkflowComplete) => {
      console.log('工作流完成:', data.workflow_run_id);
      this.emit('workflow_complete', data);
    });

    // 监听工作流错误
    this.socket.on('workflow_error', (data: WorkflowError) => {
      console.error('工作流错误:', data.error_message);
      this.emit('workflow_error', data);
    });

    // 监听房间加入成功
    this.socket.on('joined_workflow', (data) => {
      console.log('✅ 成功加入工作流房间:', data);
      this.emit('joined_workflow', data);
    });

    // 监听连接错误
    this.socket.on('error', (data) => {
      console.error('❌ WebSocket错误:', data);
      this.emit('error', data);
    });

    // 监听连接错误
    this.socket.on('connect_error', (error) => {
      console.error('❌ WebSocket连接错误:', error);
      this.emit('connect_error', error);
    });
  }

  /**
   * 断开连接
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
      this.currentWorkflowId = null;
    }
  }

  /**
   * 加入工作流房间
   */
  joinWorkflow(workflowRunId: string) {
    console.log('尝试加入工作流房间:', workflowRunId);
    console.log('WebSocket状态 - socket存在:', !!this.socket, '已连接:', this.isConnected);

    if (!this.socket || !this.isConnected) {
      console.error('WebSocket未连接，无法加入工作流');
      console.error('Socket:', this.socket, 'Connected:', this.isConnected);
      return;
    }

    this.currentWorkflowId = workflowRunId;
    console.log('发送join_workflow事件，房间ID:', workflowRunId);
    this.socket.emit('join_workflow', { workflow_run_id: workflowRunId });
    console.log('join_workflow事件已发送');
  }

  /**
   * 离开工作流房间
   */
  leaveWorkflow(workflowRunId?: string) {
    if (!this.socket) {
      return;
    }

    const targetWorkflowId = workflowRunId || this.currentWorkflowId;
    if (targetWorkflowId) {
      this.socket.emit('leave_workflow', { workflow_run_id: targetWorkflowId });
      console.log('离开工作流房间:', targetWorkflowId);
    }

    this.currentWorkflowId = null;
  }

  /**
   * 添加事件监听器
   */
  on(event: string, callback: EventCallback) {
    if (!this.eventCallbacks.has(event)) {
      this.eventCallbacks.set(event, []);
    }
    this.eventCallbacks.get(event)!.push(callback);
  }

  /**
   * 移除事件监听器
   */
  off(event: string, callback?: EventCallback) {
    if (!this.eventCallbacks.has(event)) {
      return;
    }

    if (callback) {
      const callbacks = this.eventCallbacks.get(event)!;
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    } else {
      this.eventCallbacks.delete(event);
    }
  }

  /**
   * 触发事件
   */
  private emit(event: string, data: any) {
    const callbacks = this.eventCallbacks.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('事件回调执行错误:', error);
        }
      });
    }
  }

  /**
   * 获取连接状态
   */
  isSocketConnected(): boolean {
    return this.isConnected;
  }

  /**
   * 获取当前工作流ID
   */
  getCurrentWorkflowId(): string | null {
    return this.currentWorkflowId;
  }
}

// 创建单例实例
const websocketService = new WebSocketService();

export default websocketService;
export type { WorkflowEvent, WorkflowContent, WorkflowComplete, WorkflowError };
