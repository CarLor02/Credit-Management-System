"""
知识库功能实现总结

## 功能概述
在"文档中心"界面，当项目首次上传文件并解析完成后，系统会自动调用RAGFlow的API创建知识库。

## 实现细节

### 1. 知识库服务 (services/knowledge_base_service.py)
- `KnowledgeBaseService` 类负责与RAGFlow API交互
- `create_knowledge_base_for_project()` 方法创建知识库
- 知识库命名规则：`用户id_项目名称`
- 使用配置文件中的 RAG_API_BASE_URL 和 RAG_API_KEY

### 2. 文档处理器修改 (services/document_processor.py)
- 在文档处理完成后调用 `_check_and_create_knowledge_base()`
- 检查是否为项目的首次上传文档
- 如果是首次上传，则创建知识库
- 支持PDF、Word、Markdown等文件类型

### 3. 触发条件
- 项目首次上传文件
- 文档处理/解析完成
- 状态变更为 DocumentStatus.COMPLETED

### 4. 集成点
- 在 `documents.py` 的文档上传接口中
- 文档处理完成后会自动触发知识库创建

## 配置要求
在 `config.py` 中需要配置：
```python
RAG_API_BASE_URL = 'http://172.16.76.183'
RAG_API_KEY = 'ragflow-U4OWM2Njc2NDVjNTExZjA5NDUzMDI0Mm'
```

## API调用示例
参考 `DEMO/backend.py` 中的实现：
```python
url = f"{RAG_API_BASE_URL}/api/v1/datasets"
headers = {
    "Content-Type": "application/json", 
    "Authorization": f"Bearer {RAG_API_KEY}"
}
data = {
    "name": "用户id_项目名称",
    "description": "知识库：用户id_项目名称",
    "embedding_model": "BAAI/bge-zh-v1.5"
}
```

## 处理流程
1. 用户上传文件到项目
2. 文档开始处理（OCR/解析）
3. 处理完成，状态变为 COMPLETED
4. 检查是否为该项目的首次上传
5. 如果是首次上传，调用RAGFlow API创建知识库
6. 记录日志

## 日志记录
- 创建知识库的过程会记录详细日志
- 成功/失败状态都会记录
- 不影响文档处理的主流程

这个实现确保了项目首次上传文件后，会自动在RAGFlow中创建对应的知识库，便于后续的文档检索和分析。
