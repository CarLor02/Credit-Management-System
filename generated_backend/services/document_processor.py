"""
文档处理服务
处理已上传的文档，使用OCR工具进行解析
"""

import os
import sys
import uuid
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from flask import current_app
from database import db
from db_models import Document, DocumentStatus

class DocumentProcessor:
    """文档处理器"""
    
    def __init__(self):
        self.ocr_path = self._get_ocr_path()
        self.processed_folder = 'processed'
        
    def _get_ocr_path(self) -> str:
        """获取OCR代码路径"""
        # 假设OCR文件夹在项目根目录下
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        return os.path.join(project_root, 'OCR')
    
    def process_document_async(self, document_id: int):
        """异步处理文档"""
        def process_in_background():
            try:
                with current_app.app_context():
                    self.process_document(document_id)
            except Exception as e:
                current_app.logger.error(f"后台处理文档失败: {e}")
        
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
            
            current_app.logger.info(f"开始处理文档: {document.filename}")
            
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
            
            # 调用OCR处理，进度为30%
            document.progress = 30
            db.session.commit()
            
            success = self._call_ocr_processor(input_file, processed_file_path, document)
            
            if success:
                # 更新文档状态为已完成，进度为100%
                document.status = DocumentStatus.COMPLETED
                document.processed_file_path = processed_file_path
                document.processed_at = datetime.utcnow()
                document.progress = 100
                db.session.commit()
                
                current_app.logger.info(f"文档处理完成: {document.filename}")
                return True
            else:
                self._mark_processing_failed(document, "OCR处理失败")
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
    
    def _call_ocr_processor(self, input_file: str, output_file: str, document: Document) -> bool:
        """调用OCR处理器"""
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
            
            # 构建OCR处理命令
            ocr_script = os.path.join(self.ocr_path, 'process_docs.py')
            input_dir = os.path.dirname(input_file)
            
            # 使用绝对路径
            input_dir = os.path.abspath(input_dir)
            temp_output_dir = os.path.abspath(os.path.join(output_dir, f"temp_{uuid.uuid4().hex[:8]}"))
            
            # 使用单独的输出目录避免冲突
            
            cmd = [
                sys.executable, ocr_script,
                '--input', input_dir,
                '--output', temp_output_dir,
                '--type', file_type,
                '--no-recursive',
                '--no-preserve-structure'
            ]
            
            # 添加API密钥（如果需要）
            api_key = os.environ.get('YUNWU_API_KEY')
            if api_key:
                cmd.extend(['--api-key', api_key])
            
            current_app.logger.info(f"执行OCR命令: {' '.join(cmd)}")
            
            # 开始OCR处理，进度为50%
            document.progress = 50
            db.session.commit()
            
            # 执行OCR处理
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                cwd=self.ocr_path
            )
            
            # OCR处理完成，进度为80%
            document.progress = 80
            db.session.commit()
            
            current_app.logger.info(f"OCR命令退出码: {result.returncode}")
            if result.stdout:
                current_app.logger.info(f"OCR标准输出: {result.stdout}")
            if result.stderr:
                current_app.logger.error(f"OCR错误输出: {result.stderr}")
            
            if result.returncode == 0:
                # OCR成功，查找生成的文件并移动到目标位置
                processed_files = list(Path(temp_output_dir).rglob('*.md'))
                
                current_app.logger.info(f"在{temp_output_dir}中找到{len(processed_files)}个处理后的文件")
                
                if processed_files:
                    # 查找与当前文档匹配的文件
                    target_file = None
                    base_filename = os.path.splitext(document.filename)[0]
                    
                    # 首先尝试找到与文档名称匹配的文件
                    for file in processed_files:
                        if base_filename in file.stem:
                            target_file = file
                            break
                    
                    # 如果没有找到匹配的文件，取第一个
                    if target_file is None:
                        target_file = processed_files[0]
                    
                    current_app.logger.info(f"移动文件: {target_file} -> {output_file}")
                    
                    # 移动文件到最终位置，进度为90%
                    document.progress = 90
                    db.session.commit()
                    
                    # 移动文件到最终位置
                    import shutil
                    shutil.move(str(target_file), output_file)
                    
                    # 清理临时目录
                    shutil.rmtree(temp_output_dir, ignore_errors=True)
                    
                    current_app.logger.info(f"OCR处理成功，输出文件: {output_file}")
                    return True
                else:
                    current_app.logger.error("OCR处理未生成任何文件")
                    return False
            else:
                current_app.logger.error(f"OCR处理失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            current_app.logger.error("OCR处理超时")
            return False
        except Exception as e:
            current_app.logger.error(f"调用OCR处理器失败: {e}")
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
        """处理markdown文件（无需OCR，直接复制）"""
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
            return True
                
        except Exception as e:
            current_app.logger.error(f"处理markdown文件失败: {e}")
            if 'document' in locals():
                self._mark_processing_failed(document, str(e))
            return False

# 全局文档处理器实例
document_processor = DocumentProcessor()
