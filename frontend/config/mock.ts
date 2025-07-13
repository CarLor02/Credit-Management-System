/**
 * Mock配置文件
 * 用于控制是否使用mock数据
 */

// 从环境变量读取mock开关，默认为false（使用真实API）
export const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === 'true';

// API基础URL配置
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5001/api';

// Mock配置选项
export const MOCK_CONFIG = {
  // 是否启用mock
  enabled: USE_MOCK,
  
  // API响应延迟（毫秒）
  delay: 500,
  
  // 是否在控制台显示mock日志
  logging: process.env.NODE_ENV === 'development',
  
  // 错误模拟概率（0-1）
  errorRate: 0.1,
};

/**
 * Mock日志输出
 */
export const mockLog = (message: string, data?: any) => {
  if (MOCK_CONFIG.logging) {
    console.log(`[MOCK] ${message}`, data || '');
  }
};

/**
 * 模拟API延迟
 */
export const mockDelay = (ms: number = MOCK_CONFIG.delay) => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

/**
 * 模拟随机错误
 */
export const shouldSimulateError = () => {
  return Math.random() < MOCK_CONFIG.errorRate;
};
