# 征信管理系统 API 文档

## 📋 目录

- [1. 概述](#1-概述)
- [2. 认证系统](#2-认证系统)
- [3. 项目管理](#3-项目管理)
- [4. 文档管理](#4-文档管理)
- [5. 报告生成](#5-报告生成)
- [6. 统计和系统](#6-统计和系统)
- [7. 数据模型](#7-数据模型)
- [8. 前端集成](#8-前端集成)
- [9. 错误处理](#9-错误处理)
- [10. 最佳实践](#10-最佳实践)

## 1. 概述

### 1.1 系统架构

征信管理系统采用前后端分离架构：

- **前端**: Next.js + TypeScript + Tailwind CSS
- **后端**: Flask + SQLAlchemy + SQLite
- **外部服务**: RAG知识库服务 (RAGFlow)

### 1.2 技术栈

#### 后端技术栈
- **框架**: Flask 2.3.3
- **数据库**: SQLite (开发环境)
- **ORM**: SQLAlchemy
- **认证**: JWT
- **文件处理**: Werkzeug
- **跨域**: Flask-CORS

#### 前端技术栈
- **框架**: Next.js 14
- **语言**: TypeScript
- **样式**: Tailwind CSS
- **状态管理**: React Hooks
- **HTTP客户端**: Fetch API

### 1.3 API基础信息

- **基础URL**: `http://localhost:5001`
- **API前缀**: `/api`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

### 1.4 通用响应格式

#### 成功响应
```json
{
  "success": true,
  "data": {},
  "message": "操作成功"
}
```

#### 错误响应
```json
{
  "success": false,
  "error": "错误信息",
  "code": "ERROR_CODE"
}
```

### 1.5 HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 2. 认证系统

### 2.1 JWT认证机制

系统使用JWT (JSON Web Token) 进行用户认证，token有效期为1小时。

#### 认证流程
1. 用户提供用户名和密码进行登录
2. 服务器验证凭据并生成JWT token
3. 客户端在后续请求中携带token
4. 服务器验证token并返回相应数据

#### Token格式
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### 2.2 用户登录

**接口地址**: `POST /api/auth/login`

**描述**: 用户登录获取访问token

**请求参数**:
```json
{
  "username": "string",     // 用户名，必填
  "password": "string"      // 密码，必填
}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 1,
      "username": "admin",
      "full_name": "管理员",
      "role": "admin",
      "email": "admin@example.com",
      "avatar_url": null,
      "is_active": true,
      "last_login": "2025-07-09T10:30:00",
      "created_at": "2025-01-01T00:00:00"
    }
  },
  "message": "登录成功"
}
```

**错误响应**:
- **400**: 参数错误
```json
{
  "success": false,
  "error": "用户名和密码不能为空"
}
```
- **401**: 认证失败
```json
{
  "success": false,
  "error": "用户名或密码错误"
}
```

**示例代码**:
```javascript
// 前端调用示例
const response = await fetch('/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'admin',
    password: 'password123'
  })
});

const result = await response.json();
if (result.success) {
  localStorage.setItem('token', result.data.token);
}
```

### 2.3 用户登出

**接口地址**: `POST /api/auth/logout`

**描述**: 用户登出，记录登出日志

**请求头**:
```
Authorization: Bearer <token>
```

**成功响应** (200):
```json
{
  "success": true,
  "message": "登出成功"
}
```

**错误响应**:
- **401**: 未授权
```json
{
  "success": false,
  "error": "缺少认证token"
}
```

### 2.4 获取用户信息

**接口地址**: `GET /api/auth/profile`

**描述**: 获取当前登录用户的详细信息

**请求头**:
```
Authorization: Bearer <token>
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "admin",
    "full_name": "管理员",
    "role": "admin",
    "email": "admin@example.com",
    "avatar_url": null,
    "is_active": true,
    "last_login": "2025-07-09T10:30:00",
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-07-09T10:30:00"
  }
}
```

### 2.5 更新用户信息

**接口地址**: `PUT /api/auth/profile`

**描述**: 更新当前用户的个人信息

**请求头**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

**请求参数**:
```json
{
  "full_name": "string",    // 姓名，可选
  "email": "string",        // 邮箱，可选，必须唯一
  "avatar_url": "string"    // 头像URL，可选
}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "admin",
    "full_name": "新姓名",
    "role": "admin",
    "email": "new@example.com",
    "avatar_url": "https://example.com/avatar.jpg",
    "is_active": true,
    "last_login": "2025-07-09T10:30:00",
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-07-09T10:35:00"
  },
  "message": "个人信息更新成功"
}
```

**错误响应**:
- **400**: 邮箱已被使用
```json
{
  "success": false,
  "error": "邮箱已被使用"
}
```

### 2.6 修改密码

**接口地址**: `POST /api/auth/change-password`

**描述**: 修改当前用户密码

**请求头**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

**请求参数**:
```json
{
  "old_password": "string",  // 旧密码，必填
  "new_password": "string"   // 新密码，必填
}
```

**成功响应** (200):
```json
{
  "success": true,
  "message": "密码修改成功"
}
```

**错误响应**:
- **400**: 参数错误
```json
{
  "success": false,
  "error": "旧密码和新密码不能为空"
}
```
- **400**: 旧密码错误
```json
{
  "success": false,
  "error": "旧密码错误"
}
```

### 2.7 获取用户列表 (管理员)

**接口地址**: `GET /api/users`

**描述**: 获取系统用户列表，仅管理员可访问

**请求头**:
```
Authorization: Bearer <token>
```

**查询参数**:
- `page`: 页码 (默认: 1)
- `limit`: 每页数量 (默认: 20，最大: 100)
- `search`: 搜索关键词 (搜索用户名、姓名、邮箱)

**成功响应** (200):
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "username": "admin",
      "full_name": "管理员",
      "role": "admin",
      "email": "admin@example.com",
      "is_active": true,
      "last_login": "2025-07-09T10:30:00",
      "created_at": "2025-01-01T00:00:00",
      "updated_at": "2025-07-09T10:30:00"
    },
    {
      "id": 2,
      "username": "analyst1",
      "full_name": "分析师1",
      "role": "analyst",
      "email": "analyst1@example.com",
      "is_active": true,
      "last_login": "2025-07-08T15:20:00",
      "created_at": "2025-01-02T00:00:00",
      "updated_at": "2025-07-08T15:20:00"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5,
    "pages": 1
  }
}
```

**错误响应**:
- **403**: 权限不足
```json
{
  "success": false,
  "error": "需要管理员权限"
}
```

### 2.8 用户角色说明

| 角色 | 权限描述 |
|------|----------|
| admin | 系统管理员，拥有所有权限 |
| manager | 项目经理，可管理项目和用户 |
| analyst | 分析师，可创建和分析项目 |
| user | 普通用户，只能查看分配给自己的项目 |

### 2.9 权限验证装饰器

系统提供以下权限验证装饰器：

- `@token_required`: 需要有效的JWT token
- `@admin_required`: 需要管理员权限

**使用示例**:
```python
@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    # 只有管理员可以访问
    pass
```

## 3. 项目管理

### 3.1 获取项目列表

**接口地址**: `GET /api/projects`

**描述**: 获取项目列表，支持分页、搜索和过滤

**查询参数**:
- `page`: 页码 (默认: 1)
- `limit`: 每页数量 (默认: 20，最大: 100)
- `search`: 搜索关键词 (搜索项目名称和描述)
- `type`: 项目类型 (`enterprise`, `individual`)
- `status`: 项目状态 (`collecting`, `processing`, `completed`, `archived`)

**成功响应** (200):
```json
[
  {
    "id": 1,
    "name": "企业征信分析项目",
    "type": "enterprise",
    "status": "processing",
    "score": 85,
    "riskLevel": "medium",
    "progress": 75,
    "documents": 5,
    "lastUpdate": "2025-07-09"
  },
  {
    "id": 2,
    "name": "个人信用评估",
    "type": "individual",
    "status": "completed",
    "score": 92,
    "riskLevel": "low",
    "progress": 100,
    "documents": 3,
    "lastUpdate": "2025-07-08"
  }
]
```

**注意**: 响应直接返回项目数组，不包含分页信息包装

**示例代码**:
```javascript
// 获取企业类型的项目
const response = await fetch('/api/projects?type=enterprise&page=1&limit=10');
const projects = await response.json();
```

### 3.2 获取项目详情

**接口地址**: `GET /api/projects/{id}`

**描述**: 根据项目ID获取项目详细信息

**路径参数**:
- `id`: 项目ID (必填)

**成功响应** (200):
```json
{
  "id": 1,
  "name": "企业征信分析项目",
  "type": "enterprise",
  "status": "processing",
  "score": 85,
  "riskLevel": "medium",
  "progress": 75,
  "documents": 5,
  "lastUpdate": "2025-07-09"
}
```

**错误响应**:
- **404**: 项目不存在
```json
{
  "error": "获取项目详情失败"
}
```

### 3.3 创建项目

**接口地址**: `POST /api/projects`

**描述**: 创建新项目，自动创建项目成员关系和知识库

**请求头**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

**请求参数**:
```json
{
  "name": "string",                    // 项目名称，必填
  "type": "enterprise|individual",    // 项目类型，必填
  "description": "string",             // 项目描述，可选
  "category": "string",                // 项目分类，可选
  "priority": "low|medium|high",       // 优先级，可选，默认medium
  "assigned_to": "number"              // 分配给的用户ID，可选
}
```

**成功响应** (201):
```json
{
  "id": 13,
  "name": "新项目",
  "type": "enterprise",
  "status": "collecting",
  "score": 0,
  "riskLevel": "low",
  "progress": 0,
  "documents": 0,
  "lastUpdate": "2025-07-09"
}
```

**错误响应**:
- **400**: 参数错误
```json
{
  "success": false,
  "error": "缺少必需字段: name"
}
```
- **400**: 无效的项目类型
```json
{
  "success": false,
  "error": "无效的项目类型"
}
```

**自动创建的关联数据**:
1. 项目成员关系：创建者自动成为项目owner
2. 知识库：自动创建项目专属知识库

### 3.4 更新项目

**接口地址**: `PUT /api/projects/{id}`

**描述**: 更新项目信息

**请求头**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

**路径参数**:
- `id`: 项目ID (必填)

**请求参数** (所有字段都是可选的):
```json
{
  "name": "string",                                    // 项目名称
  "description": "string",                             // 项目描述
  "category": "string",                                // 项目分类
  "priority": "low|medium|high",                       // 优先级
  "status": "collecting|processing|completed|archived", // 项目状态
  "score": "number",                                   // 项目评分
  "risk_level": "low|medium|high",                     // 风险等级
  "progress": "number",                                // 进度百分比
  "assigned_to": "number"                              // 分配给的用户ID
}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "更新后的项目名称",
    "type": "enterprise",
    "status": "processing",
    "description": "更新后的描述",
    "category": "金融",
    "priority": "high",
    "score": 90,
    "riskLevel": "medium",
    "progress": 80,
    "created_by": 1,
    "assigned_to": 2,
    "documents": 5,
    "lastUpdate": "2025-07-09",
    "created_at": "2025-07-01T00:00:00",
    "updated_at": "2025-07-09T10:30:00"
  },
  "message": "项目更新成功"
}
```

**错误响应**:
- **404**: 项目不存在
- **500**: 更新失败

### 3.5 删除项目

**接口地址**: `DELETE /api/projects/{id}`

**描述**: 删除项目及其所有关联数据（文档、成员、知识库等）

**请求头**:
```
Authorization: Bearer <token>
```

**路径参数**:
- `id`: 项目ID (必填)

**成功响应** (200):
```json
{
  "success": true,
  "message": "项目 \"企业征信分析项目\" 删除成功"
}
```

**错误响应**:
- **404**: 项目不存在
- **500**: 删除失败

**注意**: 删除项目会级联删除以下关联数据：
- 项目文档
- 项目成员关系
- 分析报告
- 知识库

### 3.6 项目状态说明

| 状态 | 描述 |
|------|------|
| collecting | 收集中 - 正在收集项目相关文档 |
| processing | 处理中 - 正在分析和处理文档 |
| completed | 已完成 - 分析完成，报告已生成 |
| archived | 已归档 - 项目已归档，只读状态 |

### 3.7 项目类型说明

| 类型 | 描述 |
|------|------|
| enterprise | 企业征信 - 针对企业的征信分析 |
| individual | 个人征信 - 针对个人的征信分析 |

### 3.8 风险等级说明

| 等级 | 描述 | 分数范围 |
|------|------|----------|
| low | 低风险 | 80-100 |
| medium | 中风险 | 60-79 |
| high | 高风险 | 0-59 |

## 4. 文档管理

### 4.1 获取文档列表

**接口地址**: `GET /api/documents`

**描述**: 获取文档列表，支持分页、搜索和过滤

**查询参数**:
- `page`: 页码 (默认: 1)
- `limit`: 每页数量 (默认: 20，最大: 100)
- `search`: 搜索关键词 (搜索文档名称和项目名称)
- `project`: 项目ID (按项目过滤)
- `status`: 文档状态 (`uploading`, `processing`, `completed`, `failed`)
- `type`: 文件类型 (`pdf`, `excel`, `word`, `image`)

**成功响应** (200):
```json
[
  {
    "id": 1,
    "name": "企业营业执照.pdf",
    "project": "企业征信分析项目",
    "type": "pdf",
    "size": "2.5 MB",
    "status": "completed",
    "uploadTime": "2025-07-09 10:30",
    "progress": 100
  },
  {
    "id": 2,
    "name": "财务报表.xlsx",
    "project": "企业征信分析项目",
    "type": "excel",
    "size": "1.8 MB",
    "status": "processing",
    "uploadTime": "2025-07-09 10:25",
    "progress": 75
  }
]
```

**注意**: 响应直接返回文档数组，不包含分页信息包装

**示例代码**:
```javascript
// 获取特定项目的PDF文档
const response = await fetch('/api/documents?project=1&type=pdf');
const documents = await response.json();
```

### 4.2 获取文档详情

**接口地址**: `GET /api/documents/{id}`

**描述**: 根据文档ID获取文档详细信息

**路径参数**:
- `id`: 文档ID (必填)

**成功响应** (200):
```json
{
  "id": 1,
  "name": "企业营业执照.pdf",
  "project": "企业征信分析项目",
  "type": "pdf",
  "size": "2.5 MB",
  "status": "completed",
  "uploadTime": "2025-07-09 10:30",
  "progress": 100
}
```

**错误响应**:
- **404**: 文档不存在
```json
{
  "success": false,
  "error": "获取文档详情失败"
}
```

### 4.3 上传文档

**接口地址**: `POST /api/documents/upload`

**描述**: 上传文档到指定项目，支持多种文件格式

**请求头**:
```
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**请求参数** (表单数据):
- `file`: 文件 (必填) - 支持的格式见下方说明
- `project`: 项目名称 (必填) - 必须是已存在的项目名称
- `name`: 文档名称 (可选，默认使用文件名)

**支持的文件格式**:
- **PDF**: .pdf
- **Excel**: .xls, .xlsx
- **Word**: .doc, .docx
- **图片**: .jpg, .jpeg, .png
- **文本**: .txt

**文件大小限制**: 最大 50MB

**成功响应** (201):
```json
{
  "success": true,
  "data": {
    "id": 7,
    "name": "新文档.pdf",
    "project": "企业征信分析项目",
    "type": "pdf",
    "size": "1.2 MB",
    "status": "completed",
    "uploadTime": "2025-07-09 10:30",
    "progress": 100
  },
  "message": "文档上传成功"
}
```

**错误响应**:
- **400**: 没有文件被上传
```json
{
  "success": false,
  "error": "没有文件被上传"
}
```
- **400**: 不支持的文件类型
```json
{
  "success": false,
  "error": "不支持的文件类型"
}
```
- **400**: 缺少项目信息
```json
{
  "success": false,
  "error": "缺少项目信息"
}
```
- **404**: 项目不存在
```json
{
  "success": false,
  "error": "项目不存在"
}
```

**示例代码**:
```javascript
// 上传文档
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('project', '企业征信分析项目');
formData.append('name', '自定义文档名称');

const response = await fetch('/api/documents/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const result = await response.json();
```

### 4.4 下载文档

**接口地址**: `GET /api/documents/{id}/download`

**描述**: 下载指定文档

**请求头**:
```
Authorization: Bearer <token>
```

**路径参数**:
- `id`: 文档ID (必填)

**成功响应** (200):
- **Content-Type**: 根据文件类型设置
- **Content-Disposition**: attachment; filename="原始文件名"
- **响应体**: 文件二进制流

**错误响应**:
- **404**: 文档不存在
```json
{
  "success": false,
  "error": "文件不存在"
}
```

**示例代码**:
```javascript
// 下载文档
const response = await fetch(`/api/documents/${documentId}/download`, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

if (response.ok) {
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
}
```

### 4.5 删除文档

**接口地址**: `DELETE /api/documents/{id}`

**描述**: 删除指定文档及其文件

**请求头**:
```
Authorization: Bearer <token>
```

**路径参数**:
- `id`: 文档ID (必填)

**成功响应** (200):
```json
{
  "success": true,
  "message": "文档 \"企业营业执照.pdf\" 删除成功"
}
```

**错误响应**:
- **404**: 文档不存在
- **500**: 删除失败

**注意**: 删除文档会同时删除数据库记录和服务器上的文件

### 4.6 文档状态说明

| 状态 | 描述 |
|------|------|
| uploading | 上传中 - 文件正在上传到服务器 |
| processing | 处理中 - 文件正在进行解析和处理 |
| completed | 已完成 - 文件上传和处理完成 |
| failed | 失败 - 上传或处理过程中出现错误 |

### 4.7 文件类型映射

| 扩展名 | 前端类型 | 描述 |
|--------|----------|------|
| .pdf | pdf | PDF文档 |
| .xls, .xlsx | excel | Excel表格 |
| .doc, .docx | word | Word文档 |
| .jpg, .jpeg, .png | image | 图片文件 |
| 其他 | pdf | 默认显示为PDF图标 |

### 4.8 文件大小格式化

系统会自动格式化文件大小显示：
- 小于1KB: 显示为 "xxx B"
- 1KB-1MB: 显示为 "xxx.x KB"
- 大于1MB: 显示为 "xxx.x MB"

## 5. 报告生成

### 5.1 创建知识库

**接口地址**: `POST /api/create_knowledge_base`

**描述**: 上传文件并创建RAG知识库，完成文档解析

**请求头**:
```
Content-Type: multipart/form-data
```

**请求参数** (表单数据):
- `files`: 文件列表 (必填) - 支持多文件上传
- `company_name`: 公司名称 (必填) - 用于创建知识库名称

**处理流程**:
1. 动态创建RAG知识库
2. 上传所有文档到知识库
3. 启动文档解析任务
4. 返回知识库信息

**成功响应** (200):
```json
{
  "success": true,
  "message": "知识库处理流程成功完成!",
  "dataset_id": "dataset_123",
  "document_ids": ["doc_1", "doc_2", "doc_3"],
  "company_name": "西安市新希望医疗器械有限公司",
  "kb_name": "西安市新希望医疗器械有限公司",
  "parsing_info": {
    "code": 0,
    "message": "success"
  },
  "log": [
    "后端流程开始...",
    "公司名称: 西安市新希望医疗器械有限公司",
    "正在创建知识库: 西安市新希望医疗器械有限公司...",
    "知识库创建成功! ID: dataset_123",
    "开始上传文档...",
    "文档解析任务已成功提交!"
  ]
}
```

**错误响应**:
- **400**: 参数错误
```json
{
  "error": "请求中未找到文件部分"
}
```
- **400**: 缺少公司名称
```json
{
  "error": "请提供公司名称"
}
```
- **500**: 处理失败
```json
{
  "error": "处理流程失败: 具体错误信息",
  "log": ["错误日志..."]
}
```

### 5.2 检查知识库状态

**接口地址**: `GET /api/check_knowledge_base/{company_name}`

**描述**: 检查指定公司的知识库是否存在且解析完成

**路径参数**:
- `company_name`: 公司名称 (必填)

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "exists": true,
    "parsing_complete": true,
    "dataset_id": "dataset_123",
    "document_count": 3,
    "kb_name": "西安市新希望医疗器械有限公司"
  }
}
```

**知识库不存在**:
```json
{
  "success": true,
  "data": {
    "exists": false,
    "parsing_complete": false
  }
}
```

### 5.3 检查文档解析状态

**接口地址**: `POST /api/check_parsing_status`

**描述**: 查询指定文档的解析状态

**请求参数**:
```json
{
  "dataset_id": "string",
  "document_ids": ["string"]
}
```

**成功响应** (200):
```json
{
  "code": 0,
  "data": {
    "docs": [
      {
        "id": "doc_1",
        "name": "企业营业执照.pdf",
        "progress": 1.0,
        "progress_msg": "解析完成",
        "run": "1",
        "chunk_count": 15
      },
      {
        "id": "doc_2",
        "name": "财务报表.xlsx",
        "progress": 0.75,
        "progress_msg": "解析中...",
        "run": "1",
        "chunk_count": 8
      }
    ]
  }
}
```

### 5.4 生成报告

**接口地址**: `POST /api/generate_report`

**描述**: 基于知识库生成征信分析报告

**请求参数**:
```json
{
  "dataset_id": "string",           // 知识库ID，必填
  "company_name": "string"          // 公司名称，可选，默认值可用
}
```

**成功响应** (200):
```json
{
  "success": true,
  "message": "报告生成成功",
  "workflow_run_id": "run_123",
  "content": "# 征信分析报告\n\n## 企业基本信息\n...",
  "metadata": {
    "company": "西安市新希望医疗器械有限公司",
    "report_type": "credit_analysis",
    "generated_at": "2025-07-09T10:30:00",
    "workflow_id": "workflow_456"
  },
  "events": [
    {
      "event": "workflow_started",
      "timestamp": "2025-07-09T10:30:00"
    },
    {
      "event": "analysis_completed",
      "timestamp": "2025-07-09T10:32:00"
    }
  ],
  "parsing_complete": true
}
```

**错误响应**:
- **400**: 参数错误
```json
{
  "error": "缺少必要参数: dataset_id"
}
```
- **400**: 解析未完成
```json
{
  "error": "文档解析尚未完成，请等待解析完成后再生成报告",
  "parsing_complete": false
}
```

### 5.5 查询报告状态

**接口地址**: `GET /api/report_status/{workflow_run_id}`

**描述**: 查询报告生成状态和内容

**路径参数**:
- `workflow_run_id`: 工作流运行ID (必填)

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "status": "completed",
    "progress": 100,
    "content": "# 征信分析报告\n\n完整的报告内容...",
    "metadata": {
      "company": "西安市新希望医疗器械有限公司",
      "report_type": "credit_analysis",
      "generated_at": "2025-07-09T10:30:00"
    },
    "events": [
      {
        "event": "workflow_started",
        "timestamp": "2025-07-09T10:30:00"
      },
      {
        "event": "workflow_finished",
        "timestamp": "2025-07-09T10:32:00"
      }
    ],
    "company_name": "西安市新希望医疗器械有限公司"
  }
}
```

**报告不存在**:
```json
{
  "success": false,
  "error": "报告不存在或已过期"
}
```

### 5.6 报告生成流程说明

#### 完整流程
1. **上传文档**: 调用 `/api/create_knowledge_base` 上传文件
2. **检查解析**: 调用 `/api/check_parsing_status` 确认解析完成
3. **生成报告**: 调用 `/api/generate_report` 生成分析报告
4. **查询结果**: 调用 `/api/report_status/{id}` 获取报告内容

#### 示例代码
```javascript
// 1. 创建知识库
const formData = new FormData();
formData.append('company_name', '测试公司');
files.forEach(file => formData.append('files', file));

const kbResponse = await fetch('/api/create_knowledge_base', {
  method: 'POST',
  body: formData
});

// 2. 生成报告
const reportResponse = await fetch('/api/generate_report', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    dataset_id: kbResponse.dataset_id,
    company_name: '测试公司'
  })
});

// 3. 获取报告内容
const statusResponse = await fetch(`/api/report_status/${reportResponse.workflow_run_id}`);
```

## 6. 统计和系统

### 6.1 获取仪表板统计

**接口地址**: `GET /api/stats/dashboard`

**描述**: 获取系统核心统计指标，用于仪表板展示

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "projects": {
      "total": 12,
      "completed": 4,
      "processing": 8,
      "completion_rate": 33.3
    },
    "documents": {
      "total": 45,
      "completed": 42,
      "completion_rate": 93.3
    },
    "users": {
      "total": 5,
      "active": 5
    },
    "average_score": 78
  }
}
```

**数据说明**:
- `projects.total`: 总项目数
- `projects.completed`: 已完成项目数
- `projects.processing`: 处理中项目数
- `projects.completion_rate`: 完成率百分比
- `documents.total`: 总文档数
- `documents.completed`: 已处理文档数
- `documents.completion_rate`: 文档处理完成率
- `users.total`: 总用户数
- `users.active`: 活跃用户数
- `average_score`: 平均征信评分

### 6.2 获取趋势数据 (建议新增)

**接口地址**: `GET /api/stats/trends`

**描述**: 获取历史趋势数据，用于图表展示

**查询参数**:
- `period`: 时间周期 (`month`, `quarter`, `year`) 默认: `month`
- `months`: 月份数量 (默认: 6)

**建议响应格式**:
```json
{
  "success": true,
  "data": [
    {
      "period": "2025-01",
      "risk_projects": 12,
      "normal_projects": 45,
      "average_score": 78,
      "total_projects": 57
    },
    {
      "period": "2025-02",
      "risk_projects": 8,
      "normal_projects": 52,
      "average_score": 82,
      "total_projects": 60
    }
  ]
}
```

### 6.3 获取最近活动 (建议新增)

**接口地址**: `GET /api/logs/recent`

**描述**: 获取最近的系统活动，用于活动时间线展示

**查询参数**:
- `limit`: 返回数量 (默认: 10，最大: 50)
- `types`: 活动类型过滤 (可选)

**建议响应格式**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "type": "report_generated",
      "title": "腾讯科技征信报告已生成",
      "description": "项目ID: 1, 评分: 85",
      "user_name": "张三",
      "created_at": "2025-07-09T10:30:00",
      "relative_time": "2分钟前"
    },
    {
      "id": 2,
      "type": "document_uploaded",
      "title": "阿里巴巴财务文档上传完成",
      "description": "文件: 财务报表.pdf",
      "user_name": "李四",
      "created_at": "2025-07-09T10:15:00",
      "relative_time": "15分钟前"
    }
  ]
}
```

### 6.4 系统健康检查

**接口地址**: `GET /health`

**描述**: 检查系统运行状态和数据库连接

**成功响应** (200):
```json
{
  "status": "healthy",
  "message": "征信管理系统后端服务运行正常",
  "database": "connected",
  "users": 5,
  "timestamp": "2025-07-09T10:30:00",
  "version": "1.0.0"
}
```

**系统异常响应** (500):
```json
{
  "status": "unhealthy",
  "message": "系统运行异常",
  "database": "disconnected",
  "errors": ["数据库连接失败"]
}
```

### 6.5 获取系统日志

**接口地址**: `GET /api/logs`

**描述**: 获取系统操作日志，支持分页和过滤

**查询参数**:
- `page`: 页码 (默认: 1)
- `limit`: 每页数量 (默认: 50，最大: 100)
- `action`: 操作类型过滤 (可选)
- `user_id`: 用户ID过滤 (可选)
- `resource_type`: 资源类型过滤 (可选)
- `start_date`: 开始日期 (格式: YYYY-MM-DD)
- `end_date`: 结束日期 (格式: YYYY-MM-DD)

**成功响应** (200):
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "user_name": "管理员",
      "action": "user_login",
      "resource_type": "user",
      "resource_id": 1,
      "details": "用户 admin 登录系统",
      "ip_address": "127.0.0.1",
      "created_at": "2025-07-09T10:30:00"
    },
    {
      "id": 2,
      "user_id": 2,
      "user_name": "分析师",
      "action": "project_create",
      "resource_type": "project",
      "resource_id": 13,
      "details": "创建项目: 新企业征信项目",
      "ip_address": "192.168.1.100",
      "created_at": "2025-07-09T10:25:00"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 100,
    "pages": 2
  }
}
```

### 6.6 常见操作类型

| 操作类型 | 描述 |
|----------|------|
| user_login | 用户登录 |
| user_logout | 用户登出 |
| project_create | 创建项目 |
| project_update | 更新项目 |
| project_delete | 删除项目 |
| document_upload | 上传文档 |
| document_download | 下载文档 |
| document_delete | 删除文档 |
| report_generate | 生成报告 |
| knowledge_base_create | 创建知识库 |

### 6.7 系统监控指标

系统提供以下监控指标：

#### 性能指标
- API响应时间: < 200ms (平均)
- 数据库查询时间: < 100ms (平均)
- 文件上传速度: 根据文件大小和网络状况

#### 可用性指标
- 系统正常运行时间: 99.9%
- 数据库连接稳定性: 99.9%
- 文件存储可用性: 99.9%

#### 容量指标
- 最大并发用户: 100
- 最大文件上传大小: 50MB
- 数据库存储容量: 根据部署环境配置

## 7. 数据模型

### 7.1 用户模型 (User)

```typescript
interface User {
  id: number;                    // 用户ID，主键
  username: string;              // 用户名，唯一
  email: string;                 // 邮箱，唯一
  full_name: string;             // 姓名
  role: 'admin' | 'manager' | 'analyst' | 'user';  // 用户角色
  avatar_url?: string;           // 头像URL，可选
  is_active: boolean;            // 是否激活
  last_login?: string;           // 最后登录时间，ISO格式
  created_at: string;            // 创建时间，ISO格式
  updated_at: string;            // 更新时间，ISO格式
}
```

**角色权限说明**:
- `admin`: 系统管理员，拥有所有权限
- `manager`: 项目经理，可管理项目和用户
- `analyst`: 分析师，可创建和分析项目
- `user`: 普通用户，只能查看分配给自己的项目

### 7.2 项目模型 (Project)

```typescript
interface Project {
  id: number;                    // 项目ID，主键
  name: string;                  // 项目名称
  type: 'enterprise' | 'individual';  // 项目类型
  status: 'collecting' | 'processing' | 'completed' | 'archived';  // 项目状态
  description?: string;          // 项目描述，可选
  category?: string;             // 项目分类，可选
  priority: 'low' | 'medium' | 'high';  // 优先级
  score: number;                 // 征信评分 (0-100)
  riskLevel: 'low' | 'medium' | 'high';  // 风险等级
  progress: number;              // 进度百分比 (0-100)
  created_by: number;            // 创建者用户ID，外键
  assigned_to?: number;          // 分配给的用户ID，外键，可选
  documents: number;             // 文档数量 (计算字段)
  lastUpdate: string;            // 最后更新日期，YYYY-MM-DD格式
  created_at: string;            // 创建时间，ISO格式
  updated_at: string;            // 更新时间，ISO格式
}
```

**状态流转**:
```
collecting → processing → completed
     ↓
  archived (任何状态都可以归档)
```

**评分与风险等级对应**:
- 80-100分: low risk (低风险)
- 60-79分: medium risk (中风险)
- 0-59分: high risk (高风险)

### 7.3 文档模型 (Document)

```typescript
interface Document {
  id: number;                    // 文档ID，主键
  name: string;                  // 文档名称
  original_filename: string;     // 原始文件名
  file_path: string;             // 服务器文件路径
  file_size: number;             // 文件大小（字节）
  file_type: string;             // 文件类型 (pdf, excel, word, image)
  mime_type?: string;            // MIME类型
  project_id: number;            // 所属项目ID，外键
  status: 'uploading' | 'processing' | 'completed' | 'failed';  // 文档状态
  progress: number;              // 处理进度 (0-100)
  upload_by: number;             // 上传者用户ID，外键
  processing_result?: string;    // 处理结果
  error_message?: string;        // 错误信息
  created_at: string;            // 创建时间，ISO格式
  updated_at: string;            // 更新时间，ISO格式
}
```

**前端展示格式** (简化版):
```typescript
interface DocumentDisplay {
  id: number;
  name: string;                  // 显示名称
  project: string;               // 项目名称
  type: 'pdf' | 'excel' | 'word' | 'image';  // 前端文件类型
  size: string;                  // 格式化的文件大小 (如 "2.5 MB")
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  uploadTime: string;            // 格式化的上传时间 (如 "2025-07-09 10:30")
  progress: number;
}
```

### 7.4 项目成员模型 (ProjectMember)

```typescript
interface ProjectMember {
  id: number;                    // 成员关系ID，主键
  project_id: number;            // 项目ID，外键
  user_id: number;               // 用户ID，外键
  role: 'owner' | 'manager' | 'analyst' | 'viewer';  // 项目角色
  permissions?: object;          // 权限配置，JSON格式
  joined_at: string;             // 加入时间，ISO格式
}
```

**项目角色说明**:
- `owner`: 项目所有者，拥有所有权限
- `manager`: 项目管理者，可管理项目和成员
- `analyst`: 分析师，可进行分析操作
- `viewer`: 查看者，只能查看项目信息

### 7.5 分析报告模型 (AnalysisReport)

```typescript
interface AnalysisReport {
  id: number;                    // 报告ID，主键
  project_id: number;            // 所属项目ID，外键
  title: string;                 // 报告标题
  content: string;               // 报告内容，Markdown格式
  report_type: 'credit_analysis' | 'risk_assessment' | 'summary';  // 报告类型
  status: 'generating' | 'completed' | 'failed';  // 报告状态
  generated_by: number;          // 生成者用户ID，外键
  workflow_run_id?: string;      // 工作流运行ID，用于查询状态
  metadata?: object;             // 报告元数据，JSON格式
  created_at: string;            // 创建时间，ISO格式
  updated_at: string;            // 更新时间，ISO格式
}
```

**报告类型说明**:
- `credit_analysis`: 征信分析报告
- `risk_assessment`: 风险评估报告
- `summary`: 综合摘要报告

### 7.6 知识库模型 (KnowledgeBase)

```typescript
interface KnowledgeBase {
  id: number;                    // 知识库ID，主键
  name: string;                  // 知识库名称
  project_id: number;            // 所属项目ID，外键
  dataset_id?: string;           // RAG系统中的数据集ID
  status: 'creating' | 'ready' | 'updating' | 'error';  // 知识库状态
  document_count: number;        // 文档数量
  parsing_complete: boolean;     // 是否解析完成
  created_at: string;            // 创建时间，ISO格式
  updated_at: string;            // 更新时间，ISO格式
}
```

### 7.7 系统日志模型 (SystemLog)

```typescript
interface SystemLog {
  id: number;                    // 日志ID，主键
  user_id?: number;              // 操作用户ID，外键，可选
  action: string;                // 操作类型
  resource_type?: string;        // 资源类型
  resource_id?: number;          // 资源ID
  details?: string;              // 操作详情
  ip_address?: string;           // IP地址
  user_agent?: string;           // 用户代理
  created_at: string;            // 创建时间，ISO格式
}
```

**常见操作类型**:
- `user_login`, `user_logout`: 用户登录/登出
- `project_create`, `project_update`, `project_delete`: 项目操作
- `document_upload`, `document_download`, `document_delete`: 文档操作
- `report_generate`: 报告生成

### 7.8 系统设置模型 (SystemSetting)

```typescript
interface SystemSetting {
  id: number;                    // 设置ID，主键
  key: string;                   // 设置键，唯一
  value?: string;                // 设置值
  description?: string;          // 设置描述
  category: string;              // 设置分类
  is_public: boolean;            // 是否公开
  created_at: string;            // 创建时间，ISO格式
  updated_at: string;            // 更新时间，ISO格式
}
```

### 7.9 数据关系图

```
User (用户)
├── created_projects (创建的项目) → Project.created_by
├── assigned_projects (分配的项目) → Project.assigned_to
├── uploaded_documents (上传的文档) → Document.upload_by
├── project_memberships (项目成员关系) → ProjectMember.user_id
├── generated_reports (生成的报告) → AnalysisReport.generated_by
└── system_logs (系统日志) → SystemLog.user_id

Project (项目)
├── documents (项目文档) → Document.project_id
├── members (项目成员) → ProjectMember.project_id
├── reports (分析报告) → AnalysisReport.project_id
├── knowledge_base (知识库) → KnowledgeBase.project_id
├── creator (创建者) → User.id
└── assignee (分配者) → User.id

Document (文档)
├── project (所属项目) → Project.id
└── uploader (上传者) → User.id

ProjectMember (项目成员)
├── project (项目) → Project.id
└── user (用户) → User.id

AnalysisReport (分析报告)
├── project (所属项目) → Project.id
└── generator (生成者) → User.id

KnowledgeBase (知识库)
└── project (所属项目) → Project.id

SystemLog (系统日志)
└── user (操作用户) → User.id
```

## 8. 前端集成

### 8.1 API服务层架构

前端采用分层架构设计，通过统一的API服务层处理所有HTTP请求，支持Mock数据和真实API的无缝切换。

#### 架构层次
```
页面组件 (Pages)
    ↓
业务服务层 (Services)
    ↓
基础API客户端 (ApiClient)
    ↓
Mock系统 / 真实API
```

#### 基础API客户端

```typescript
// services/api.ts
import { MOCK_CONFIG, API_BASE_URL } from '@/config/mock';

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async request<T>(endpoint: string, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    const { method = 'GET', headers = {}, body } = config;

    try {
      // Mock模式检查
      if (MOCK_CONFIG.enabled) {
        mockLog(`Mock API call: ${method} ${endpoint}`, body);
        await mockDelay();

        if (shouldSimulateError()) {
          throw new Error('Mock API Error: Simulated network error');
        }

        // 由具体服务类实现Mock逻辑
        return {
          success: false,
          error: 'Mock implementation not found'
        };
      }

      // 真实API调用
      const url = `${this.baseUrl}${endpoint}`;
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        data,
      };

    } catch (error) {
      console.error(`API Error: ${method} ${endpoint}`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  // 便捷方法
  async get<T>(endpoint: string, headers?: Record<string, string>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET', headers });
  }

  async post<T>(endpoint: string, body?: any, headers?: Record<string, string>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'POST', body, headers });
  }

  async put<T>(endpoint: string, body?: any, headers?: Record<string, string>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'PUT', body, headers });
  }

  async delete<T>(endpoint: string, headers?: Record<string, string>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE', headers });
  }
}

export const apiClient = new ApiClient();
```

### 8.2 业务服务层

#### 项目服务

```typescript
// services/projectService.ts
import { apiClient, ApiResponse } from './api';
import { MOCK_CONFIG, mockLog, mockDelay } from '@/config/mock';
import { Project, mockProjects } from '@/data/mockData';

export interface CreateProjectData {
  name: string;
  type: 'enterprise' | 'individual';
  description?: string;
  category?: string;
  priority?: 'low' | 'medium' | 'high';
  assigned_to?: number;
}

export interface ProjectQueryParams {
  type?: 'enterprise' | 'individual';
  status?: 'collecting' | 'processing' | 'completed';
  search?: string;
  page?: number;
  limit?: number;
}

class ProjectService {
  async getProjects(params?: ProjectQueryParams): Promise<ApiResponse<Project[]>> {
    if (MOCK_CONFIG.enabled) {
      mockLog('Getting projects list', params);
      await mockDelay();

      let filteredProjects = [...mockProjects];

      // 应用过滤条件
      if (params) {
        if (params.type) {
          filteredProjects = filteredProjects.filter(p => p.type === params.type);
        }
        if (params.status) {
          filteredProjects = filteredProjects.filter(p => p.status === params.status);
        }
        if (params.search) {
          const searchLower = params.search.toLowerCase();
          filteredProjects = filteredProjects.filter(p =>
            p.name.toLowerCase().includes(searchLower)
          );
        }
      }

      return {
        success: true,
        data: filteredProjects
      };
    }

    // 真实API调用
    const queryString = params ? new URLSearchParams(params as any).toString() : '';
    const endpoint = `/projects${queryString ? `?${queryString}` : ''}`;
    return apiClient.get<Project[]>(endpoint);
  }

  async getProjectById(id: number): Promise<ApiResponse<Project>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Getting project by ID: ${id}`);
      await mockDelay();

      const project = mockProjects.find(p => p.id === id);
      if (!project) {
        return {
          success: false,
          error: 'Project not found'
        };
      }

      return {
        success: true,
        data: project
      };
    }

    return apiClient.get<Project>(`/projects/${id}`);
  }

  async createProject(data: CreateProjectData): Promise<ApiResponse<Project>> {
    if (MOCK_CONFIG.enabled) {
      mockLog('Creating new project', data);
      await mockDelay();

      const newProject: Project = {
        id: Math.max(...mockProjects.map(p => p.id)) + 1,
        name: data.name,
        type: data.type,
        status: 'collecting',
        score: 0,
        riskLevel: 'low',
        lastUpdate: new Date().toISOString().split('T')[0],
        documents: 0,
        progress: 0
      };

      mockProjects.push(newProject);

      return {
        success: true,
        data: newProject
      };
    }

    return apiClient.post<Project>('/projects', data);
  }

  async updateProject(id: number, data: Partial<CreateProjectData>): Promise<ApiResponse<Project>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Updating project ${id}`, data);
      await mockDelay();

      const projectIndex = mockProjects.findIndex(p => p.id === id);
      if (projectIndex === -1) {
        return {
          success: false,
          error: 'Project not found'
        };
      }

      mockProjects[projectIndex] = {
        ...mockProjects[projectIndex],
        ...data,
        lastUpdate: new Date().toISOString().split('T')[0]
      };

      return {
        success: true,
        data: mockProjects[projectIndex]
      };
    }

    return apiClient.put<Project>(`/projects/${id}`, data);
  }

  async deleteProject(id: number): Promise<ApiResponse<void>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Deleting project ${id}`);
      await mockDelay();

      const projectIndex = mockProjects.findIndex(p => p.id === id);
      if (projectIndex === -1) {
        return {
          success: false,
          error: 'Project not found'
        };
      }

      mockProjects.splice(projectIndex, 1);

      return {
        success: true,
        message: 'Project deleted successfully'
      };
    }

    return apiClient.delete(`/projects/${id}`);
  }
}

export const projectService = new ProjectService();
```

#### 文档服务

```typescript
// services/documentService.ts
import { apiClient, ApiResponse } from './api';
import { MOCK_CONFIG, mockLog, mockDelay } from '@/config/mock';
import { Document, mockDocuments } from '@/data/mockData';

export interface UploadDocumentData {
  name: string;
  project: string;
  type: 'pdf' | 'excel' | 'word' | 'image';
  file: File;
}

export interface DocumentQueryParams {
  project?: string;
  status?: 'completed' | 'processing' | 'failed';
  type?: 'pdf' | 'excel' | 'word' | 'image';
  search?: string;
  page?: number;
  limit?: number;
}

class DocumentService {
  async getDocuments(params?: DocumentQueryParams): Promise<ApiResponse<Document[]>> {
    if (MOCK_CONFIG.enabled) {
      mockLog('Getting documents list', params);
      await mockDelay();

      let filteredDocuments = [...mockDocuments];

      // 应用过滤条件
      if (params) {
        if (params.project) {
          filteredDocuments = filteredDocuments.filter(d =>
            d.project.toLowerCase().includes(params.project!.toLowerCase())
          );
        }
        if (params.status) {
          filteredDocuments = filteredDocuments.filter(d => d.status === params.status);
        }
        if (params.type) {
          filteredDocuments = filteredDocuments.filter(d => d.type === params.type);
        }
        if (params.search) {
          const searchLower = params.search.toLowerCase();
          filteredDocuments = filteredDocuments.filter(d =>
            d.name.toLowerCase().includes(searchLower) ||
            d.project.toLowerCase().includes(searchLower)
          );
        }
      }

      return {
        success: true,
        data: filteredDocuments
      };
    }

    const queryString = params ? new URLSearchParams(params as any).toString() : '';
    const endpoint = `/documents${queryString ? `?${queryString}` : ''}`;
    return apiClient.get<Document[]>(endpoint);
  }

  async uploadDocument(data: UploadDocumentData): Promise<ApiResponse<Document>> {
    if (MOCK_CONFIG.enabled) {
      mockLog('Uploading document', data);
      await mockDelay();

      const newDocument: Document = {
        id: Math.max(...mockDocuments.map(d => d.id)) + 1,
        name: data.name,
        project: data.project,
        type: data.type,
        size: `${(data.file.size / 1024 / 1024).toFixed(1)} MB`,
        status: 'completed',
        uploadTime: new Date().toLocaleString('zh-CN'),
        progress: 100
      };

      mockDocuments.push(newDocument);

      return {
        success: true,
        data: newDocument
      };
    }

    // 真实API调用需要使用FormData
    const formData = new FormData();
    formData.append('file', data.file);
    formData.append('project', data.project);
    formData.append('name', data.name);

    return apiClient.request<Document>('/documents/upload', {
      method: 'POST',
      body: formData,
      headers: {} // 不设置Content-Type，让浏览器自动设置
    });
  }

  async deleteDocument(id: number): Promise<ApiResponse<void>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Deleting document ${id}`);
      await mockDelay();

      const documentIndex = mockDocuments.findIndex(d => d.id === id);
      if (documentIndex === -1) {
        return {
          success: false,
          error: 'Document not found'
        };
      }

      mockDocuments.splice(documentIndex, 1);

      return {
        success: true,
        message: 'Document deleted successfully'
      };
    }

    return apiClient.delete(`/documents/${id}`);
  }

  async downloadDocument(id: number): Promise<ApiResponse<Blob>> {
    if (MOCK_CONFIG.enabled) {
      mockLog(`Downloading document ${id}`);
      await mockDelay();

      const document = mockDocuments.find(d => d.id === id);
      if (!document) {
        return {
          success: false,
          error: 'Document not found'
        };
      }

      // 创建模拟文件blob
      const mockContent = `Mock content for ${document.name}`;
      const blob = new Blob([mockContent], { type: 'text/plain' });

      return {
        success: true,
        data: blob
      };
    }

    return apiClient.get<Blob>(`/documents/${id}/download`);
  }
}

export const documentService = new DocumentService();
```

### 8.3 Mock系统配置

#### Mock配置文件

```typescript
// config/mock.ts
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === 'true';

export const MOCK_CONFIG = {
  enabled: USE_MOCK,
  delay: 500,                    // API响应延迟（毫秒）
  logging: true,                 // 是否显示Mock日志
  errorRate: 0.05,               // 错误模拟概率（0-1）
};

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5001/api';

// Mock工具函数
export const mockLog = (message: string, data?: any) => {
  if (MOCK_CONFIG.logging) {
    console.log(`[MOCK] ${message}`, data || '');
  }
};

export const mockDelay = () => {
  return new Promise(resolve => setTimeout(resolve, MOCK_CONFIG.delay));
};

export const shouldSimulateError = () => {
  return Math.random() < MOCK_CONFIG.errorRate;
};
```

#### Mock数据文件

```typescript
// data/mockData.ts
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
}

export interface Document {
  id: number;
  name: string;
  project: string;
  type: 'pdf' | 'excel' | 'word' | 'image';
  size: string;
  status: 'completed' | 'processing' | 'failed';
  uploadTime: string;
  progress: number;
}

export const mockProjects: Project[] = [
  {
    id: 1,
    name: "腾讯科技有限公司",
    type: "enterprise",
    status: "completed",
    score: 85,
    riskLevel: "low",
    lastUpdate: "2024-01-15",
    documents: 12,
    progress: 100
  },
  // ... 更多Mock数据
];

export const mockDocuments: Document[] = [
  {
    id: 1,
    name: "财务报表2023.pdf",
    project: "腾讯科技有限公司",
    type: "pdf",
    size: "2.3 MB",
    status: "completed",
    uploadTime: "2024-01-15 14:30",
    progress: 100
  },
  // ... 更多Mock数据
];
```

### 8.4 环境配置

#### 环境变量配置

```env
# .env.local (开发环境)
NEXT_PUBLIC_USE_MOCK=true
NEXT_PUBLIC_API_BASE_URL=http://localhost:5001/api

# .env.production (生产环境)
NEXT_PUBLIC_USE_MOCK=false
NEXT_PUBLIC_API_BASE_URL=https://api.example.com/api
```

#### 启动脚本

```json
{
  "scripts": {
    "dev": "next dev",
    "dev:mock": "NEXT_PUBLIC_USE_MOCK=true next dev",
    "dev:real": "NEXT_PUBLIC_USE_MOCK=false next dev",
    "build": "next build",
    "start": "next start"
  }
}
```

### 8.5 页面组件集成

#### 项目列表页面示例

```typescript
// app/projects/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { projectService } from '@/services/projectService';
import { Project } from '@/data/mockData';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProjects = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await projectService.getProjects();

      if (response.success && response.data) {
        setProjects(response.data);
      } else {
        setError(response.error || '加载项目失败');
      }
    } catch (err) {
      setError('网络错误，请稍后重试');
      console.error('Load projects error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  if (loading) return <div>加载中...</div>;
  if (error) return <div>错误: {error}</div>;

  return (
    <div>
      {projects.map(project => (
        <div key={project.id}>
          {project.name} - {project.status}
        </div>
      ))}
    </div>
  );
}
```

### 8.6 Mock状态指示器

```typescript
// components/MockIndicator.tsx
'use client';

import { MOCK_CONFIG } from '@/config/mock';

export default function MockIndicator() {
  if (!MOCK_CONFIG.enabled) return null;

  return (
    <div className="fixed top-4 right-4 bg-yellow-500 text-white px-3 py-1 rounded-full text-sm font-medium z-50">
      🎭 Mock模式
    </div>
  );
}
```

### 8.7 错误处理最佳实践

#### 统一错误处理

```typescript
// utils/errorHandler.ts
export const handleApiError = (error: string, context: string) => {
  console.error(`[${context}] API Error:`, error);

  // 根据错误类型显示不同的用户提示
  if (error.includes('network')) {
    return '网络连接异常，请检查网络设置';
  } else if (error.includes('401')) {
    return '登录已过期，请重新登录';
  } else if (error.includes('403')) {
    return '权限不足，无法执行此操作';
  } else if (error.includes('404')) {
    return '请求的资源不存在';
  } else {
    return '操作失败，请稍后重试';
  }
};
```

#### 在组件中使用

```typescript
const response = await projectService.getProjects();
if (!response.success) {
  const userFriendlyError = handleApiError(response.error || '', 'ProjectList');
  setError(userFriendlyError);
}
```

## 9. 错误处理

### 9.1 错误码定义

| 错误码 | 说明 |
|--------|------|
| AUTH_001 | 用户名或密码错误 |
| AUTH_002 | Token已过期 |
| AUTH_003 | 权限不足 |
| PROJ_001 | 项目不存在 |
| PROJ_002 | 项目名称已存在 |
| DOC_001 | 文档不存在 |
| DOC_002 | 不支持的文件类型 |
| DOC_003 | 文件大小超限 |
| SYS_001 | 系统内部错误 |

### 9.2 错误处理示例

```typescript
// 前端错误处理
try {
  const response = await projectService.getProjects();
  if (!response.success) {
    throw new Error(response.error);
  }
  // 处理成功响应
} catch (error) {
  console.error('获取项目列表失败:', error);
  // 显示错误提示
}
```

## 9. 错误处理

### 9.1 错误码定义

| 错误码 | HTTP状态码 | 说明 | 解决方案 |
|--------|------------|------|----------|
| AUTH_001 | 401 | 用户名或密码错误 | 检查登录凭据 |
| AUTH_002 | 401 | Token已过期 | 重新登录获取新token |
| AUTH_003 | 403 | 权限不足 | 联系管理员分配权限 |
| PROJ_001 | 404 | 项目不存在 | 检查项目ID是否正确 |
| PROJ_002 | 400 | 项目名称已存在 | 使用不同的项目名称 |
| DOC_001 | 404 | 文档不存在 | 检查文档ID是否正确 |
| DOC_002 | 400 | 不支持的文件类型 | 使用支持的文件格式 |
| DOC_003 | 400 | 文件大小超限 | 压缩文件或分割上传 |
| KB_001 | 400 | 知识库创建失败 | 检查文件格式和网络连接 |
| KB_002 | 400 | 文档解析未完成 | 等待解析完成后重试 |
| SYS_001 | 500 | 系统内部错误 | 联系技术支持 |

### 9.2 统一错误响应格式

```json
{
  "success": false,
  "error": "错误描述信息",
  "code": "ERROR_CODE",
  "details": {
    "field": "具体字段错误信息",
    "timestamp": "2025-07-09T10:30:00Z"
  }
}
```

### 9.3 前端错误处理示例

```typescript
// 统一错误处理函数
export const handleApiError = (error: string, context: string): string => {
  console.error(`[${context}] API Error:`, error);

  // 根据错误类型返回用户友好的提示
  if (error.includes('401')) {
    return '登录已过期，请重新登录';
  } else if (error.includes('403')) {
    return '权限不足，无法执行此操作';
  } else if (error.includes('404')) {
    return '请求的资源不存在';
  } else if (error.includes('network')) {
    return '网络连接异常，请检查网络设置';
  } else {
    return '操作失败，请稍后重试';
  }
};

// 在组件中使用
try {
  const response = await projectService.getProjects();
  if (!response.success) {
    const userMessage = handleApiError(response.error || '', 'ProjectList');
    setError(userMessage);
  }
} catch (error) {
  const userMessage = handleApiError(error.message, 'ProjectList');
  setError(userMessage);
}
```

## 10. 最佳实践

### 10.1 认证和安全

#### JWT Token管理
```typescript
// Token存储和管理
class TokenManager {
  private static readonly TOKEN_KEY = 'auth_token';

  static setToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  static getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  static removeToken(): void {
    localStorage.removeItem(this.TOKEN_KEY);
  }

  static isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp * 1000 < Date.now();
    } catch {
      return true;
    }
  }
}

// 自动添加认证头
apiClient.interceptors.request.use((config) => {
  const token = TokenManager.getToken();
  if (token && !TokenManager.isTokenExpired(token)) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

#### 权限检查
```typescript
// 权限检查Hook
export const usePermission = (requiredRole: UserRole) => {
  const { user } = useAuth();

  const hasPermission = useMemo(() => {
    if (!user) return false;

    const roleHierarchy = {
      'user': 1,
      'analyst': 2,
      'manager': 3,
      'admin': 4
    };

    return roleHierarchy[user.role] >= roleHierarchy[requiredRole];
  }, [user, requiredRole]);

  return hasPermission;
};
```

### 10.2 API调用优化

#### 请求缓存
```typescript
// 简单的内存缓存
class ApiCache {
  private cache = new Map<string, { data: any; timestamp: number }>();
  private readonly TTL = 5 * 60 * 1000; // 5分钟

  set(key: string, data: any): void {
    this.cache.set(key, { data, timestamp: Date.now() });
  }

  get(key: string): any | null {
    const item = this.cache.get(key);
    if (!item) return null;

    if (Date.now() - item.timestamp > this.TTL) {
      this.cache.delete(key);
      return null;
    }

    return item.data;
  }

  clear(): void {
    this.cache.clear();
  }
}

// 在服务中使用缓存
class ProjectService {
  private cache = new ApiCache();

  async getProjects(params?: ProjectQueryParams): Promise<ApiResponse<Project[]>> {
    const cacheKey = `projects_${JSON.stringify(params)}`;
    const cached = this.cache.get(cacheKey);

    if (cached) {
      return { success: true, data: cached };
    }

    const response = await apiClient.get<Project[]>('/projects');
    if (response.success) {
      this.cache.set(cacheKey, response.data);
    }

    return response;
  }
}
```

#### 请求去重
```typescript
// 防止重复请求
class RequestDeduplicator {
  private pendingRequests = new Map<string, Promise<any>>();

  async deduplicate<T>(key: string, requestFn: () => Promise<T>): Promise<T> {
    if (this.pendingRequests.has(key)) {
      return this.pendingRequests.get(key)!;
    }

    const promise = requestFn().finally(() => {
      this.pendingRequests.delete(key);
    });

    this.pendingRequests.set(key, promise);
    return promise;
  }
}
```

### 10.3 文件上传优化

#### 分片上传
```typescript
// 大文件分片上传
class ChunkedUploader {
  private readonly CHUNK_SIZE = 1024 * 1024; // 1MB

  async uploadFile(file: File, onProgress?: (progress: number) => void): Promise<string> {
    const chunks = Math.ceil(file.size / this.CHUNK_SIZE);
    const uploadId = await this.initializeUpload(file.name, file.size);

    for (let i = 0; i < chunks; i++) {
      const start = i * this.CHUNK_SIZE;
      const end = Math.min(start + this.CHUNK_SIZE, file.size);
      const chunk = file.slice(start, end);

      await this.uploadChunk(uploadId, i, chunk);

      if (onProgress) {
        onProgress(((i + 1) / chunks) * 100);
      }
    }

    return this.finalizeUpload(uploadId);
  }

  private async initializeUpload(filename: string, size: number): Promise<string> {
    const response = await apiClient.post('/upload/init', { filename, size });
    return response.data.uploadId;
  }

  private async uploadChunk(uploadId: string, chunkIndex: number, chunk: Blob): Promise<void> {
    const formData = new FormData();
    formData.append('uploadId', uploadId);
    formData.append('chunkIndex', chunkIndex.toString());
    formData.append('chunk', chunk);

    await apiClient.post('/upload/chunk', formData);
  }

  private async finalizeUpload(uploadId: string): Promise<string> {
    const response = await apiClient.post('/upload/finalize', { uploadId });
    return response.data.fileUrl;
  }
}
```

### 10.4 性能监控

#### API性能监控
```typescript
// API性能监控
class PerformanceMonitor {
  static measureApiCall<T>(
    apiCall: () => Promise<T>,
    endpoint: string
  ): Promise<T> {
    const startTime = performance.now();

    return apiCall().finally(() => {
      const duration = performance.now() - startTime;

      // 记录性能数据
      console.log(`API ${endpoint} took ${duration.toFixed(2)}ms`);

      // 发送到监控服务
      if (duration > 1000) { // 超过1秒的慢请求
        this.reportSlowRequest(endpoint, duration);
      }
    });
  }

  private static reportSlowRequest(endpoint: string, duration: number): void {
    // 发送到监控服务
    fetch('/api/monitoring/slow-requests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ endpoint, duration, timestamp: Date.now() })
    }).catch(console.error);
  }
}

// 使用示例
const projects = await PerformanceMonitor.measureApiCall(
  () => projectService.getProjects(),
  'GET /api/projects'
);
```

### 10.5 开发调试

#### API调试工具
```typescript
// API调试工具
class ApiDebugger {
  static logRequest(method: string, url: string, data?: any): void {
    if (process.env.NODE_ENV === 'development') {
      console.group(`🚀 API Request: ${method} ${url}`);
      if (data) console.log('Data:', data);
      console.groupEnd();
    }
  }

  static logResponse(method: string, url: string, response: any, duration: number): void {
    if (process.env.NODE_ENV === 'development') {
      console.group(`✅ API Response: ${method} ${url} (${duration}ms)`);
      console.log('Response:', response);
      console.groupEnd();
    }
  }

  static logError(method: string, url: string, error: any): void {
    if (process.env.NODE_ENV === 'development') {
      console.group(`❌ API Error: ${method} ${url}`);
      console.error('Error:', error);
      console.groupEnd();
    }
  }
}
```

### 10.6 部署和运维

#### 环境配置
```typescript
// 环境配置管理
export const config = {
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5001/api',
    timeout: parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '10000'),
    retryAttempts: parseInt(process.env.NEXT_PUBLIC_API_RETRY_ATTEMPTS || '3'),
  },
  mock: {
    enabled: process.env.NEXT_PUBLIC_USE_MOCK === 'true',
    delay: parseInt(process.env.NEXT_PUBLIC_MOCK_DELAY || '500'),
  },
  features: {
    enableAnalytics: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true',
    enableErrorReporting: process.env.NEXT_PUBLIC_ENABLE_ERROR_REPORTING === 'true',
  }
};
```

#### 健康检查
```typescript
// 系统健康检查
export const healthCheck = async (): Promise<boolean> => {
  try {
    const response = await fetch('/health', {
      method: 'GET',
      timeout: 5000
    });
    return response.ok;
  } catch {
    return false;
  }
};

// 定期健康检查
setInterval(async () => {
  const isHealthy = await healthCheck();
  if (!isHealthy) {
    console.warn('System health check failed');
    // 触发告警或重连逻辑
  }
}, 30000); // 每30秒检查一次
```

## 11. 总结

### 11.1 API覆盖范围

本文档涵盖了征信管理系统的完整API接口：

- ✅ **认证系统**: 用户登录、权限验证、用户管理
- ✅ **项目管理**: 项目CRUD、状态管理、成员管理
- ✅ **文档管理**: 文件上传下载、文档处理、状态跟踪
- ✅ **报告生成**: RAG知识库、报告生成、状态查询
- ✅ **统计系统**: 仪表板数据、趋势分析、系统监控
- ✅ **系统功能**: 健康检查、日志管理、错误处理

### 11.2 技术特性

- **前后端分离**: 清晰的API边界和数据格式
- **Mock系统**: 完整的开发时Mock数据支持
- **类型安全**: TypeScript类型定义和接口规范
- **错误处理**: 统一的错误码和处理机制
- **性能优化**: 缓存、分页、请求优化策略
- **安全性**: JWT认证、权限控制、数据验证

### 11.3 开发指南

1. **开发环境**: 使用Mock模式进行前端开发
2. **接口对接**: 按照文档规范进行API集成
3. **错误处理**: 实现统一的错误处理机制
4. **性能优化**: 应用缓存和优化策略
5. **测试验证**: 编写完整的API测试用例

### 11.4 后续规划

- **API版本管理**: 实现API版本控制机制
- **实时通信**: 添加WebSocket支持
- **批量操作**: 实现批量数据处理接口
- **数据导出**: 添加数据导出功能
- **审计日志**: 完善操作审计和追踪

---

**文档版本**: v1.0
**最后更新**: 2025-07-09
**维护者**: 征信管理系统开发团队
**联系方式**: dev-team@example.com
