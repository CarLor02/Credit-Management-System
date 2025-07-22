# 征信管理系统数据库设计

## 数据库表结构设计

### 新增表结构（2025-07-10）

#### 8. 财务分析表 (financial_analysis)
```sql
CREATE TABLE financial_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,

    -- 基础财务指标
    total_assets DECIMAL(15,2),           -- 资产总额
    annual_revenue DECIMAL(15,2),         -- 年营业收入
    net_profit DECIMAL(15,2),             -- 净利润
    debt_ratio DECIMAL(5,2),              -- 负债率(%)

    -- 流动性指标
    current_ratio DECIMAL(8,2),           -- 流动比率
    quick_ratio DECIMAL(8,2),             -- 速动比率
    cash_ratio DECIMAL(8,2),              -- 现金比率

    -- 盈利能力指标
    gross_profit_margin DECIMAL(5,2),     -- 毛利率(%)
    net_profit_margin DECIMAL(5,2),       -- 净利率(%)
    roe DECIMAL(5,2),                     -- 净资产收益率(%)
    roa DECIMAL(5,2),                     -- 总资产收益率(%)

    -- 运营能力指标
    inventory_turnover DECIMAL(8,2),      -- 存货周转率
    receivables_turnover DECIMAL(8,2),    -- 应收账款周转率
    total_asset_turnover DECIMAL(8,2),    -- 总资产周转率

    -- 发展能力指标
    revenue_growth_rate DECIMAL(5,2),     -- 营收增长率(%)
    profit_growth_rate DECIMAL(5,2),      -- 利润增长率(%)

    -- 分析期间
    analysis_year INTEGER NOT NULL,       -- 分析年度
    analysis_quarter INTEGER,             -- 分析季度(1-4)

    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE(project_id, analysis_year, analysis_quarter)
);
```

#### 9. 经营状况表 (business_status)
```sql
CREATE TABLE business_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,

    -- 经营资质状态
    business_license_status ENUM('normal', 'expiring', 'expired') DEFAULT 'normal',
    business_license_expiry DATE,
    tax_registration_status ENUM('normal', 'abnormal') DEFAULT 'normal',
    organization_code_status ENUM('normal', 'expiring', 'expired') DEFAULT 'normal',

    -- 合规状态
    legal_violations INTEGER DEFAULT 0,    -- 违法记录数量
    tax_compliance_status ENUM('normal', 'warning', 'violation') DEFAULT 'normal',
    environmental_compliance ENUM('compliant', 'warning', 'violation') DEFAULT 'compliant',
    labor_compliance ENUM('compliant', 'warning', 'violation') DEFAULT 'compliant',

    -- 经营风险
    market_risk_level ENUM('low', 'medium', 'high') DEFAULT 'low',
    financial_risk_level ENUM('low', 'medium', 'high') DEFAULT 'low',
    operational_risk_level ENUM('low', 'medium', 'high') DEFAULT 'low',

    -- 行业地位
    industry_ranking INTEGER,             -- 行业排名
    market_share DECIMAL(5,2),           -- 市场份额(%)
    competitive_advantage TEXT,           -- 竞争优势描述

    -- 经营状况评分
    overall_score INTEGER DEFAULT 0,     -- 总体评分(0-100)
    qualification_score INTEGER DEFAULT 0, -- 资质评分
    compliance_score INTEGER DEFAULT 0,   -- 合规评分
    risk_score INTEGER DEFAULT 0,        -- 风险评分

    -- 备注信息
    risk_factors TEXT,                    -- 风险因素描述
    improvement_suggestions TEXT,         -- 改进建议

    -- 元数据
    evaluation_date DATE NOT NULL,       -- 评估日期
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
```

#### 10. 项目时间轴表 (project_timeline)
```sql
CREATE TABLE project_timeline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,

    -- 事件信息
    event_title VARCHAR(200) NOT NULL,    -- 事件标题
    event_description TEXT,               -- 事件描述
    event_type ENUM('milestone', 'document', 'analysis', 'review', 'report', 'other') DEFAULT 'other',

    -- 事件状态
    status ENUM('completed', 'in_progress', 'pending', 'cancelled') DEFAULT 'pending',
    priority ENUM('low', 'medium', 'high') DEFAULT 'medium',

    -- 时间信息
    event_date DATE NOT NULL,            -- 事件日期
    planned_date DATE,                   -- 计划日期
    completed_date DATE,                 -- 完成日期

    -- 关联信息
    related_document_id INTEGER,         -- 关联文档ID
    related_user_id INTEGER,             -- 关联用户ID

    -- 进度信息
    progress INTEGER DEFAULT 0,          -- 进度百分比(0-100)

    -- 元数据
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (related_document_id) REFERENCES documents(id) ON DELETE SET NULL,
    FOREIGN KEY (related_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);
```

### 1. 用户表 (users)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role ENUM('admin', 'user') DEFAULT 'user',
    avatar_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2. 项目表 (projects)
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    type ENUM('enterprise', 'individual') NOT NULL,
    status ENUM('collecting', 'processing', 'completed', 'archived') DEFAULT 'collecting',
    description TEXT,
    category VARCHAR(50),
    priority ENUM('low', 'medium', 'high') DEFAULT 'medium',
    score INTEGER DEFAULT 0,
    risk_level ENUM('low', 'medium', 'high') DEFAULT 'low',
    progress INTEGER DEFAULT 0,
    created_by INTEGER NOT NULL,
    assigned_to INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (assigned_to) REFERENCES users(id)
);
```

### 3. 文档表 (documents)
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    mime_type VARCHAR(100),
    project_id INTEGER NOT NULL,
    status ENUM('uploading', 'processing', 'completed', 'failed') DEFAULT 'uploading',
    progress INTEGER DEFAULT 0,
    upload_by INTEGER NOT NULL,
    processing_result TEXT,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (upload_by) REFERENCES users(id)
);
```

### 4. 项目成员表 (project_members)
```sql
CREATE TABLE project_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role ENUM('owner', 'manager', 'analyst', 'viewer') DEFAULT 'viewer',
    permissions JSON,
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(project_id, user_id)
);
```

### 5. 分析报告表 (analysis_reports)
```sql
CREATE TABLE analysis_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    report_type ENUM('credit_analysis', 'risk_assessment', 'summary') NOT NULL,
    status ENUM('generating', 'completed', 'failed') DEFAULT 'generating',
    generated_by INTEGER NOT NULL,
    workflow_run_id VARCHAR(100),
    metadata JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (generated_by) REFERENCES users(id)
);
```

### 6. 知识库表 (knowledge_bases)
```sql
CREATE TABLE knowledge_bases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    project_id INTEGER NOT NULL,
    dataset_id VARCHAR(100),
    status ENUM('creating', 'ready', 'updating', 'error') DEFAULT 'creating',
    document_count INTEGER DEFAULT 0,
    parsing_complete BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
```

### 7. 系统日志表 (system_logs)
```sql
CREATE TABLE system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 8. 系统设置表 (system_settings)
```sql
CREATE TABLE system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    category VARCHAR(50) DEFAULT 'general',
    is_public BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 索引设计

```sql
-- 用户表索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);

-- 项目表索引
CREATE INDEX idx_projects_type ON projects(type);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created_by ON projects(created_by);
CREATE INDEX idx_projects_assigned_to ON projects(assigned_to);
CREATE INDEX idx_projects_created_at ON projects(created_at);

-- 文档表索引
CREATE INDEX idx_documents_project_id ON documents(project_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_upload_by ON documents(upload_by);
CREATE INDEX idx_documents_file_type ON documents(file_type);

-- 项目成员表索引
CREATE INDEX idx_project_members_project_id ON project_members(project_id);
CREATE INDEX idx_project_members_user_id ON project_members(user_id);

-- 分析报告表索引
CREATE INDEX idx_analysis_reports_project_id ON analysis_reports(project_id);
CREATE INDEX idx_analysis_reports_status ON analysis_reports(status);
CREATE INDEX idx_analysis_reports_type ON analysis_reports(report_type);

-- 知识库表索引
CREATE INDEX idx_knowledge_bases_project_id ON knowledge_bases(project_id);
CREATE INDEX idx_knowledge_bases_status ON knowledge_bases(status);

-- 系统日志表索引
CREATE INDEX idx_system_logs_user_id ON system_logs(user_id);
CREATE INDEX idx_system_logs_action ON system_logs(action);
CREATE INDEX idx_system_logs_created_at ON system_logs(created_at);
```

## 数据关系说明

1. **用户 -> 项目**: 一对多关系，用户可以创建多个项目
2. **项目 -> 文档**: 一对多关系，项目可以包含多个文档
3. **项目 -> 成员**: 多对多关系，通过project_members表关联
4. **项目 -> 分析报告**: 一对多关系，项目可以有多个分析报告
5. **项目 -> 知识库**: 一对一关系，每个项目对应一个知识库
6. **用户 -> 系统日志**: 一对多关系，记录用户操作历史

## 权限设计

### 角色权限
- **admin**: 系统管理员，可以看到、新建、上传和删除所有角色的项目和文件
- **user**: 普通用户，只能看到、新建、上传和删除自己的项目和文件

### 项目级权限
- **owner**: 项目所有者，拥有项目的所有权限
- **manager**: 项目管理者，可以管理项目成员和设置
- **analyst**: 项目分析师，可以上传文档和生成报告
- **viewer**: 项目查看者，只能查看项目信息
