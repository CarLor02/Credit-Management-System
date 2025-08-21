/**
 * 流式内容服务
 * 用于在组件外部持久化流式输出内容
 */

export interface StreamingEvent {
  timestamp: string;
  eventType: string;
  content: string;
  color: string;
  isContent: boolean;
}

export interface ProjectStreamingData {
  projectId: number;
  events: StreamingEvent[];
  isGenerating: boolean;
  reportContent: string;
  lastUpdated: number;
  progress: number; // 进度百分比 (0-100)
  completedChapters: number; // 已完成章节数
  totalChapters: number; // 总章节数 (默认8)
}

class StreamingContentService {
  private streamingData: Map<number, ProjectStreamingData> = new Map();
  private listeners: Map<number, Set<(data: ProjectStreamingData) => void>> = new Map();

  /**
   * 获取项目的流式数据
   */
  getProjectData(projectId: number): ProjectStreamingData | null {
    return this.streamingData.get(projectId) || null;
  }

  /**
   * 设置项目的流式数据
   */
  setProjectData(projectId: number, data: Partial<ProjectStreamingData>): void {
    const existing = this.streamingData.get(projectId) || {
      projectId,
      events: [],
      isGenerating: false,
      reportContent: '',
      lastUpdated: Date.now(),
      progress: 0,
      completedChapters: 0,
      totalChapters: 8
    };

    const updated = {
      ...existing,
      ...data,
      lastUpdated: Date.now()
    };

    this.streamingData.set(projectId, updated);
    this.notifyListeners(projectId, updated);
  }

  /**
   * 添加流式事件
   */
  addEvent(projectId: number, event: StreamingEvent): void {
    const existing = this.getProjectData(projectId) || {
      projectId,
      events: [],
      isGenerating: false,
      reportContent: '',
      lastUpdated: Date.now(),
      progress: 0,
      completedChapters: 0,
      totalChapters: 8
    };

    const updated = {
      ...existing,
      events: [...existing.events, event],
      lastUpdated: Date.now()
    };

    this.streamingData.set(projectId, updated);
    this.notifyListeners(projectId, updated);
  }

  /**
   * 更新报告内容
   */
  updateReportContent(projectId: number, content: string): void {
    this.setProjectData(projectId, { reportContent: content });
  }

  /**
   * 设置生成状态
   */
  setGeneratingStatus(projectId: number, isGenerating: boolean): void {
    this.setProjectData(projectId, { isGenerating });
  }

  /**
   * 处理章节完成事件
   */
  handleChapterComplete(projectId: number, eventData: any): void {
    const data = this.getProjectData(projectId);
    if (!data) return;

    // 检查是否是章节完成事件
    // 根据Dify API格式，节点信息在event_data.data中
    const title = eventData.event_data?.data?.title || eventData.data?.title;
    if (eventData.event_type === 'node_finished' && title) {
      
      // 检查标题是否包含"第X章"和"内容生成"关键字
      const chapterMatch = title.match(/第([一二三四五六七八九十\d]+)章/);
      const hasContentGeneration = title.includes('内容生成');
      
      if (chapterMatch && hasContentGeneration) {
        console.log('📊 检测到章节完成:', title);
        
        // 提取章节号
        const chapterText = chapterMatch[1];
        let chapterNumber = 0;
        
        // 转换中文数字或阿拉伯数字为数字
        const chineseNumbers: { [key: string]: number } = {
          '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
          '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
        };
        
        if (chineseNumbers[chapterText]) {
          chapterNumber = chineseNumbers[chapterText];
        } else if (!isNaN(parseInt(chapterText))) {
          chapterNumber = parseInt(chapterText);
        }
        
        if (chapterNumber > 0 && chapterNumber <= data.totalChapters) {
          // 更新已完成章节数（取最大值，避免重复计算）
          const newCompletedChapters = Math.max(data.completedChapters, chapterNumber);
          const newProgress = Math.round((newCompletedChapters / data.totalChapters) * 100);
          
          console.log(`📊 章节进度更新: ${newCompletedChapters}/${data.totalChapters} = ${newProgress}%`);
          
          this.setProjectData(projectId, {
            completedChapters: newCompletedChapters,
            progress: newProgress
          });
        }
      }
    }
  }

  /**
   * 清空项目数据
   */
  clearProjectData(projectId: number): void {
    this.streamingData.delete(projectId);
    this.notifyListeners(projectId, {
      projectId,
      events: [],
      isGenerating: false,
      reportContent: '',
      lastUpdated: Date.now(),
      progress: 0,
      completedChapters: 0,
      totalChapters: 8
    });
  }

  /**
   * 添加监听器
   */
  addListener(projectId: number, callback: (data: ProjectStreamingData) => void): void {
    if (!this.listeners.has(projectId)) {
      this.listeners.set(projectId, new Set());
    }
    this.listeners.get(projectId)!.add(callback);
  }

  /**
   * 移除监听器
   */
  removeListener(projectId: number, callback: (data: ProjectStreamingData) => void): void {
    const projectListeners = this.listeners.get(projectId);
    if (projectListeners) {
      projectListeners.delete(callback);
      if (projectListeners.size === 0) {
        this.listeners.delete(projectId);
      }
    }
  }

  /**
   * 通知监听器
   */
  private notifyListeners(projectId: number, data: ProjectStreamingData): void {
    const projectListeners = this.listeners.get(projectId);
    if (projectListeners) {
      projectListeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('流式内容监听器回调错误:', error);
        }
      });
    }
  }

  /**
   * 检查项目是否正在生成
   */
  isProjectGenerating(projectId: number): boolean {
    const data = this.getProjectData(projectId);
    return data?.isGenerating || false;
  }

  /**
   * 获取项目的事件数量
   */
  getEventCount(projectId: number): number {
    const data = this.getProjectData(projectId);
    return data?.events.length || 0;
  }

  /**
   * 清理过期数据（超过1小时的数据）
   */
  cleanupExpiredData(): void {
    const now = Date.now();
    const oneHour = 60 * 60 * 1000;

    for (const [projectId, data] of this.streamingData.entries()) {
      if (now - data.lastUpdated > oneHour && !data.isGenerating) {
        this.streamingData.delete(projectId);
        this.listeners.delete(projectId);
      }
    }
  }
}

// 创建并导出服务实例
export const streamingContentService = new StreamingContentService();

// 定期清理过期数据
setInterval(() => {
  streamingContentService.cleanupExpiredData();
}, 10 * 60 * 1000); // 每10分钟清理一次
