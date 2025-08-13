"""
文档数据访问对象
"""

from typing import List, Optional
from dao.base_dao import BaseDAO
from db_models import Document, DocumentStatus

class DocumentDAO(BaseDAO):
    """文档数据访问对象"""
    
    def __init__(self):
        super().__init__(Document)
    
    def get_by_project(self, project_id: int) -> List[Document]:
        """获取项目的所有文档"""
        return self.get_by_filter(project_id=project_id)
    
    def get_by_status(self, status: DocumentStatus) -> List[Document]:
        """根据状态获取文档"""
        return self.get_by_filter(status=status)
    
    def get_by_project_and_status(self, project_id: int, status: DocumentStatus) -> List[Document]:
        """根据项目和状态获取文档"""
        return self.get_by_filter(project_id=project_id, status=status)
    
    def create_document(self, project_id: int, name: str, original_filename: str,
                       file_path: str, file_type: str, upload_by: int,
                       file_size: int = 0, mime_type: str = None) -> Optional[Document]:
        """创建文档记录"""
        return self.create(
            project_id=project_id,
            name=name,
            original_filename=original_filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            mime_type=mime_type,
            upload_by=upload_by,
            status=DocumentStatus.UPLOADING
        )
    
    def update_status(self, document_id: int, status: DocumentStatus) -> Optional[Document]:
        """更新文档状态"""
        return self.update(document_id, status=status)
    
    def update_processing_info(self, document_id: int, processed_file_path: str = None,
                             text_content: str = None, rag_document_id: str = None) -> Optional[Document]:
        """更新文档处理信息"""
        update_data = {}
        if processed_file_path:
            update_data['processed_file_path'] = processed_file_path
        if text_content:
            update_data['text_content'] = text_content
        if rag_document_id:
            update_data['rag_document_id'] = rag_document_id
        
        return self.update(document_id, **update_data)
    
    def get_processed_documents(self, project_id: int) -> List[Document]:
        """获取已处理的文档"""
        return self.get_by_project_and_status(project_id, DocumentStatus.COMPLETED)
    
    def count_by_project_and_status(self, project_id: int, status: DocumentStatus) -> int:
        """统计项目中指定状态的文档数量"""
        return self.count(project_id=project_id, status=status)
