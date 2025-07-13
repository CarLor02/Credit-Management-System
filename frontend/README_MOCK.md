# Mock系统使用说明

本项目实现了一个完整的Mock系统，允许在开发过程中轻松切换真实API调用和模拟数据。

## 功能特性

- ✅ 全局Mock开关控制
- ✅ 环境变量配置支持
- ✅ 统一的API服务层
- ✅ 完整的Mock数据
- ✅ 可视化Mock状态指示器
- ✅ 模拟网络延迟和错误
- ✅ 开发友好的日志输出

## 快速开始

### 1. 环境配置

复制环境变量示例文件：
```bash
cp .env.example .env.local
```

编辑 `.env.local` 文件：
```env
# 使用Mock数据
NEXT_PUBLIC_USE_MOCK=true

# 或使用真实API
NEXT_PUBLIC_USE_MOCK=false
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

### 2. 启动项目

```bash
# 使用Mock数据启动（默认）
npm run dev

# 或者明确指定使用Mock数据
npm run dev:mock

# 使用真实API启动
npm run dev:real
```

## Mock系统架构

### 配置层 (`config/mock.ts`)
- 全局Mock开关控制
- 配置选项管理
- 工具函数提供

### 数据层 (`data/mockData.ts`)
- 项目数据模拟
- 文档数据模拟
- 用户数据模拟
- 统计数据模拟

### 服务层 (`services/`)
- `api.ts`: 基础API客户端
- `projectService.ts`: 项目相关API
- `documentService.ts`: 文档相关API

### 组件层
- `MockIndicator.tsx`: Mock状态指示器

## 使用方式

### 在组件中使用服务

```typescript
import { projectService } from '@/services/projectService';

// 获取项目列表（自动根据Mock开关选择数据源）
const response = await projectService.getProjects();
if (response.success) {
  setProjects(response.data);
}
```

### Mock配置选项

```typescript
export const MOCK_CONFIG = {
  enabled: USE_MOCK,        // 是否启用Mock
  delay: 500,               // API响应延迟（毫秒）
  logging: true,            // 是否显示Mock日志
  errorRate: 0.1,           // 错误模拟概率（0-1）
};
```

## Mock数据结构

### 项目数据 (Project)
```typescript
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
```

### 文档数据 (Document)
```typescript
interface Document {
  id: number;
  name: string;
  project: string;
  type: 'pdf' | 'excel' | 'word' | 'image';
  size: string;
  status: 'completed' | 'processing' | 'failed';
  uploadTime: string;
  progress: number;
}
```

## 开发调试

### Mock日志
当 `MOCK_CONFIG.logging = true` 时，控制台会显示Mock API调用日志：
```
[MOCK] Getting projects list {type: "enterprise"}
[MOCK] Creating new project {name: "测试项目", type: "enterprise"}
```

### Mock状态指示器
在Mock模式下，页面右上角会显示黄色的"Mock模式"指示器。

### 错误模拟
系统会根据 `MOCK_CONFIG.errorRate` 随机模拟API错误，帮助测试错误处理逻辑。

## 真实API集成

当 `NEXT_PUBLIC_USE_MOCK=false` 时，系统会调用真实的后端API。

### API端点映射
- `GET /api/projects` - 获取项目列表
- `POST /api/projects` - 创建项目
- `PUT /api/projects/:id` - 更新项目
- `DELETE /api/projects/:id` - 删除项目
- `GET /api/documents` - 获取文档列表
- `POST /api/documents/upload` - 上传文档
- `DELETE /api/documents/:id` - 删除文档
- `GET /api/documents/:id/download` - 下载文档

## 最佳实践

1. **开发阶段**：使用Mock数据进行快速开发和测试
2. **集成测试**：切换到真实API进行集成测试
3. **生产部署**：确保 `NEXT_PUBLIC_USE_MOCK=false`
4. **错误处理**：利用Mock错误模拟完善错误处理逻辑
5. **性能测试**：调整Mock延迟模拟不同网络条件

## 扩展Mock数据

要添加新的Mock数据，请编辑 `data/mockData.ts` 文件：

```typescript
// 添加新的数据类型
export interface NewDataType {
  id: number;
  name: string;
  // ... 其他字段
}

// 添加Mock数据
export const mockNewData: NewDataType[] = [
  // ... Mock数据
];
```

然后在对应的服务文件中实现Mock逻辑。
