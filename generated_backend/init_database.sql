-- 数据库初始化脚本
-- 根据 db_models.py 和 seed_data.py 生成

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS `credit_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE `credit_db`;

-- 创建用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    avatar_url VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 创建项目表
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    folder_uuid VARCHAR(36) NOT NULL UNIQUE,
    type ENUM('enterprise', 'individual') NOT NULL,
    status ENUM('collecting', 'processing', 'completed') NOT NULL DEFAULT 'collecting',
    description TEXT,
    category VARCHAR(50),
    priority ENUM('low', 'medium', 'high') NOT NULL DEFAULT 'medium',
    score INTEGER DEFAULT 0,
    risk_level ENUM('low', 'medium', 'high') NOT NULL DEFAULT 'low',
    progress INTEGER DEFAULT 0,
    company_info JSON,
    personal_info JSON,

    financial_data JSON,
    dataset_id VARCHAR(100),
    knowledge_base_name VARCHAR(200),
    report_path VARCHAR(500),
    report_status ENUM('not_generated', 'generating', 'generated', 'cancelled') NOT NULL DEFAULT 'not_generated',
    created_by INTEGER NOT NULL,
    assigned_to INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (assigned_to) REFERENCES users(id)
);

-- 创建文档表
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    mime_type VARCHAR(100),
    project_id INTEGER NOT NULL,
    status ENUM('uploading', 'processing', 'uploading_to_kb', 'parsing_kb', 'completed', 'failed', 'kb_parse_failed') NOT NULL DEFAULT 'uploading',
    progress INTEGER DEFAULT 0,
    upload_by INTEGER NOT NULL,
    processing_result TEXT,
    error_message TEXT,
    label ENUM('QICHACHA', 'INTRODUCTION', 'BUSINESS_LICENSE', 'FINANCIAL_STATEMENT', 'BALANCE_SHEET', 'PROFIT_STATEMENT', 'CASH_FLOW', 'ENTERPRISE_CREDIT', 'PERSONAL_CREDIT'),
    processed_file_path VARCHAR(500),
    processing_started_at DATETIME,
    processed_at DATETIME,
    rag_document_id VARCHAR(100),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (upload_by) REFERENCES users(id)
);

-- 创建项目成员表
CREATE TABLE project_members (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role ENUM('owner', 'manager', 'analyst', 'viewer') NOT NULL DEFAULT 'viewer',
    permissions JSON,
    joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_project_user (project_id, user_id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 创建分析报告表
CREATE TABLE analysis_reports (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    report_type ENUM('credit_analysis', 'risk_assessment', 'summary') NOT NULL,
    status ENUM('not_generated', 'generating', 'generated', 'cancelled') NOT NULL DEFAULT 'generating',
    generated_by INTEGER NOT NULL,
    workflow_run_id VARCHAR(100),
    report_metadata JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (generated_by) REFERENCES users(id)
);

-- 创建系统日志表
CREATE TABLE system_logs (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 创建系统设置表
CREATE TABLE system_settings (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    `key` VARCHAR(100) NOT NULL UNIQUE,
    value TEXT,
    description TEXT,
    category VARCHAR(50) DEFAULT 'general',
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 创建仪表板统计数据表
CREATE TABLE dashboard_stats (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    date DATE NOT NULL UNIQUE,
    total_projects INTEGER DEFAULT 0,
    completed_projects INTEGER DEFAULT 0,
    processing_projects INTEGER DEFAULT 0,
    collecting_projects INTEGER DEFAULT 0,
    archived_projects INTEGER DEFAULT 0,
    total_documents INTEGER DEFAULT 0,
    completed_documents INTEGER DEFAULT 0,
    processing_documents INTEGER DEFAULT 0,
    failed_documents INTEGER DEFAULT 0,
    total_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    average_score FLOAT DEFAULT 0.0,
    high_risk_projects INTEGER DEFAULT 0,
    medium_risk_projects INTEGER DEFAULT 0,
    low_risk_projects INTEGER DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 创建活动日志表
CREATE TABLE activity_logs (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    user_id INTEGER,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    activity_metadata JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 创建财务分析表
CREATE TABLE financial_analysis (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id INTEGER NOT NULL,
    total_assets DECIMAL(15, 2),
    annual_revenue DECIMAL(15, 2),
    net_profit DECIMAL(15, 2),
    debt_ratio DECIMAL(5, 2),
    current_ratio DECIMAL(8, 2),
    quick_ratio DECIMAL(8, 2),
    cash_ratio DECIMAL(8, 2),
    gross_profit_margin DECIMAL(5, 2),
    net_profit_margin DECIMAL(5, 2),
    roe DECIMAL(5, 2),
    roa DECIMAL(5, 2),
    inventory_turnover DECIMAL(8, 2),
    receivables_turnover DECIMAL(8, 2),
    total_asset_turnover DECIMAL(8, 2),
    revenue_growth_rate DECIMAL(5, 2),
    profit_growth_rate DECIMAL(5, 2),
    analysis_year INTEGER NOT NULL,
    analysis_quarter INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_project_analysis (project_id, analysis_year, analysis_quarter),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- 创建经营状况表
CREATE TABLE business_status (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id INTEGER NOT NULL,
    business_license_status ENUM('normal', 'expiring', 'expired') DEFAULT 'normal',
    business_license_expiry DATE,
    tax_registration_status ENUM('normal', 'abnormal') DEFAULT 'normal',
    organization_code_status ENUM('normal', 'expiring', 'expired') DEFAULT 'normal',
    legal_violations INTEGER DEFAULT 0,
    tax_compliance_status ENUM('compliant', 'warning', 'violation') DEFAULT 'compliant',
    environmental_compliance ENUM('compliant', 'warning', 'violation') DEFAULT 'compliant',
    labor_compliance ENUM('compliant', 'warning', 'violation') DEFAULT 'compliant',
    market_risk_level ENUM('low', 'medium', 'high') DEFAULT 'low',
    financial_risk_level ENUM('low', 'medium', 'high') DEFAULT 'low',
    operational_risk_level ENUM('low', 'medium', 'high') DEFAULT 'low',
    industry_ranking INTEGER,
    market_share DECIMAL(5, 2),
    competitive_advantage TEXT,
    overall_score INTEGER DEFAULT 0,
    qualification_score INTEGER DEFAULT 0,
    compliance_score INTEGER DEFAULT 0,
    risk_score INTEGER DEFAULT 0,
    risk_factors TEXT,
    improvement_suggestions TEXT,
    evaluation_date DATE NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- 创建项目时间轴表
CREATE TABLE project_timeline (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id INTEGER NOT NULL,
    event_title VARCHAR(200) NOT NULL,
    event_description TEXT,
    event_type ENUM('milestone', 'document', 'analysis', 'review', 'report', 'other') DEFAULT 'other',
    status ENUM('completed', 'in_progress', 'pending', 'cancelled') DEFAULT 'pending',
    priority ENUM('low', 'medium', 'high') DEFAULT 'medium',
    event_date DATE NOT NULL,
    planned_date DATE,
    completed_date DATE,
    related_document_id INTEGER,
    related_user_id INTEGER,
    progress INTEGER DEFAULT 0,
    created_by INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (related_document_id) REFERENCES documents(id),
    FOREIGN KEY (related_user_id) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- 创建统计历史表
CREATE TABLE statistics_history (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    stat_date DATE NOT NULL,
    stat_type ENUM('daily', 'weekly', 'monthly') DEFAULT 'daily',
    total_projects INTEGER DEFAULT 0,
    enterprise_projects INTEGER DEFAULT 0,
    individual_projects INTEGER DEFAULT 0,
    collecting_projects INTEGER DEFAULT 0,
    processing_projects INTEGER DEFAULT 0,
    completed_projects INTEGER DEFAULT 0,
    archived_projects INTEGER DEFAULT 0,
    high_risk_projects INTEGER DEFAULT 0,
    medium_risk_projects INTEGER DEFAULT 0,
    low_risk_projects INTEGER DEFAULT 0,
    average_score DECIMAL(5, 2) DEFAULT 0,
    min_score INTEGER DEFAULT 0,
    max_score INTEGER DEFAULT 0,
    total_documents INTEGER DEFAULT 0,
    completed_documents INTEGER DEFAULT 0,
    processing_documents INTEGER DEFAULT 0,
    failed_documents INTEGER DEFAULT 0,
    total_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    completion_rate DECIMAL(5, 2) DEFAULT 0,
    doc_completion_rate DECIMAL(5, 2) DEFAULT 0,
    new_projects INTEGER DEFAULT 0,
    new_documents INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_stat (stat_date, stat_type)
);

-- 插入种子用户数据
-- 密码: admin - admin123, user1/user2/user3 - user123
INSERT INTO users (username, email, password_hash, phone, role, is_active, last_login) VALUES
('admin', 'admin@example.com', 'pbkdf2:sha256:600000$iu0c0jWvMhEsPP8J$56fa52e76e9537f70fe15d7ee5069dde4cf52ae62a65c6c20e4af4b927785f21', '13800138000', 'admin', TRUE, DATE_SUB(NOW(), INTERVAL 1 DAY)),
('user1', 'user1@example.com', 'pbkdf2:sha256:600000$GizkWjSgyQxr3dyv$4f94bd52e2211fe45056cdae98ba335f397f79b29f5b7fe3efde58332ac79b6c', '13800138001', 'user', TRUE, DATE_SUB(NOW(), INTERVAL 1 DAY)),
('user2', 'user2@example.com', 'pbkdf2:sha256:600000$AD1WKcMIw1f1ChxH$515fa2c9d658e510f9cc39aa1267253523b62004ea7e20b24aba953fcb78c705', '13800138002', 'user', TRUE, DATE_SUB(NOW(), INTERVAL 1 DAY)),
('user3', 'user3@example.com', 'pbkdf2:sha256:600000$pG06uYLbGrUdZcac$0e4a7dcb1eec2195a9a0879c45635fc07222be088931d129bfa2076c6e9947e1', '13800138003', 'user', TRUE, DATE_SUB(NOW(), INTERVAL 1 DAY));

-- 插入系统设置数据
INSERT INTO system_settings (`key`, value, description, category, is_public) VALUES
('system_name', 'Credit Management System', '系统名称', 'general', TRUE),
('version', '1.0.0', '系统版本', 'general', TRUE),
('max_file_size', '10485760', '最大文件上传大小（字节）', 'upload', FALSE),
('allowed_file_types', 'pdf,doc,docx,xls,xlsx,txt,jpg,jpeg,png,bmp', '允许上传的文件类型', 'upload', FALSE),
('report_generation_timeout', '3600', '报告生成超时时间（秒）', 'report', FALSE),
('enable_email_notifications', 'true', '启用邮件通知', 'notification', FALSE),
('default_project_priority', 'medium', '默认项目优先级', 'project', FALSE),
('auto_backup_enabled', 'false', '自动备份功能', 'backup', FALSE);

-- 创建索引优化查询性能
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);

CREATE INDEX idx_projects_created_by ON projects(created_by);
CREATE INDEX idx_projects_assigned_to ON projects(assigned_to);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_type ON projects(type);
CREATE INDEX idx_projects_risk_level ON projects(risk_level);
CREATE INDEX idx_projects_folder_uuid ON projects(folder_uuid);
CREATE INDEX idx_projects_created_at ON projects(created_at);

CREATE INDEX idx_documents_project_id ON documents(project_id);
CREATE INDEX idx_documents_upload_by ON documents(upload_by);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_label ON documents(label);
CREATE INDEX idx_documents_created_at ON documents(created_at);

CREATE INDEX idx_project_members_project_id ON project_members(project_id);
CREATE INDEX idx_project_members_user_id ON project_members(user_id);
CREATE INDEX idx_project_members_role ON project_members(role);

CREATE INDEX idx_analysis_reports_project_id ON analysis_reports(project_id);
CREATE INDEX idx_analysis_reports_generated_by ON analysis_reports(generated_by);
CREATE INDEX idx_analysis_reports_status ON analysis_reports(status);
CREATE INDEX idx_analysis_reports_report_type ON analysis_reports(report_type);

CREATE INDEX idx_system_logs_user_id ON system_logs(user_id);
CREATE INDEX idx_system_logs_action ON system_logs(action);
CREATE INDEX idx_system_logs_resource_type ON system_logs(resource_type);
CREATE INDEX idx_system_logs_created_at ON system_logs(created_at);

CREATE INDEX idx_dashboard_stats_date ON dashboard_stats(date);

CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_type ON activity_logs(type);
CREATE INDEX idx_activity_logs_resource_type ON activity_logs(resource_type);
CREATE INDEX idx_activity_logs_created_at ON activity_logs(created_at);

CREATE INDEX idx_financial_analysis_project_id ON financial_analysis(project_id);
CREATE INDEX idx_financial_analysis_year ON financial_analysis(analysis_year);

CREATE INDEX idx_business_status_project_id ON business_status(project_id);
CREATE INDEX idx_business_status_evaluation_date ON business_status(evaluation_date);

CREATE INDEX idx_project_timeline_project_id ON project_timeline(project_id);
CREATE INDEX idx_project_timeline_event_type ON project_timeline(event_type);
CREATE INDEX idx_project_timeline_status ON project_timeline(status);
CREATE INDEX idx_project_timeline_event_date ON project_timeline(event_date);

CREATE INDEX idx_statistics_history_stat_date ON statistics_history(stat_date);
CREATE INDEX idx_statistics_history_stat_type ON statistics_history(stat_type);