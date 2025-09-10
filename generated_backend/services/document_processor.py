"""
文档处理服务
处理已上传的文档，使用外部API进行解析
"""

import os
import sys
import uuid
import threading
import subprocess
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# 导入文档处理库（现在主要通过外部接口处理）
# 保留DOCX_AVAILABLE用于兼容性检查
DOCX_AVAILABLE = True

from flask import current_app
from database import db
from db_models import Document, DocumentStatus

class DocumentProcessor:
    """文档处理器"""
    
    def __init__(self):
        self.processed_folder = 'processed'
        
    def process_document_async(self, document_id: int, app=None):
        """异步处理文档"""
        def process_in_background():
            try:
                # 如果没有传递app实例，尝试获取当前应用实例
                if app is None:
                    application = current_app._get_current_object()
                else:
                    application = app

                with application.app_context():
                    self.process_document(document_id)
            except Exception as e:
                # 使用标准logging而不是current_app.logger
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"后台处理文档失败 (ID: {document_id}): {e}")
                print(f"后台处理文档失败 (ID: {document_id}): {e}")  # 备用日志输出

                # 尝试更新文档状态为失败（如果可能的话）
                try:
                    if app is None:
                        application = current_app._get_current_object()
                    else:
                        application = app

                    with application.app_context():
                        from db_models import Document, DocumentStatus
                        from database import db

                        doc = Document.query.get(document_id)
                        if doc:
                            doc.status = DocumentStatus.FAILED
                            doc.error_message = str(e)
                            db.session.commit()
                            logger.info(f"已将文档 {document_id} 状态设置为失败")
                except Exception as update_error:
                    logger.error(f"更新文档状态失败: {update_error}")

        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()
    
    def process_document(self, document_id: int) -> bool:
        """处理单个文档"""
        try:
            document = Document.query.get(document_id)
            if not document:
                current_app.logger.error(f"文档不存在: {document_id}")
                return False
            
            # 更新状态为处理中，进度为10%
            document.status = DocumentStatus.PROCESSING
            document.processing_started_at = datetime.utcnow()
            document.progress = 10
            db.session.commit()
            
            current_app.logger.info(f"开始处理文档: {document.name}")
            
            # 构建输入和输出路径
            input_file = document.file_path
            if not os.path.exists(input_file):
                current_app.logger.error(f"源文件不存在: {input_file}")
                self._mark_processing_failed(document, "源文件不存在")
                return False
            
            # 创建处理后文件的路径结构，进度为20%
            processed_file_path = self._create_processed_file_path(document)
            document.progress = 20
            db.session.commit()
            
            # 调用文档处理，进度为30%
            document.progress = 30
            db.session.commit()
            
            success = self._call_document_processor(input_file, processed_file_path, document)
            
            if success:
                # 更新文档状态，进度为50%（完成文件处理，准备上传知识库）
                document.processed_file_path = processed_file_path
                document.processed_at = datetime.utcnow()
                document.progress = 50
                db.session.commit()
                
                current_app.logger.info(f"文档处理完成: {document.name}")
                self._check_and_create_knowledge_base(document)
                return True
            else:
                self._mark_processing_failed(document, "文档处理失败")
                return False
                
        except Exception as e:
            current_app.logger.error(f"处理文档失败: {e}")
            if 'document' in locals():
                self._mark_processing_failed(document, str(e))
            return False
    
    def _create_processed_file_path(self, document: Document) -> str:
        """创建处理后文件的路径"""
        # 获取项目的folder_uuid
        project = document.project
        if not project or not project.folder_uuid:
            raise ValueError("项目不存在或缺少folder_uuid")
        
        # 创建processed目录结构：processed/{project_folder_uuid}/{filename}.md
        # processed和uploads应该是同级关系
        project_upload_dir = os.path.dirname(document.file_path)  # 获取uploads/{project_folder_uuid}目录
        uploads_dir = os.path.dirname(project_upload_dir)  # 获取uploads目录
        backend_dir = os.path.dirname(uploads_dir)  # 获取generated_backend目录
        
        processed_dir = os.path.join(
            backend_dir,
            self.processed_folder,
            project.folder_uuid
        )
        
        # 确保目录存在
        os.makedirs(processed_dir, exist_ok=True)
        
        # 获取上传时生成的文件名（带UUID前缀），去掉扩展名后加上.md
        uploaded_filename = os.path.basename(document.file_path)  # 获取带UUID的文件名
        base_name = os.path.splitext(uploaded_filename)[0]  # 去掉扩展名
        processed_filename = f"{base_name}.md"  # 加上.md扩展名
        
        return os.path.join(processed_dir, processed_filename)
    
    def _call_document_processor(self, input_file: str, output_file: str, document: Document) -> bool:
        """调用文档处理器或直接处理特定文件类型"""
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_file)
            os.makedirs(output_dir, exist_ok=True)
            
            # 检测文件类型，进度为40%
            file_extension = Path(input_file).suffix.lower()
            file_type = self._get_file_type(file_extension)
            
            if not file_type:
                current_app.logger.error(f"不支持的文件类型: {file_extension}")
                return False
            
            document.progress = 40
            db.session.commit()
            
            # 对于markdown文件，直接处理；其他文件类型统一调用外部接口
            if file_type == 'markdown':
                return self._process_markdown_direct(input_file, output_file, document)
            else:
                # 其他文件类型统一调用外部接口处理
                return self._process_with_external_api(input_file, output_file, document)
                
        except Exception as e:
            current_app.logger.error(f"调用处理器失败: {e}")
            import traceback
            current_app.logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
    
    def _process_markdown_direct(self, input_file: str, output_file: str, document: Document) -> bool:
        """直接处理markdown文件"""
        try:
            # 进度为50%
            document.progress = 50
            db.session.commit()
            
            # 读取原始md文件内容
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 进度为80%
            document.progress = 80
            db.session.commit()
            
            # 写入到processed目录
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            current_app.logger.info(f"markdown文件直接处理完成: {output_file}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"直接处理markdown文件失败: {e}")
            return False
    

    def _process_with_external_api(self, input_file: str, output_file: str, document: Document) -> bool:
        """使用外部接口处理文件"""
        try:
            # 进度为50%
            document.progress = 50
            db.session.commit()

            # 获取外部接口URL
            api_url = current_app.config.get('DOCUMENT_PROCESS_API_URL')
            if not api_url:
                current_app.logger.error("未配置DOCUMENT_PROCESS_API_URL")
                return False

            current_app.logger.info(f"调用外部接口处理文件: {input_file}")
            current_app.logger.info(f"接口URL: {api_url}")

            # 准备文件上传
            with open(input_file, 'rb') as f:
                files = {'file': (os.path.basename(input_file), f, 'application/octet-stream')}

                # 进度为60%
                document.progress = 60
                db.session.commit()

                # 调用外部接口
                response = requests.post(api_url, files=files, timeout=300)  # 5分钟超时

                # 进度为80%
                document.progress = 80
                db.session.commit()

            # 检查响应
            if response.status_code != 200:
                current_app.logger.error(f"外部接口调用失败，状态码: {response.status_code}")
                current_app.logger.error(f"响应内容: {response.text}")
                return False

            # 解析响应
            try:
                result = response.json()
            except Exception as e:
                current_app.logger.error(f"解析响应JSON失败: {e}")
                current_app.logger.error(f"响应内容: {response.text}")
                return False

            # 检查处理是否成功
            if not result.get('success', False):
                current_app.logger.error(f"外部接口处理失败: {result}")
                return False

            # 获取处理后的内容
            content = result.get('content', '')
            if not content:
                current_app.logger.error("外部接口返回的内容为空")
                return False

            # 进度为90%
            document.progress = 90
            db.session.commit()

            # 写入处理后的内容到输出文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

            # 记录处理信息
            metadata = result.get('metadata', {})
            processing_time = result.get('processing_time', 0)
            current_app.logger.info(f"外部接口处理完成: {output_file}")
            current_app.logger.info(f"文件类型: {metadata.get('file_type', 'unknown')}")
            current_app.logger.info(f"处理时间: {processing_time}秒")

            return True

        except requests.exceptions.Timeout:
            current_app.logger.error("外部接口调用超时")
            return False
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"外部接口调用异常: {e}")
            return False
        except Exception as e:
            current_app.logger.error(f"调用外部接口处理文件失败: {e}")
            import traceback
            current_app.logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False

    def _get_file_type(self, extension: str) -> Optional[str]:
        """根据文件扩展名获取处理类型"""
        extension = extension.lower()
        
        if extension == '.pdf':
            return 'pdf'
        elif extension in ['.xlsx', '.xls', '.csv']:
            return 'excel'
        elif extension in ['.html', '.htm']:
            return 'html'
        elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif']:
            return 'image'
        elif extension in ['.md', '.markdown']:
            return 'markdown'
        elif extension in ['.doc', '.docx']:
            return 'word'
        else:
            return None
    
    def _mark_processing_failed(self, document: Document, error_message: str):
        """标记文档处理失败"""
        try:
            document.status = DocumentStatus.FAILED
            document.progress = 0  # 失败时进度设为0
            db.session.commit()
            current_app.logger.error(f"文档处理失败: {document.filename}, 错误: {error_message}")
        except Exception as e:
            current_app.logger.error(f"更新文档状态失败: {e}")
            db.session.rollback()
    
    def get_processing_progress(self, document_id: int) -> Dict[str, Any]:
        """获取文档处理进度"""
        try:
            document = Document.query.get(document_id)
            if not document:
                return {'error': '文档不存在'}
            
            progress_info = {
                'status': document.status.value,
                'filename': document.filename,
                'processing_started_at': document.processing_started_at.isoformat() if document.processing_started_at else None,
                'processed_at': document.processed_at.isoformat() if document.processed_at else None,
                'processed_file_path': document.processed_file_path,
                'progress_percent': document.progress  # 使用数据库中的实际进度
            }
            
            return progress_info
            
        except Exception as e:
            current_app.logger.error(f"获取处理进度失败: {e}")
            return {'error': '获取进度失败'}
    
    def delete_processed_document(self, document: Document) -> bool:
        """删除处理后的文档文件"""
        try:
            if document.processed_file_path and os.path.exists(document.processed_file_path):
                os.remove(document.processed_file_path)
                current_app.logger.info(f"删除处理后的文档: {document.processed_file_path}")
                return True
            return False
        except Exception as e:
            current_app.logger.error(f"删除处理后的文档失败: {e}")
            return False
    
    def delete_project_documents(self, project) -> bool:
        """删除项目相关的所有文档文件（原始文件和处理后文件）"""
        try:
            success_count = 0
            total_count = 0
            
            # 获取项目的所有文档
            documents = Document.query.filter_by(project_id=project.id).all()
            
            for document in documents:
                total_count += 1
                
                # 删除原始文件
                try:
                    if document.file_path and os.path.exists(document.file_path):
                        os.remove(document.file_path)
                        current_app.logger.info(f"删除原始文件: {document.file_path}")
                except Exception as e:
                    current_app.logger.warning(f"删除原始文件失败: {e}")
                
                # 删除处理后的文件
                try:
                    if document.processed_file_path and os.path.exists(document.processed_file_path):
                        os.remove(document.processed_file_path)
                        current_app.logger.info(f"删除处理后文件: {document.processed_file_path}")
                except Exception as e:
                    current_app.logger.warning(f"删除处理后文件失败: {e}")
                
                success_count += 1
            
            # 删除项目相关的文件夹
            try:
                # 删除uploads中的项目文件夹
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
                project_upload_dir = os.path.join(upload_folder, project.folder_uuid)
                if os.path.exists(project_upload_dir):
                    import shutil
                    shutil.rmtree(project_upload_dir)
                    current_app.logger.info(f"删除项目上传目录: {project_upload_dir}")
                
                # 删除processed中的项目文件夹
                backend_dir = os.path.dirname(upload_folder)
                project_processed_dir = os.path.join(backend_dir, self.processed_folder, project.folder_uuid)
                if os.path.exists(project_processed_dir):
                    import shutil
                    shutil.rmtree(project_processed_dir)
                    current_app.logger.info(f"删除项目处理目录: {project_processed_dir}")
                    
            except Exception as e:
                current_app.logger.warning(f"删除项目文件夹失败: {e}")
            
            current_app.logger.info(f"项目文档删除完成: {success_count}/{total_count}")
            return success_count == total_count
            
        except Exception as e:
            current_app.logger.error(f"删除项目文档失败: {e}")
            return False
    
    def process_markdown_file(self, document_id: int) -> bool:
        """处理markdown文件（直接复制）"""
        try:
            document = Document.query.get(document_id)
            if not document:
                current_app.logger.error(f"文档不存在: {document_id}")
                return False
            
            # 更新状态为处理中，进度为10%
            document.status = DocumentStatus.PROCESSING
            document.processing_started_at = datetime.utcnow()
            document.progress = 10
            db.session.commit()
            
            current_app.logger.info(f"开始处理markdown文件: {document.filename}")
            
            # 构建输入和输出路径
            input_file = document.file_path
            if not os.path.exists(input_file):
                current_app.logger.error(f"源文件不存在: {input_file}")
                self._mark_processing_failed(document, "源文件不存在")
                return False
            
            # 创建处理后文件的路径，进度为30%
            processed_file_path = self._create_processed_file_path(document)
            document.progress = 30
            db.session.commit()
            
            # 直接复制md文件内容到processed目录，进度为70%
            document.progress = 70
            db.session.commit()
            
            # 读取原始md文件内容
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 写入到processed目录
            with open(processed_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 更新文档状态为已完成，进度为100%
            document.status = DocumentStatus.COMPLETED
            document.processed_file_path = processed_file_path
            document.processed_at = datetime.utcnow()
            document.progress = 100
            db.session.commit()
            
            current_app.logger.info(f"markdown文件处理完成: {document.filename}")
            
            # 检查是否需要创建知识库
            self._check_and_create_knowledge_base(document)
            
            return True
                
        except Exception as e:
            current_app.logger.error(f"处理markdown文件失败: {e}")
            if 'document' in locals():
                self._mark_processing_failed(document, str(e))
            return False
    
    def process_word_file(self, document_id: int) -> bool:
        """处理Word文件（doc/docx）- 现在统一使用外部接口"""
        # 直接调用通用的文档处理方法
        return self.process_document(document_id)
    

    
    def _check_and_create_knowledge_base(self, document: Document):
        """检查并创建知识库（当项目没有知识库时自动创建）"""
        try:
            # 导入知识库服务
            from services.knowledge_base_service import knowledge_base_service
            
            project_id = document.project_id
            user_id = document.upload_by
            
            # 获取项目信息
            project = document.project
            if not project:
                current_app.logger.error(f"项目不存在: {project_id}")
                return
            
            # 检查项目是否已有知识库
            if project.dataset_id:
                current_app.logger.info(f"项目 {project_id} 已有知识库 {project.dataset_id}，直接上传文档")
                # 项目已有知识库，直接上传文档
                self._upload_document_to_knowledge_base(document)
                return
            
            # 项目没有知识库，为项目创建知识库
            current_app.logger.info(f"项目 {project_id} 没有知识库，开始创建知识库")
            
            # 创建知识库
            dataset_id = knowledge_base_service.create_knowledge_base_for_project(
                project_id=project_id,
                user_id=user_id
            )
            
            if dataset_id:
                current_app.logger.info(f"成功为项目 {project_id} 创建知识库，dataset_id: {dataset_id}")
                
                # 上传当前文档到知识库
                self._upload_document_to_knowledge_base(document)
            else:
                current_app.logger.error(f"为项目 {project_id} 创建知识库失败")
                
        except Exception as e:
            current_app.logger.error(f"检查和创建知识库失败: {e}")
            # 不影响文档处理的主流程，只记录错误
    
    def _upload_document_to_knowledge_base(self, document: Document):
        """将文档上传到知识库"""
        try:
            from services.knowledge_base_service import knowledge_base_service
            
            # 检查项目是否有知识库
            project = document.project
            if not project or not project.dataset_id:
                current_app.logger.warning(f"项目 {document.project_id} 没有知识库，跳过文档上传")
                return
            
            current_app.logger.info(f"开始上传文档 {document.name} 到知识库 {project.dataset_id}")
            
            # 上传文档到知识库
            success = knowledge_base_service.upload_document_to_knowledge_base(
                project_id=document.project_id,
                document_id=document.id
            )
            
            if success:
                current_app.logger.info(f"成功上传文档 {document.name} 到知识库")
            else:
                current_app.logger.error(f"上传文档 {document.name} 到知识库失败")
                
        except Exception as e:
            current_app.logger.error(f"上传文档到知识库异常: {e}")
            # 不影响文档处理的主流程，只记录错误

# 全局文档处理器实例
document_processor = DocumentProcessor()
