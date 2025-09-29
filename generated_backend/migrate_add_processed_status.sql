-- 数据库迁移脚本：添加 PROCESSED 状态到 documents 表
-- 执行日期: 2025-09-29

USE `credit_db`;

-- 备份当前表结构（可选）
-- CREATE TABLE documents_backup AS SELECT * FROM documents;

-- 修改 documents 表的 status 字段，添加 'PROCESSED' 状态
ALTER TABLE documents 
MODIFY COLUMN status ENUM(
    'UPLOADING', 
    'PROCESSING', 
    'PROCESSED',
    'UPLOADING_TO_KB', 
    'PARSING_KB', 
    'COMPLETED', 
    'FAILED', 
    'KB_PARSE_FAILED'
) NOT NULL DEFAULT 'UPLOADING';

-- 验证修改
DESCRIBE documents;