/**
 * Mock数据文件
 * 包含所有页面的模拟数据
 */

// 企业信息接口
export interface CompanyInfo {
  registeredCapital?: string;
  establishDate?: string;
  industry?: string;
  employees?: string;
  legalPerson?: string;
  businessScope?: string;
}

// 个人信息接口
export interface PersonalInfo {
  age?: number;
  education?: string;
  profession?: string;
  workYears?: number;
  monthlyIncome?: string;
  maritalStatus?: string;
}

// 财务数据接口
export interface FinancialData {
  annualRevenue?: string;
  totalAssets?: string;
  liabilities?: string;
  netProfit?: string;
  monthlyIncome?: string;
  monthlyExpense?: string;
  savings?: string;
  debts?: string;
}

// 项目数据类型定义
export interface Project {
  id: number;
  name: string;
  type: 'enterprise' | 'individual';
  status: 'collecting' | 'processing' | 'completed';
  score: number;
  riskLevel: 'low' | 'medium' | 'high';
  lastUpdate: string;
  documents: number;
  progress: number;
  // 扩展信息
  companyInfo?: CompanyInfo;
  personalInfo?: PersonalInfo;
  financialData?: FinancialData;
}

// 文档数据类型定义
export interface Document {
  id: number;
  name: string;
  project: string;
  type: 'pdf' | 'excel' | 'word' | 'image';
  size: string;
  status: 'uploading' | 'completed' | 'processing' | 'failed';
  uploadTime: string;
  progress: number;
}

// 用户数据类型定义
export interface User {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'user';
  avatar?: string;
  lastLogin: string;
}

// Mock项目数据
export const mockProjects: Project[] = [
  {
    id: 1,
    name: '腾讯科技有限公司',
    type: 'enterprise',
    status: 'completed',
    score: 85,
    riskLevel: 'low',
    lastUpdate: '2024-01-15',
    documents: 12,
    progress: 100
  },
  {
    id: 2,
    name: '阿里巴巴集团',
    type: 'enterprise',
    status: 'processing',
    score: 78,
    riskLevel: 'medium',
    lastUpdate: '2024-01-14',
    documents: 8,
    progress: 75
  },
  {
    id: 3,
    name: '张三',
    type: 'individual',
    status: 'collecting',
    score: 92,
    riskLevel: 'low',
    lastUpdate: '2024-01-13',
    documents: 5,
    progress: 45
  },
  {
    id: 4,
    name: '字节跳动科技',
    type: 'enterprise',
    status: 'completed',
    score: 65,
    riskLevel: 'high',
    lastUpdate: '2024-01-12',
    documents: 15,
    progress: 100
  },
  {
    id: 5,
    name: '李四',
    type: 'individual',
    status: 'processing',
    score: 88,
    riskLevel: 'low',
    lastUpdate: '2024-01-11',
    documents: 7,
    progress: 80
  },
  {
    id: 6,
    name: '美团点评',
    type: 'enterprise',
    status: 'completed',
    score: 76,
    riskLevel: 'medium',
    lastUpdate: '2024-01-10',
    documents: 11,
    progress: 100
  }
];

// Mock文档数据
export const mockDocuments: Document[] = [
  {
    id: 1,
    name: '财务报表2023.pdf',
    project: '腾讯科技有限公司',
    type: 'pdf',
    size: '2.3 MB',
    status: 'completed',
    uploadTime: '2024-01-15 14:30',
    progress: 100
  },
  {
    id: 2,
    name: '营业执照.jpg',
    project: '阿里巴巴集团',
    type: 'image',
    size: '856 KB',
    status: 'processing',
    uploadTime: '2024-01-15 14:25',
    progress: 65
  },
  {
    id: 3,
    name: '银行流水明细.xlsx',
    project: '张三',
    type: 'excel',
    size: '1.2 MB',
    status: 'completed',
    uploadTime: '2024-01-15 14:20',
    progress: 100
  },
  {
    id: 4,
    name: '信用报告.pdf',
    project: '字节跳动科技',
    type: 'pdf',
    size: '3.1 MB',
    status: 'failed',
    uploadTime: '2024-01-15 14:15',
    progress: 0
  },
  {
    id: 5,
    name: '身份证明.pdf',
    project: '李四',
    type: 'pdf',
    size: '1.8 MB',
    status: 'processing',
    uploadTime: '2024-01-15 14:10',
    progress: 30
  },
  {
    id: 6,
    name: '公司章程.docx',
    project: '美团点评',
    type: 'word',
    size: '945 KB',
    status: 'completed',
    uploadTime: '2024-01-15 14:05',
    progress: 100
  }
];

// Mock用户数据
export const mockUser: User = {
  id: 1,
  name: '管理员',
  email: 'admin@example.com',
  role: 'admin',
  lastLogin: '2024-01-15 15:30'
};

// Mock统计数据
export const mockStats = {
  totalProjects: mockProjects.length,
  completedProjects: mockProjects.filter(p => p.status === 'completed').length,
  processingProjects: mockProjects.filter(p => p.status === 'processing').length,
  totalDocuments: mockDocuments.length,
  averageScore: Math.round(mockProjects.reduce((sum, p) => sum + p.score, 0) / mockProjects.length),
};
