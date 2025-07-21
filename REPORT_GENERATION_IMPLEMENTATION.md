# 征信报告生成功能实现总结

## 📋 功能概述

在ProjectDetail.tsx页面中实现了"生成征信报告"按钮功能，点击后调用后端API生成征信报告并自动下载。

## 🔧 实现细节

### 1. 前端修改 (ProjectDetail.tsx)

#### 1.1 数据类型更新
- 在`frontend/data/mockData.ts`中的`Project`接口添加了知识库相关字段：
  ```typescript
  interface Project {
    // ... 其他字段
    dataset_id?: string;
    knowledge_base_name?: string;
  }
  ```

#### 1.2 按钮功能实现
- 添加了报告生成状态管理：`reportGenerating`
- 修改了`handleDownloadReport`函数，使用`apiClient`调用后端API
- 按钮在生成过程中显示加载状态和禁用状态
- 成功生成后自动下载Markdown格式的报告文件

#### 1.3 API调用参数
```typescript
{
  dataset_id: project.dataset_id,
  company_name: project.name,
  knowledge_name: project.knowledge_base_name
}
```

### 2. 后端实现 (api/reports.py)

#### 2.1 新增API接口
- 路由：`POST /api/generate_report`
- 功能：生成征信报告并返回内容

#### 2.2 参数验证
- `company_name`：必需参数，企业名称
- `dataset_id`：必需参数，知识库数据集ID
- `knowledge_name`：可选参数，默认使用`company_name`

#### 2.3 处理流程
1. 验证必要参数（company_name, dataset_id, knowledge_name）
2. 检查文档解析状态（如果有dataset_id）
3. 调用外部报告生成API（标准模式）
4. 保存报告到本地文件
5. 返回报告内容给前端

#### 2.4 外部API集成
- 报告生成API：`http://172.16.76.203/v1/workflows/run`
- API密钥：`app-zLDrndvfJ81HaTWD3gXXVJaq`
- 请求模式：`blocking`（同步模式）
- 用户标识：`root`
- 超时时间：600秒（10分钟）

#### 2.5 请求格式
```json
{
    "inputs": {
        "company": "公司名称",
        "knowledge_name": "知识库名称"
    },
    "response_mode": "blocking",
    "user": "root"
}
```

### 3. 后端API修改 (api/projects.py)

#### 3.1 项目详情API更新
- 在`GET /api/projects/<id>`响应中添加了知识库字段：
  ```json
  {
    "dataset_id": "...",
    "knowledge_base_name": "...",
    // ... 其他字段
  }
  ```

#### 3.2 项目列表API更新
- 在`GET /api/projects`响应中也添加了相同的知识库字段

### 4. 路由注册 (routes.py)

- 在`register_routes`函数中添加了报告路由注册：
  ```python
  from api.reports import register_report_routes
  register_report_routes(app)
  ```

## 🔄 数据流程

1. **前端触发**：用户点击"生成征信报告"按钮
2. **参数准备**：从项目数据中提取`name`、`dataset_id`、`knowledge_base_name`
3. **API调用**：前端调用`POST /api/generate_report`
4. **后端处理**：
   - 验证参数
   - 检查解析状态
   - 调用外部报告生成API
   - 保存报告文件
5. **响应返回**：返回报告内容
6. **文件下载**：前端创建下载链接，自动下载Markdown文件

## 📁 文件变更清单

### 新增文件
- `generated_backend/api/reports.py` - 报告生成API
- `generated_backend/test_report_api.py` - API测试脚本
- `generated_backend/test_complete_flow.py` - 完整功能测试
- `generated_backend/check_project_data.py` - 数据库检查脚本

### 修改文件
- `frontend/app/projects/[id]/ProjectDetail.tsx` - 前端按钮功能
- `frontend/data/mockData.ts` - 数据类型定义
- `generated_backend/api/projects.py` - 项目API响应格式
- `generated_backend/routes.py` - 路由注册
- `generated_backend/config.py` - 配置项

## ⚙️ 配置要求

### 环境变量
```bash
REPORT_API_URL=http://172.16.76.203/v1/workflows/run
REPORT_API_KEY=app-zLDrndvfJ81HaTWD3gXXVJaq
RAG_API_BASE_URL=http://172.16.76.183
RAG_API_KEY=ragflow-U4OWM2Njc2NDVjNTExZjA5NDUzMDI0Mm
```

### 目录结构
- `generated_backend/output/` - 报告文件保存目录（自动创建）

## 🧪 测试方法

### 1. 启动后端服务器
```bash
cd generated_backend
python app.py
```

### 2. 测试API
```bash
python test_report_api.py
```

### 3. 完整功能测试
```bash
python test_complete_flow.py
```

## 📝 注意事项

1. **知识库数据**：项目需要有`dataset_id`和`knowledge_base_name`才能正常生成报告
2. **文档解析**：如果项目有dataset_id，会检查文档解析状态
3. **超时处理**：报告生成可能需要较长时间，设置了10分钟超时
4. **错误处理**：包含了完整的错误处理和用户提示
5. **文件格式**：生成的报告为Markdown格式，便于阅读和编辑

## 🎯 功能特点

- ✅ 真实API集成（标准模式）
- ✅ 完整的错误处理和用户反馈
- ✅ 加载状态显示
- ✅ 自动文件下载
- ✅ 本地文件保存
- ✅ 参数验证和安全检查
- ✅ 日志记录和调试支持
- ✅ 与Postman测试参数完全一致

## 🚀 使用方法

1. 确保项目有知识库数据（`dataset_id`和`knowledge_base_name`）
2. 在项目详情页面点击"生成征信报告"按钮
3. 等待报告生成完成（可能需要几分钟）
4. 报告会自动下载为Markdown文件
5. 同时在服务器的`output`目录中保存一份副本
