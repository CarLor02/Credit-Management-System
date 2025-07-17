"""
知识库服务
负责与RAG API交互，管理知识库的创建、更新和状态
"""

import requests
import logging
import os
from typing import Optional, Dict, Any
from flask import current_app

from database import db
from db_models import Project, User

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    """知识库服务类"""
    
    def __init__(self):
        self.rag_api_base_url = None
        self.rag_api_key = None
        
    def _get_config(self):
        """获取配置"""
        if not self.rag_api_base_url:
            self.rag_api_base_url = current_app.config.get('RAG_API_BASE_URL')
        if not self.rag_api_key:
            self.rag_api_key = current_app.config.get('RAG_API_KEY')
    
    def create_knowledge_base_for_project(self, project_id: int, user_id: int) -> Optional[str]:
        """
        为项目创建知识库
        
        Args:
            project_id: 项目ID
            user_id: 用户ID
            
        Returns:
            创建的知识库dataset_id，失败返回None
        """
        try:
            self._get_config()
            
            # 获取项目和用户信息
            project = Project.query.get(project_id)
            if not project:
                logger.error(f"项目不存在: {project_id}")
                return None
                
            user = User.query.get(user_id)
            if not user:
                logger.error(f"用户不存在: {user_id}")
                return None
            
            # 构造知识库名称：用户名_项目名
            kb_name = f"{user.full_name}_{project.name}"
            
            # 调用RAG API创建知识库
            dataset_id = self._create_dataset_via_api(kb_name)
            if not dataset_id:
                logger.error(f"创建知识库失败: {kb_name}")
                return None
            
            # 保存dataset_id到项目表
            project.dataset_id = dataset_id
            project.knowledge_base_name = kb_name
            db.session.commit()
            
            logger.info(f"成功创建知识库: {kb_name}, dataset_id: {dataset_id}")
            return dataset_id
            
        except Exception as e:
            logger.error(f"创建知识库失败: {e}")
            return None
    
    def _create_dataset_via_api(self, name: str) -> Optional[str]:
        """
        通过API创建数据集
        
        Args:
            name: 数据集名称
            
        Returns:
            数据集ID，失败返回None
        """
        try:
            url = f"{self.rag_api_base_url}/api/v1/datasets"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.rag_api_key}"
            }
            data = {
                "name": name,
                "description": f"知识库：{name}"
            }
            
            logger.info(f"调用RAG API创建数据集: {name}")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") == 0:
                dataset_id = result["data"]["id"]
                logger.info(f"成功创建数据集: {name}, ID: {dataset_id}")
                return dataset_id
            else:
                logger.error(f"创建数据集失败: {result.get('message')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"调用RAG API失败: {e}")
            return None
        except Exception as e:
            logger.error(f"创建数据集异常: {e}")
            return None
    
    def check_if_first_upload(self, project_id: int) -> bool:
        """
        检查是否是项目首次上传文件
        
        Args:
            project_id: 项目ID
            
        Returns:
            是否首次上传
        """
        from db_models import Document, DocumentStatus
        
        # 检查项目是否有已完成的文档
        completed_docs = Document.query.filter_by(
            project_id=project_id,
            status=DocumentStatus.COMPLETED
        ).count()
        
        return completed_docs == 0

    def upload_document_to_knowledge_base(self, project_id: int, document_id: int) -> bool:
        """
        将处理后的文档上传到知识库
        
        Args:
            project_id: 项目ID
            document_id: 文档ID
            
        Returns:
            是否上传成功
        """
        try:
            self._get_config()
            
            # 获取项目信息
            project = Project.query.get(project_id)
            if not project or not project.dataset_id:
                logger.error(f"项目不存在或未创建知识库: {project_id}")
                return False
            
            # 获取文档信息
            from db_models import Document, DocumentStatus
            document = Document.query.get(document_id)
            if not document or not document.processed_file_path:
                logger.error(f"文档不存在或未处理: {document_id}")
                return False
            
            # 检查处理后的文件是否存在
            if not document.processed_file_path or not os.path.exists(document.processed_file_path):
                logger.error(f"处理后的文件不存在: {document.processed_file_path}")
                return False
            
            # 更新状态为上传知识库中
            document.status = DocumentStatus.UPLOADING_TO_KB
            document.progress = 60
            db.session.commit()
            
            # 生成正确的文件名 - 确保是.md扩展名
            base_name = os.path.splitext(document.name)[0]  # 去掉原始扩展名
            md_filename = f"{base_name}.md"
            
            # 上传文件到知识库
            rag_document_id = self._upload_file_to_dataset(project.dataset_id, document.processed_file_path, md_filename)
            if not rag_document_id:
                logger.error(f"上传文件到知识库失败: {md_filename}")
                document.status = DocumentStatus.FAILED
                document.error_message = "上传文件到知识库失败"
                db.session.commit()
                return False
            
            # 更新状态为知识库解析中
            document.status = DocumentStatus.PARSING_KB
            document.progress = 80
            db.session.commit()
            
            # 触发文档解析
            rag_document_id_for_parsing = rag_document_id  # 保存文档ID用于后续状态检查
            success = self._parse_document_in_dataset(project.dataset_id, rag_document_id)
            if success:
                # 解析任务已触发，但不立即设置为完成状态
                # 需要异步检查解析状态
                document.status = DocumentStatus.PARSING_KB
                document.progress = 80
                document.error_message = None
                logger.info(f"成功触发文档解析任务: {md_filename}")
                
                # 启动后台任务检查解析状态
                self._start_parsing_status_check(project.dataset_id, rag_document_id, document.id)
                
            else:
                # 解析任务触发失败
                document.status = DocumentStatus.KB_PARSE_FAILED
                document.progress = 80
                document.error_message = "触发知识库解析失败"
                logger.warning(f"触发文档解析任务失败: {md_filename}")
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"上传文档到知识库失败: {e}")
            # 更新文档状态为失败
            try:
                from db_models import Document, DocumentStatus
                document = Document.query.get(document_id)
                if document:
                    document.status = DocumentStatus.FAILED
                    document.error_message = f"上传知识库异常: {str(e)}"
                    db.session.commit()
            except:
                pass
            return False
    
    def _upload_file_to_dataset(self, dataset_id: str, file_path: str, file_name: str) -> Optional[str]:
        """
        上传文件到数据集
        
        Args:
            dataset_id: 数据集ID
            file_path: 文件路径
            file_name: 文件名
            
        Returns:
            上传后的文档ID，失败返回None
        """
        try:
            url = f"{self.rag_api_base_url}/api/v1/datasets/{dataset_id}/documents"
            headers = {
                "Authorization": f"Bearer {self.rag_api_key}"
            }
            
            # 读取文件内容
            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_name, f, 'text/markdown')
                }
                
                logger.info(f"上传文件到数据集: {file_name}")
                response = requests.post(url, headers=headers, files=files, timeout=60)
                response.raise_for_status()
                
                result = response.json()
                if result.get("code") == 0:
                    document_id = result["data"][0]["id"]
                    logger.info(f"成功上传文件: {file_name}, ID: {document_id}")
                    return document_id
                else:
                    logger.error(f"上传文件失败: {result.get('message')}")
                    return None
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"上传文件请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"上传文件异常: {e}")
            return None
    
    def _start_parsing_status_check(self, dataset_id: str, document_id: str, doc_db_id: int):
        """
        启动后台任务检查解析状态
        
        Args:
            dataset_id: 数据集ID
            document_id: RAG文档ID
            doc_db_id: 数据库中的文档ID
        """
        import threading
        from flask import current_app
        
        # 保存当前应用上下文
        app = current_app._get_current_object()
        
        def check_parsing_status():
            """后台检查解析状态"""
            with app.app_context():
                max_attempts = 60  # 最多检查60次 (10分钟)
                attempt = 0
                
                while attempt < max_attempts:
                    try:
                        # 等待10秒再检查
                        import time
                        time.sleep(5)
                        
                        # 查询解析状态
                        parsing_complete = self._check_document_parsing_status(dataset_id, document_id)
                        
                        if parsing_complete is None:
                            # 查询失败，继续尝试
                            attempt += 1
                            continue
                        elif parsing_complete:
                            # 解析完成，更新数据库状态
                            self._update_document_parsing_complete(doc_db_id)
                            break
                        else:
                            # 解析未完成，继续等待
                            attempt += 1
                            
                    except Exception as e:
                        logger.error(f"检查解析状态异常: {e}")
                        attempt += 1
                
                # 如果达到最大尝试次数仍未完成，标记为失败
                if attempt >= max_attempts:
                    self._update_document_parsing_failed(doc_db_id, "解析超时")
        
        # 启动后台线程
        thread = threading.Thread(target=check_parsing_status)
        thread.daemon = True
        thread.start()
    
    def _check_document_parsing_status(self, dataset_id: str, document_id: str) -> Optional[bool]:
        """
        检查文档解析状态
        
        Args:
            dataset_id: 数据集ID
            document_id: 文档ID
            
        Returns:
            True: 解析完成
            False: 解析未完成
            None: 查询失败
        """
        try:
            # 查询文档列表获取解析状态
            list_url = f"{self.rag_api_base_url}/api/v1/datasets/{dataset_id}/documents"
            headers = {"Authorization": f"Bearer {self.rag_api_key}"}
            params = {"page_size": 100}
            
            response = requests.get(list_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") != 0:
                logger.error(f"查询文档列表失败: {result.get('message')}")
                return None
                
            # 查找目标文档
            docs = result.get("data", {}).get("docs", [])
            target_doc = None
            for doc in docs:
                if doc.get("id") == document_id:
                    target_doc = doc
                    break
            
            if not target_doc:
                logger.error(f"未找到文档: {document_id}")
                return None
            
            # 检查解析进度
            progress = target_doc.get("progress", 0.0)
            run_status = target_doc.get("run", "0")
            
            logger.info(f"文档 {document_id} 解析进度: {progress}, 运行状态: {run_status}")
            
            # 如果进度达到1.0且不在运行状态，认为解析完成
            if progress >= 1.0 and run_status == 'DONE':
                return True
            else:
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"查询解析状态请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"查询解析状态异常: {e}")
            return None
    
    def _update_document_parsing_complete(self, doc_db_id: int):
        """
        更新文档解析完成状态
        
        Args:
            doc_db_id: 数据库中的文档ID
        """
        try:
            from db_models import Document, DocumentStatus
            from flask import current_app
            
            # 在后台线程中需要创建新的应用上下文
            with current_app.app_context():
                # 创建新的数据库会话
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                
                engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
                Session = sessionmaker(bind=engine)
                session = Session()
                
                try:
                    document = session.query(Document).get(doc_db_id)
                    if document:
                        document.status = DocumentStatus.COMPLETED
                        document.progress = 100
                        document.error_message = None
                        session.commit()
                        logger.info(f"文档 {doc_db_id} 解析完成")
                    else:
                        logger.error(f"未找到文档: {doc_db_id}")
                        
                finally:
                    session.close()
                
        except Exception as e:
            logger.error(f"更新文档解析完成状态失败: {e}")
    
    def _update_document_parsing_failed(self, doc_db_id: int, error_message: str):
        """
        更新文档解析失败状态
        
        Args:
            doc_db_id: 数据库中的文档ID
            error_message: 错误消息
        """
        try:
            from db_models import Document, DocumentStatus
            from flask import current_app
            
            # 在后台线程中需要创建新的应用上下文
            with current_app.app_context():
                # 创建新的数据库会话
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                
                engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
                Session = sessionmaker(bind=engine)
                session = Session()
                
                try:
                    document = session.query(Document).get(doc_db_id)
                    if document:
                        document.status = DocumentStatus.KB_PARSE_FAILED
                        document.progress = 80
                        document.error_message = error_message
                        session.commit()
                        logger.warning(f"文档 {doc_db_id} 解析失败: {error_message}")
                    else:
                        logger.error(f"未找到文档: {doc_db_id}")
                        
                finally:
                    session.close()
                
        except Exception as e:
            logger.error(f"更新文档解析失败状态失败: {e}")

    def _parse_document_in_dataset(self, dataset_id: str, document_id: str) -> bool:
        """
        解析数据集中的文档
        
        Args:
            dataset_id: 数据集ID
            document_id: 文档ID
            
        Returns:
            是否成功触发解析
        """
        try:
            url = f"{self.rag_api_base_url}/api/v1/datasets/{dataset_id}/chunks"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.rag_api_key}"
            }
            data = {
                "document_ids": [document_id]
            }
            
            logger.info(f"触发文档解析: {document_id}")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") == 0:
                logger.info(f"成功触发文档解析: {document_id}")
                return True
            else:
                logger.error(f"触发文档解析失败: {result.get('message')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"触发文档解析请求失败: {e}")
            return False
        except Exception as e:
            logger.error(f"触发文档解析异常: {e}")
            return False
# 全局服务实例
knowledge_base_service = KnowledgeBaseService()
