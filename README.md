# 征信管理系统

## 项目简介
一个完整的征信管理系统，包含前端界面和后端API服务。

## 项目结构
```
.
├── frontend/           # 前端项目 (Next.js)
├── generated_backend/  # 后端项目 (Flask)
├── start.sh           # 快速启动脚本
└── README.md          # 项目说明
```

## 快速开始

### 环境要求
- Node.js (推荐 v18+)
- Python 3.8+
- npm 或 yarn

### 安装依赖

#### 前端依赖
```bash
cd frontend
npm install
```

#### 后端依赖
```bash
cd generated_backend
pip install -r requirements.txt
```

### 启动服务

#### 方式一：使用启动脚本（推荐）
```bash
./start.sh
```

#### 方式二：手动启动

启动后端服务：
```bash
cd generated_backend
python app.py
```

启动前端服务：
```bash
cd frontend
npm run dev
```

### 访问地址
- 前端：http://localhost:3000
- 后端：http://localhost:5001
- 后端健康检查：http://localhost:5001/health

## 功能特性
- 项目管理
- 文档上传与处理
- 征信分析与报告生成
- 统计数据展示
- 用户权限管理

## 技术栈

### 前端
- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- Recharts

### 后端
- Flask
- SQLAlchemy
- Flask-CORS
- JWT认证

## 开发说明
项目采用前后端分离架构，前端使用Next.js构建，后端使用Flask提供API服务。

## 许可证
本项目仅供学习和研究使用。
