"""
报告生成API
"""

import os
import time
import json
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
from flask import request, jsonify, current_app, send_file
from websocket_handlers import (
    broadcast_workflow_event,
    broadcast_workflow_content,
    broadcast_workflow_complete,
    broadcast_workflow_error
)

# 导入数据库模型
from db_models import Project, AnalysisReport, ReportType, ReportStatus, ProjectStatus

# 导入PDF转换服务
from services.pdf_converter import convert_report_to_pdf, is_pdf_conversion_available
from services.md_to_pdf_converter import MarkdownToPDFConverter
from services.markdown_postprocessor import process_markdown_content
from database import db

# 导入认证装饰器
from api.auth import token_required

# 全局变量：跟踪正在进行的工作流
import threading
active_workflows = {}  # {project_id: {'workflow_run_id': str, 'stop_flag': bool, 'thread': Thread}}
workflow_lock = threading.Lock()

# 导入配置（如果需要的话）
# from config import Config

# 全局变量，用于存储每个工作流的事件和内容
workflow_events = {}  # 格式: {workflow_run_id: {'events': [], 'content': '', 'metadata': {}}}

# 导入Project模型以获取folder_uuid
from db_models import Project, Document, DocumentStatus

def calculate_project_progress(project_id):
    """
    根据项目文档完成情况计算项目进度
    项目进度计算规则：
    - 没有文档：0%
    - 部分文档完成：按完成文档比例计算，最高75%
    - 所有文档完成：75%（未生成报告的情况下）
    - 报告生成完成：100%
    """
    try:
        # 获取项目的所有文档
        documents = Document.query.filter_by(project_id=project_id).all()
        
        if not documents:
            # 没有文档，进度为0
            return 0
        
        # 计算完成的文档数量
        completed_documents = [doc for doc in documents if doc.status == DocumentStatus.COMPLETED]
        
        if len(completed_documents) == 0:
            # 没有完成的文档，进度为0
            return 0
        elif len(completed_documents) == len(documents):
            # 所有文档都完成了，但没有生成报告，进度为75%
            return 75
        else:
            # 部分文档完成，按比例计算，最高不超过75%
            completion_ratio = len(completed_documents) / len(documents)
            return min(int(completion_ratio * 75), 75)
            
    except Exception as e:
        current_app.logger.error(f"计算项目进度失败: {e}")
        return 0

# 添加删除非项目文件的函数
def delete_non_project_files(dataset_id, project_id):
    """删除知识库中所有非项目文件"""
    try:
        # 获取项目信息
        project = Project.query.get(project_id)
        if not project:
            current_app.logger.error(f"项目 {project_id} 不存在")
            return False
        
        # 从数据库中查询该项目的所有文件id
        from db_models import Document
        project_documents = Document.query.filter_by(project_id=project_id).all()
        
        # 构建项目文件id集合，包括rag_document_id
        project_file_ids = set()
        for doc in project_documents:
            # 添加文档的id字段
            if doc.rag_document_id:
                project_file_ids.add(doc.rag_document_id)
        
        current_app.logger.info(f"项目 {project_id} 共有 {len(project_documents)} 个文档，文件id集合大小: {len(project_file_ids)}")
        
        # 获取知识库中的所有文档
        RAG_API_BASE_URL = current_app.config.get('RAG_API_BASE_URL')
        RAG_API_KEY = current_app.config.get('RAG_API_KEY')
        
        list_url = f"{RAG_API_BASE_URL}/api/v1/datasets/{dataset_id}/documents"
        headers = {"Authorization": f"Bearer {RAG_API_KEY}"}
        params = {"page_size": 100}
        
        list_res = requests.get(list_url, headers=headers, params=params, timeout=30)
        list_res.raise_for_status()
        list_res_json = list_res.json()
        
        if list_res_json.get("code") != 0:
            raise Exception(f"查询文档列表失败: {list_res_json.get('message')}")
        
        docs = list_res_json.get("data", {}).get("docs", [])
        
        # 筛选出非项目文件并删除
        deleted_count = 0
        for doc in docs:
            doc_id = doc.get("id")
            doc_name = doc.get("name", "")
            
            # 检查文件名是否在项目文件名集合中
            if doc_id not in project_file_ids:
                # 删除非项目文件
                delete_url = f"{RAG_API_BASE_URL}/api/v1/datasets/{dataset_id}/documents"
                delete_data = {"ids": [doc_id]}
                delete_res = requests.delete(delete_url, headers=headers, json=delete_data, timeout=30)
                
                if delete_res.status_code == 200:
                    delete_res_json = delete_res.json()
                    if delete_res_json.get("code") == 0:
                        current_app.logger.info(f"成功删除非项目文件: {doc_name} (ID: {doc_id})")
                        deleted_count += 1
                    else:
                        current_app.logger.error(f"删除非项目文件失败: {doc_name} (ID: {doc_id}), 错误: {delete_res_json.get('message')}")
                else:
                    current_app.logger.error(f"删除非项目文件请求失败: {doc_name} (ID: {doc_id}), 状态码: {delete_res.status_code}")
        
        current_app.logger.info(f"共删除 {deleted_count} 个非项目文件")
        return True
    
    except Exception as e:
        current_app.logger.error(f"删除非项目文件时发生错误: {e}")
        return False


def check_parsing_status(dataset_id, project_id=None):
    """检查文档解析状态"""
    try:
        # 如果提供了project_id，先删除非项目文件
        if project_id:
            delete_non_project_files(dataset_id, project_id)
        
        # 真实检查：获取文档列表并检查解析状态
        RAG_API_BASE_URL = current_app.config.get('RAG_API_BASE_URL')
        RAG_API_KEY = current_app.config.get('RAG_API_KEY')

        list_url = f"{RAG_API_BASE_URL}/api/v1/datasets/{dataset_id}/documents"
        headers = {"Authorization": f"Bearer {RAG_API_KEY}"}
        params = {"page_size": 100}

        list_res = requests.get(list_url, headers=headers, params=params, timeout=30)
        list_res.raise_for_status()
        list_res_json = list_res.json()

        if list_res_json.get("code") != 0:
            raise Exception(f"查询文档列表失败: {list_res_json.get('message')}")

        docs = list_res_json.get("data", {}).get("docs", [])
        return all(doc.get("progress", 0.0) >= 1.0 for doc in docs)

    except Exception as e:
        current_app.logger.error(f"检查解析状态失败: {e}")
        return False


def register_report_routes(app):
    """注册报告相关路由"""

    @app.route('/api/generate_report_stream', methods=['POST'])
    def generate_report_stream():
        """
        生成报告的流式API接口 - 实时返回流式数据
        """
        from flask import Response
        import json

        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "error": "缺少请求数据"}), 400

            # 获取参数
            dataset_id = data.get('dataset_id')
            company_name = data.get('company_name')
            knowledge_name = data.get('knowledge_name')
            project_id = data.get('project_id')

            # 验证必要参数
            if not company_name:
                return jsonify({"success": False, "error": "缺少必要参数: company_name"}), 400

            if not dataset_id:
                return jsonify({"success": False, "error": "缺少必要参数: dataset_id"}), 400

            # 如果没有提供knowledge_name，使用company_name作为默认值
            if not knowledge_name:
                knowledge_name = company_name

            # 检查项目是否存在和报告状态
            if project_id:
                project = Project.query.get(project_id)
                if not project:
                    return jsonify({"success": False, "error": "项目不存在"}), 404
                
                # 检查报告状态，如果正在生成则检查是否真的有活跃工作流
                if project.report_status == ReportStatus.GENERATING:
                    # 检查是否真的有活跃的工作流
                    with workflow_lock:
                        if project_id in active_workflows:
                            return jsonify({"success": False, "error": "报告正在生成中，请稍后再试"}), 400
                        else:
                            # 没有活跃工作流，重置状态
                            current_app.logger.info(f"项目 {project_id} 状态为GENERATING但没有活跃工作流，重置状态")
                            project.report_status = ReportStatus.NOT_GENERATED
                            try:
                                db.session.commit()
                                current_app.logger.info("已重置项目状态为NOT_GENERATED")
                            except Exception as e:
                                current_app.logger.error(f"重置项目状态失败: {str(e)}")
                                db.session.rollback()

                # 检查报告状态和文件是否存在
                if project.report_status == ReportStatus.GENERATED:
                    # 获取项目根目录绝对路径
                    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                    full_path = os.path.join(base_dir, project.report_path) if project.report_path else None
                    current_app.logger.info(f"检查报告文件是否存在(完整路径): {full_path}")
                    
                    # 如果报告文件不存在，更新状态为未生成
                    if not full_path or not os.path.exists(full_path):
                        current_app.logger.info(f"报告文件不存在于: {full_path}，更新状态为未生成")
                        project.report_status = ReportStatus.NOT_GENERATED
                        project.report_path = None
                        try:
                            db.session.commit()
                            current_app.logger.info("数据库状态更新成功")
                        except Exception as e:
                            current_app.logger.error(f"数据库提交失败: {str(e)}")
                            db.session.rollback()
                    else:
                        current_app.logger.info("报告文件存在，不允许重复生成")
                        return jsonify({"success": False, "error": "报告已生成，若需重新生成，请先删除旧报告"}), 400

            # 获取当前应用实例，确保在生成器中有应用上下文
            app = current_app._get_current_object()

            def generate_stream():
                """生成器函数，实时返回流式数据"""
                with app.app_context():
                    try:
                        # 发送开始事件
                        yield f"data: {json.dumps({'event': 'start', 'message': '开始生成报告'}, ensure_ascii=False)}\n\n"

                        # 对于测试数据，使用模拟流式输出
                        if dataset_id and dataset_id.startswith('test_'):
                            # 模拟流式输出
                            import time
                            workflow_run_id = f"test_workflow_{int(time.time())}"

                            # 发送多个内容块来模拟流式输出
                            content_chunks = [
                                f"# {company_name} 征信分析报告\n\n",
                                "## 公司基本信息\n",
                                f"- 公司名称：{company_name}\n",
                                f"- 知识库：{knowledge_name}\n",
                                f"- 生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n\n",
                                "## 征信评估\n",
                                "这是一个测试报告，用于验证流式输出功能。\n\n",
                                "### 主要发现\n",
                                "1. 流式输出功能正常\n",
                                "2. WebSocket广播工作正常\n",
                                "3. 前端实时显示正常\n\n",
                                "### 建议\n",
                                "继续完善系统功能，确保生产环境的稳定性。\n"
                            ]

                            report_content = ""
                            for i, chunk in enumerate(content_chunks):
                                report_content += chunk
                                # 发送内容块事件
                                yield f"data: {json.dumps({'event': 'content', 'content': chunk, 'workflow_run_id': workflow_run_id}, ensure_ascii=False)}\n\n"
                                # 模拟处理时间
                                time.sleep(0.5)

                            events = ['workflow_started', 'content_generated', 'workflow_finished']
                        else:
                            # 调用真实的流式报告生成API
                            report_content, workflow_run_id, events = call_report_generation_api_streaming(company_name, knowledge_name, project_id)

                        # 发送完成事件
                        yield f"data: {json.dumps({'event': 'complete', 'workflow_run_id': workflow_run_id, 'content': report_content}, ensure_ascii=False)}\n\n"

                        # 发送结束标记
                        yield "data: [DONE]\n\n"

                    except Exception as e:
                        # 发送错误事件
                        yield f"data: {json.dumps({'event': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
                        yield "data: [DONE]\n\n"

            return Response(
                generate_stream(),
                mimetype='text/plain',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                }
            )

        except Exception as e:
            current_app.logger.error(f"流式生成报告失败: {str(e)}")
            return jsonify({"success": False, "error": f"流式生成报告失败: {str(e)}"}), 500

    @app.route('/api/stop_report_generation', methods=['POST', 'OPTIONS'])
    @token_required
    def stop_report_generation():
        """
        停止正在生成的报告
        """
        try:
            data = request.get_json()
            project_id = data.get('project_id')
            if not project_id:
                return jsonify({"success": False, "error": "缺少project_id参数"}), 400

            # 获取项目
            project = Project.query.get(project_id)
            if not project:
                return jsonify({"success": False, "error": "项目不存在"}), 404

            # 获取task_id并调用Dify停止接口
            task_id = None
            with workflow_lock:
                if project_id in active_workflows:
                    active_workflows[project_id]['stop_flag'] = True
                    task_id = active_workflows[project_id].get('task_id')
                    current_app.logger.info(f"设置项目 {project_id} 的停止标志，task_id: {task_id}")
                else:
                    current_app.logger.warning(f"项目 {project_id} 没有活跃的工作流")

            # 如果有task_id，调用Dify的停止接口
            if task_id:
                try:
                    stop_success = call_dify_stop_api(task_id)
                    if stop_success:
                        current_app.logger.info(f"成功调用Dify停止接口，task_id: {task_id}")
                    else:
                        current_app.logger.warning(f"调用Dify停止接口失败，task_id: {task_id}")
                except Exception as stop_error:
                    current_app.logger.error(f"调用Dify停止接口异常: {stop_error}")

            # 更新项目报告状态为已取消（使用NOT_GENERATED作为取消状态）
            project.report_status = ReportStatus.NOT_GENERATED
            db.session.commit()

            # 广播停止事件
            project_room_id = f"project_{project_id}"
            socketio = current_app.socketio
            broadcast_workflow_event(socketio, project_room_id, 'generation_cancelled', {
                'project_id': project_id,
                'message': '报告生成已取消'
            })

            return jsonify({
                "success": True,
                "message": "报告生成已停止"
            })

        except Exception as e:
            current_app.logger.error(f"停止报告生成失败: {str(e)}")
            return jsonify({"success": False, "error": f"停止报告生成失败: {str(e)}"}), 500

    @app.route('/api/projects/<int:project_id>/generation_status', methods=['GET'])
    @token_required
    def get_generation_status(project_id):
        """
        检查项目的报告生成状态
        """
        try:
            # 检查项目是否存在
            project = Project.query.get(project_id)
            if not project:
                return jsonify({"success": False, "error": "项目不存在"}), 404

            # 检查是否有活跃的工作流
            with workflow_lock:
                is_generating = project_id in active_workflows
                workflow_info = active_workflows.get(project_id, {})

            return jsonify({
                "success": True,
                "data": {
                    "isGenerating": is_generating,
                    "reportStatus": project.report_status.value if project.report_status else "not_generated",
                    "workflowInfo": workflow_info if is_generating else None
                }
            })

        except Exception as e:
            current_app.logger.error(f"获取生成状态失败: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/generate_report', methods=['POST'])
    def generate_report():
        """
        生成报告的API接口 - 立即返回项目ID，异步执行报告生成
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "error": "缺少请求数据"}), 400

            # 获取参数
            dataset_id = data.get('dataset_id')
            company_name = data.get('company_name')
            knowledge_name = data.get('knowledge_name')
            project_id = data.get('project_id')

            # 简化日志：只在调试模式下打印请求详情
            if current_app.config.get('DEBUG', False):
                current_app.logger.info(f"收到生成报告请求，参数: {data}")
                current_app.logger.info(f"解析参数: dataset_id={dataset_id}, company_name={company_name}, knowledge_name={knowledge_name}, project_id={project_id}")
            else:
                current_app.logger.info(f"收到生成报告请求 - 公司: {company_name}, 项目ID: {project_id}")

            # 验证必要参数
            if not company_name:
                return jsonify({"success": False, "error": "缺少必要参数: company_name"}), 400

            if not project_id:
                return jsonify({"success": False, "error": "缺少必要参数: project_id"}), 400

            # dataset_id是可选的，如果没有提供，可以使用默认值或从项目中获取
            if not dataset_id:
                current_app.logger.info(f"未提供dataset_id，将从项目 {project_id} 中获取")
                # 这里可以从项目中获取dataset_id，或者使用默认值

            # 检查项目是否存在
            project = Project.query.get(project_id)
            if not project:
                return jsonify({"success": False, "error": "项目不存在"}), 404

            # 如果没有提供dataset_id，从项目中获取
            if not dataset_id:
                dataset_id = project.dataset_id
                current_app.logger.info(f"从项目中获取dataset_id: {dataset_id}")

            # 如果没有提供knowledge_name，使用项目的知识库名称
            if not knowledge_name:
                knowledge_name = project.knowledge_base_name or company_name
                current_app.logger.info(f"使用项目知识库名称: {knowledge_name}")

            # 检查报告状态，如果正在生成则检查是否真的有活跃工作流
            if project.report_status == ReportStatus.GENERATING:
                # 检查是否真的有活跃的工作流
                with workflow_lock:
                    if project_id in active_workflows:
                        return jsonify({"success": False, "error": "报告正在生成中，请稍后再试"}), 400
                    else:
                        # 没有活跃工作流，重置状态
                        current_app.logger.info(f"项目 {project_id} 状态为GENERATING但没有活跃工作流，重置状态")
                        project.report_status = ReportStatus.NOT_GENERATED
                        try:
                            db.session.commit()
                            current_app.logger.info("已重置项目状态为NOT_GENERATED")
                        except Exception as e:
                            current_app.logger.error(f"重置项目状态失败: {str(e)}")
                            db.session.rollback()

            # 检查报告状态和文件是否存在
            if project.report_status == ReportStatus.GENERATED:
                # 获取项目根目录绝对路径
                base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                full_path = os.path.join(base_dir, project.report_path) if project.report_path else None
                current_app.logger.info(f"检查报告文件是否存在(完整路径): {full_path}")
                
                # 如果报告文件不存在，更新状态为未生成
                if not full_path or not os.path.exists(full_path):
                    current_app.logger.info(f"报告文件不存在于: {full_path}，更新状态为未生成")
                    project.report_status = ReportStatus.NOT_GENERATED
                    project.report_path = None
                    try:
                        db.session.commit()
                        current_app.logger.info("数据库状态更新成功")
                    except Exception as e:
                        current_app.logger.error(f"数据库提交失败: {str(e)}")
                        db.session.rollback()
                else:
                    current_app.logger.info("报告文件存在，不允许重复生成")
                    return jsonify({"success": False, "error": "报告已生成，若需重新生成，请先删除旧报告"}), 400
            
            # 如果没有提供knowledge_name，使用company_name作为默认值
            if not knowledge_name:
                knowledge_name = company_name

            current_app.logger.info(f"开始生成报告 - 公司: {company_name}, 知识库: {knowledge_name}, 项目ID: {project_id}")

            # 在启动任务前检查解析状态（仅在非测试环境下）
            if dataset_id and not dataset_id.startswith('test_'):
                parsing_complete = check_parsing_status(dataset_id, project_id)
                if not parsing_complete:
                    current_app.logger.error(f"项目 {project_id} 文档解析尚未完成")
                    return jsonify({"success": False, "error": "文档解析尚未完成，请等待解析完成后再生成报告"}), 400

            # 更新项目状态为处理中，报告状态为正在生成
            project.status = ProjectStatus.PROCESSING
            project.report_status = ReportStatus.GENERATING
            db.session.commit()

            # 项目WebSocket房间ID
            project_room_id = f"project_{project_id}"

            # 获取当前应用实例
            app = current_app._get_current_object()

            # 异步执行报告生成
            def async_generate_report():
                """异步执行报告生成的函数"""
                # 在异步线程中设置应用上下文
                with app.app_context():
                    try:
                        # 通过WebSocket广播开始事件
                        socketio = current_app.socketio
                        broadcast_workflow_event(socketio, project_room_id, 'generation_started', {
                            'company_name': company_name,
                            'knowledge_name': knowledge_name,
                            'project_id': project_id,
                            'message': '开始生成报告...'
                        })

                        # 执行实际的报告生成逻辑
                        _execute_report_generation(dataset_id, company_name, knowledge_name, project_id, project_room_id)

                    except Exception as e:
                        current_app.logger.error(f"异步报告生成失败: {str(e)}")
                        # 广播错误事件
                        try:
                            socketio = current_app.socketio
                            broadcast_workflow_error(socketio, project_room_id, f"报告生成失败: {str(e)}", project_id)
                        except Exception as ws_error:
                            current_app.logger.error(f"WebSocket错误广播失败: {ws_error}")

            # 启动异步任务
            import threading
            thread = threading.Thread(target=async_generate_report)
            thread.daemon = True
            thread.start()

            # 立即返回，让前端连接WebSocket
            return jsonify({
                "success": True,
                "message": "报告生成已开始",
                "project_id": project_id,
                "websocket_room": project_room_id,
                "status": "generating"
            })

        except Exception as e:
            current_app.logger.error(f"生成报告失败: {str(e)}")
            return jsonify({"success": False, "error": f"生成报告失败: {str(e)}"}), 500

    def _execute_report_generation(dataset_id, company_name, knowledge_name, project_id, project_room_id):
        """执行实际的报告生成逻辑"""
        try:
            socketio = current_app.socketio

            # 注：解析状态检查已在主函数中完成，这里不再重复检查

            # 对于测试数据，返回模拟响应
            if dataset_id and dataset_id.startswith('test_'):
                # 模拟工作流ID和内容
                mock_workflow_id = f"workflow_{int(time.time())}"
                mock_content = f"""# {company_name} 征信分析报告

## 公司基本信息
- 公司名称：{company_name}
- 知识库：{knowledge_name}
- 生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}

## 征信评估
这是一个测试报告，用于验证系统功能。

### 主要发现
1. 测试数据处理正常
2. API接口工作正常
3. 报告生成流程完整

### 建议
继续完善系统功能，确保生产环境的稳定性。
"""

                # 不使用假的模拟事件，保持空列表
                mock_events = []

                # 存储到全局变量
                workflow_events[mock_workflow_id] = {
                    'events': mock_events,
                    'content': mock_content,
                    'metadata': {'test': True, 'company': company_name},
                    'timestamp': time.time(),
                    'company_name': company_name
                }

                # 对测试内容进行markdown后处理
                try:
                    current_app.logger.info("开始对测试报告内容进行后处理...")
                    processed_mock_content = process_markdown_content(mock_content)
                    current_app.logger.info("测试报告内容后处理完成")
                    mock_content = processed_mock_content
                except Exception as e:
                    current_app.logger.error(f"测试报告内容后处理失败: {e}")
                    # 即使后处理失败，仍然使用原始内容

                # 保存报告到本地文件
                file_path = save_report_to_file(company_name, mock_content, project_id)
                current_app.logger.info(f"测试报告已保存到: {file_path}")

                # 保存报告路径到数据库
                if project_id:
                    try:
                        project = Project.query.get(project_id)
                        if project:
                            project.report_path = file_path
                            db.session.commit()
                            current_app.logger.info(f"报告路径已保存到数据库: {file_path}")
                    except Exception as db_error:
                        current_app.logger.error(f"保存报告路径到数据库失败: {db_error}")

                # 通过WebSocket广播测试报告完成
                broadcast_workflow_complete(socketio, project_room_id, mock_content, project_id)
                return

            # 真实的流式调用报告生成API
            try:
                # 注册活跃工作流
                with workflow_lock:
                    active_workflows[project_id] = {
                        'workflow_run_id': f"workflow_{int(time.time())}",
                        'stop_flag': False
                    }

                # 调用流式报告生成API，传递项目房间ID用于WebSocket广播
                report_content, workflow_run_id, events = call_report_generation_api_streaming(company_name, knowledge_name, project_id, project_room_id)

                # 保存报告到本地文件
                file_path = save_report_to_file(company_name, report_content, project_id)

                # 保存报告路径到数据库
                if project_id:
                    try:
                        project = Project.query.get(project_id)
                        if project:
                            project.report_path = file_path
                            db.session.commit()
                            current_app.logger.info(f"报告路径已保存到数据库: {file_path}")
                    except Exception as db_error:
                        current_app.logger.error(f"保存报告路径到数据库失败: {db_error}")

                current_app.logger.info(f"报告生成成功，已保存到: {file_path}")

                # 更新项目报告状态为已生成
                project = Project.query.get(project_id)
                if project:
                    project.report_status = ReportStatus.GENERATED
                    project.report_path = file_path
                    # 报告生成完成，更新项目状态和进度
                    project.status = ProjectStatus.COMPLETED
                    project.progress = 100
                    db.session.commit()

                # 通过WebSocket广播报告完成
                broadcast_workflow_complete(socketio, project_room_id, report_content)

                # 清理活跃工作流
                with workflow_lock:
                    if project_id in active_workflows:
                        del active_workflows[project_id]

            except Exception as api_error:
                current_app.logger.error(f"调用外部API失败: {str(api_error)}")

                # 清理活跃工作流
                with workflow_lock:
                    if project_id in active_workflows:
                        del active_workflows[project_id]

                # 通过WebSocket广播错误事件
                try:
                    socketio = current_app.socketio
                    # 这里我们没有workflow_run_id，所以使用一个临时ID
                    temp_workflow_id = f"error_{int(time.time())}"
                    broadcast_workflow_error(socketio, temp_workflow_id, f"调用外部API失败: {str(api_error)}")
                except Exception as ws_error:
                    current_app.logger.error(f"WebSocket错误广播失败: {ws_error}")

                raise Exception(f"调用外部API失败: {str(api_error)}")

        except Exception as e:
            current_app.logger.error(f"生成报告失败: {str(e)}")

            # 重置项目报告状态为未生成
            try:
                project = Project.query.get(project_id)
                if project:
                    project.report_status = ReportStatus.NOT_GENERATED
                    db.session.commit()
            except Exception as db_error:
                current_app.logger.error(f"重置报告状态失败: {str(db_error)}")

            # 通过WebSocket广播错误
            broadcast_workflow_error(socketio, project_room_id, f"生成报告失败: {str(e)}")



    @app.route('/api/projects/<int:project_id>/report', methods=['GET'])
    def get_project_report(project_id):
        """
        获取项目的报告内容
        """
        try:
            # 使用新的数据库会话查询，避免连接问题
            project = db.session.get(Project, project_id)
            if not project:
                return jsonify({
                    "success": False,
                    "error": "项目不存在"
                }), 404

            # 获取项目名称（在检查报告之前先获取，避免后续数据库连接问题）
            company_name = project.name

            # 如果报告路径为空或None，返回友好提示
            if not project.report_path or project.report_path.strip() == "":
                return jsonify({
                    "success": False,
                    "error": "该项目尚未生成报告",
                    "has_report": False,
                    "company_name": company_name
                }), 404  # 使用404状态码，表示资源不存在

            # 检查文件是否存在
            if not os.path.exists(project.report_path):
                # 文件不存在，清空数据库中的路径
                try:
                    project.report_path = None
                    project.report_status = ReportStatus.NOT_GENERATED
                    db.session.commit()
                    current_app.logger.warning(f"报告文件不存在，已清空数据库路径: 项目ID {project_id}")
                except Exception as db_error:
                    current_app.logger.error(f"更新数据库失败: {db_error}")
                    db.session.rollback()

                return jsonify({
                    "success": False,
                    "error": "该项目尚未生成报告",
                    "has_report": False,
                    "company_name": company_name
                }), 404  # 使用404状态码

            # 读取报告内容
            try:
                with open(project.report_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查内容是否为空
                if not content or content.strip() == "":
                    return jsonify({
                        "success": False,
                        "error": "该项目尚未生成报告",
                        "has_report": False,
                        "company_name": company_name
                    }), 404

                # 对内容进行后处理，修复表格等格式问题
                try:
                    processed_content = process_markdown_content(content)
                    current_app.logger.info("报告内容后处理完成")
                except Exception as process_error:
                    current_app.logger.warning(f"报告内容后处理失败，使用原内容: {process_error}")
                    processed_content = content

                return jsonify({
                    "success": True,
                    "content": processed_content,
                    "file_path": project.report_path,
                    "company_name": company_name,
                    "has_report": True
                })
            except Exception as read_error:
                current_app.logger.error(f"读取报告文件失败: {read_error}")
                return jsonify({
                    "success": False,
                    "error": "该项目尚未生成报告",
                    "has_report": False,
                    "company_name": company_name
                }), 404

        except Exception as e:
            current_app.logger.error(f"获取项目报告失败: {str(e)}")
            # 对于数据库连接问题，也返回友好的提示
            if "result object does not return rows" in str(e).lower() or "closed automatically" in str(e).lower():
                return jsonify({
                    "success": False,
                    "error": "该项目尚未生成报告",
                    "has_report": False
                }), 404
            else:
                return jsonify({
                    "success": False,
                    "error": "获取报告时发生错误，请稍后重试",
                    "has_report": False
                }), 500

    @app.route('/api/projects/<int:project_id>/report', methods=['DELETE'])
    def delete_project_report(project_id):
        """
        删除项目的报告文件和相关数据
        """
        try:
            # 使用新的数据库会话查询，避免连接问题
            project = db.session.get(Project, project_id)
            if not project:
                return jsonify({
                    "success": False,
                    "error": "项目不存在"
                }), 404

            current_app.logger.info(f"开始删除项目 {project_id} 的报告")

            # 保存报告路径用于删除文件
            report_path = project.report_path

            # 删除报告文件
            if report_path and os.path.exists(report_path):
                try:
                    os.remove(report_path)
                    current_app.logger.info(f"已删除报告文件: {report_path}")
                except Exception as file_error:
                    current_app.logger.error(f"删除报告文件失败: {file_error}")
                    # 继续执行，不因为文件删除失败而中断

            # 清空数据库中的报告路径，并重置项目状态和进度
            try:
                project.report_status = ReportStatus.NOT_GENERATED
                project.report_path = None
                
                # 重置项目状态为COLLECTING
                project.status = ProjectStatus.COLLECTING
                
                # 重新计算项目进度（基于文档完成情况）
                project_progress = calculate_project_progress(project_id)
                project.progress = project_progress
                
                db.session.commit()
                current_app.logger.info(f"已清空项目 {project_id} 的报告路径，重置状态为COLLECTING，进度为{project_progress}%")
            except Exception as db_error:
                current_app.logger.error(f"更新数据库失败: {db_error}")
                db.session.rollback()
                return jsonify({
                    "success": False,
                    "error": "删除报告时数据库更新失败"
                }), 500

            return jsonify({
                "success": True,
                "message": "报告删除成功"
            })

        except Exception as e:
            current_app.logger.error(f"删除项目报告失败: {str(e)}")
            db.session.rollback()  # 确保回滚事务
            return jsonify({
                "success": False,
                "error": f"删除项目报告失败: {str(e)}"
            }), 500

    @app.route('/api/projects/<int:project_id>/report/download-pdf', methods=['GET'])
    def download_project_report_pdf(project_id):
        """
        下载项目报告的PDF版本
        """
        try:
            # 检查PDF转换功能是否可用
            if not is_pdf_conversion_available():
                return jsonify({
                    "success": False,
                    "error": "PDF转换功能不可用，请联系管理员"
                }), 500

            project = Project.query.get(project_id)
            if not project:
                return jsonify({
                    "success": False,
                    "error": "项目不存在"
                }), 404

            # 检查报告是否存在
            if not project.report_path or project.report_path.strip() == "":
                return jsonify({
                    "success": False,
                    "error": "该项目尚未生成报告"
                }), 404

            # 检查报告文件是否存在
            if not os.path.exists(project.report_path):
                return jsonify({
                    "success": False,
                    "error": "报告文件不存在"
                }), 404

            # 读取Markdown报告内容
            try:
                with open(project.report_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()

                if not md_content or md_content.strip() == "":
                    return jsonify({
                        "success": False,
                        "error": "报告内容为空"
                    }), 404

            except Exception as read_error:
                current_app.logger.error(f"读取报告文件失败: {read_error}")
                return jsonify({
                    "success": False,
                    "error": "读取报告文件失败"
                }), 500

            # 转换为PDF
            current_app.logger.info(f"开始将项目 {project_id} 的报告转换为PDF")

            # 对Markdown内容进行后处理
            try:
                processed_md_content = process_markdown_content(md_content)
                current_app.logger.info("PDF转换前的Markdown后处理完成")
            except Exception as process_error:
                current_app.logger.warning(f"Markdown后处理失败，使用原内容: {process_error}")
                processed_md_content = md_content

            success, message, pdf_path = convert_report_to_pdf(processed_md_content, project.name, project.report_path)

            if not success or not pdf_path:
                current_app.logger.error(f"PDF转换失败: {message}")
                return jsonify({
                    "success": False,
                    "error": f"PDF转换失败: {message}"
                }), 500

            try:
                # 生成下载文件名
                safe_company_name = "".join(c for c in project.name if c.isalnum() or c in (' ', '-', '_')).strip()
                if not safe_company_name:
                    safe_company_name = "征信报告"

                download_filename = f"{safe_company_name}_征信报告.pdf"

                current_app.logger.info(f"PDF转换成功，开始下载: {pdf_path}")

                # 发送文件并在发送后清理临时文件
                def cleanup_after_send():
                    """发送完成后清理临时文件"""
                    try:
                        if os.path.exists(pdf_path):
                            os.unlink(pdf_path)
                            current_app.logger.info(f"已清理临时PDF文件: {pdf_path}")
                    except Exception as cleanup_error:
                        current_app.logger.warning(f"清理临时PDF文件失败: {cleanup_error}")

                # 使用Flask的send_file发送PDF文件
                response = send_file(
                    pdf_path,
                    as_attachment=True,
                    download_name=download_filename,
                    mimetype='application/pdf'
                )

                # 注册清理函数（在响应发送后执行）
                @response.call_on_close
                def cleanup_temp_file():
                    cleanup_after_send()

                return response

            except Exception as send_error:
                current_app.logger.error(f"发送PDF文件失败: {send_error}")
                # 清理临时文件
                try:
                    if pdf_path and os.path.exists(pdf_path):
                        os.unlink(pdf_path)
                except:
                    pass
                return jsonify({
                    "success": False,
                    "error": "发送PDF文件失败"
                }), 500

        except Exception as e:
            current_app.logger.error(f"下载PDF报告失败: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"下载PDF报告失败: {str(e)}"
            }), 500

    @app.route('/api/projects/<int:project_id>/report/html', methods=['GET'])
    @token_required
    def get_project_report_html(project_id):
        """
        获取项目报告的HTML版本
        """
        try:
            # 使用新的数据库会话查询，避免连接问题
            project = db.session.get(Project, project_id)
            if not project:
                return jsonify({
                    "success": False,
                    "error": "项目不存在"
                }), 404

            # 检查报告是否存在
            if not project.report_path or project.report_path.strip() == "":
                return jsonify({
                    "success": False,
                    "error": "该项目尚未生成报告"
                }), 404

            # 检查报告文件是否存在
            if not os.path.exists(project.report_path):
                # 文件不存在，清空数据库中的路径
                try:
                    project.report_path = None
                    project.report_status = ReportStatus.NOT_GENERATED
                    db.session.commit()
                    current_app.logger.warning(f"报告文件不存在，已清空数据库路径: 项目ID {project_id}")
                except Exception as db_error:
                    current_app.logger.error(f"更新数据库失败: {db_error}")
                    db.session.rollback()

                return jsonify({
                    "success": False,
                    "error": "该项目尚未生成报告"
                }), 404

            # 读取Markdown报告内容
            try:
                with open(project.report_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()

                if not md_content or md_content.strip() == "":
                    return jsonify({
                        "success": False,
                        "error": "该项目尚未生成报告"
                    }), 404

            except Exception as read_error:
                current_app.logger.error(f"读取报告文件失败: {read_error}")
                return jsonify({
                    "success": False,
                    "error": "该项目尚未生成报告"
                }), 404

            # 转换为HTML
            try:
                # 对Markdown内容进行后处理
                try:
                    processed_md_content = process_markdown_content(md_content)
                    current_app.logger.info("HTML转换前的Markdown后处理完成")
                except Exception as process_error:
                    current_app.logger.warning(f"Markdown后处理失败，使用原内容: {process_error}")
                    processed_md_content = md_content

                converter = MarkdownToPDFConverter()
                html_content = converter.convert_markdown_to_html(processed_md_content, project.report_path)

                return jsonify({
                    "success": True,
                    "data": {
                        "html_content": html_content,
                        "company_name": project.name,
                        "file_path": project.report_path
                    }
                })

            except Exception as convert_error:
                current_app.logger.error(f"Markdown转HTML失败: {convert_error}")
                return jsonify({
                    "success": False,
                    "error": f"Markdown转HTML失败: {str(convert_error)}"
                }), 500

        except Exception as e:
            current_app.logger.error(f"获取HTML报告失败: {e}")
            # 对于数据库连接问题，也返回友好的提示
            if "result object does not return rows" in str(e).lower() or "closed automatically" in str(e).lower():
                return jsonify({
                    "success": False,
                    "error": "该项目尚未生成报告"
                }), 404
            else:
                return jsonify({
                    "success": False,
                    "error": "获取报告时发生错误，请稍后重试"
                }), 500

    @app.route('/api/projects/<int:project_id>/report/download-html', methods=['GET'])
    @token_required
    def download_project_report_html(project_id):
        """
        下载项目报告的HTML版本
        """
        try:
            project = Project.query.get(project_id)
            if not project:
                return jsonify({
                    "success": False,
                    "error": "项目不存在"
                }), 404

            # 检查报告是否存在
            if not project.report_path or project.report_path.strip() == "":
                return jsonify({
                    "success": False,
                    "error": "该项目尚未生成报告"
                }), 404

            # 检查报告文件是否存在
            if not os.path.exists(project.report_path):
                return jsonify({
                    "success": False,
                    "error": "报告文件不存在"
                }), 404

            # 读取Markdown报告内容
            try:
                with open(project.report_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()

                if not md_content or md_content.strip() == "":
                    return jsonify({
                        "success": False,
                        "error": "报告内容为空"
                    }), 404

            except Exception as read_error:
                current_app.logger.error(f"读取报告文件失败: {read_error}")
                return jsonify({
                    "success": False,
                    "error": "读取报告文件失败"
                }), 500

            # 转换为HTML
            try:
                # 对Markdown内容进行后处理
                try:
                    processed_md_content = process_markdown_content(md_content)
                    current_app.logger.info("HTML下载前的Markdown后处理完成")
                except Exception as process_error:
                    current_app.logger.warning(f"Markdown后处理失败，使用原内容: {process_error}")
                    processed_md_content = md_content

                converter = MarkdownToPDFConverter()
                html_content = converter.convert_markdown_to_html(processed_md_content, project.report_path)

                # 创建HTML文件的响应
                from flask import Response

                # 设置文件名，使用URL编码处理中文
                import urllib.parse
                filename = f"{project.name}_征信报告.html"
                encoded_filename = urllib.parse.quote(filename.encode('utf-8'))

                response = Response(
                    html_content,
                    mimetype='text/html',
                    headers={
                        'Content-Disposition': f'attachment; filename*=UTF-8\'\'{encoded_filename}',
                        'Content-Type': 'text/html; charset=utf-8'
                    }
                )

                current_app.logger.info(f"HTML报告下载成功: 项目 {project_id}")
                return response

            except Exception as convert_error:
                current_app.logger.error(f"Markdown转HTML失败: {convert_error}")
                return jsonify({
                    "success": False,
                    "error": f"Markdown转HTML失败: {str(convert_error)}"
                }), 500

        except Exception as e:
            current_app.logger.error(f"下载HTML报告失败: {e}")
            return jsonify({
                "success": False,
                "error": f"下载HTML报告失败: {str(e)}"
            }), 500

def call_report_generation_api_streaming(company_name, knowledge_name, project_id=None, project_room_id=None):
    """调用报告生成API - 流式模式"""
    try:
        # 新API调用
        report_api_url = current_app.config.get('REPORT_API_URL', 'http://172.16.18.157:18080/v1/chat-messages')
        api_key = current_app.config.get('REPORT_API_KEY', 'app-c8cKydhESsFxtG7QZvZkR5YU')

        current_app.logger.info(f"调用报告生成API (流式): {report_api_url}")
        # 简化日志：只在调试模式下打印详细信息
        if current_app.config.get('DEBUG', False):
            current_app.logger.info(f"使用公司名称: {company_name}, 知识库名称: {knowledge_name}")

        # 构建请求数据 - 使用streaming模式
        request_data = {
            "query": "生成报告",
            "inputs": {
                "company": company_name,
                "knowledge_name": knowledge_name
            },
            "response_mode": "streaming",
            "user": f"user-{project_id}" if project_id else "user-anonymous",
            "conversation_id": ""
        }

        # 简化日志：只在调试模式下打印请求数据
        if current_app.config.get('DEBUG', False):
            current_app.logger.info(f"请求数据: {request_data}")

        response = requests.post(
            report_api_url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json=request_data,
            stream=True,  # 启用流式响应
            timeout=1200  # 10分钟超时
        )

        # 检查HTTP状态码
        if response.status_code != 200:
            error_msg = f"API请求失败，状态码: {response.status_code}"
            try:
                # 尝试读取错误响应
                error_response = response.text
                current_app.logger.error(f"API错误响应: {error_response}")

                # 检查是否是token超限错误
                if "token count exceed" in error_response.lower() or "token" in error_response.lower():
                    error_msg = "请求的内容过长，超出了API的token限制。请尝试减少输入内容或分批处理。"
                elif "quota" in error_response.lower():
                    error_msg = "API配额已用完，请稍后重试或联系管理员。"
                else:
                    error_msg = f"API请求失败: {error_response}"
            except:
                pass
            raise Exception(error_msg)

        # 使用解析方法处理流式响应，传递项目房间ID用于WebSocket广播
        workflow_run_id, full_content, metadata, events, task_id = parse_dify_streaming_response(response, company_name, project_id, project_room_id)

        # 简化日志：只在调试模式下打印详细信息
        if current_app.config.get('DEBUG', False):
            current_app.logger.info(f"流式响应解析完成，workflow_run_id: {workflow_run_id}, task_id: {task_id}")
            current_app.logger.info(f"提取到的事件数量: {len(events)}")
        current_app.logger.info(f"内容长度: {len(full_content) if full_content is not None else 0}")

        # 存储流式数据到全局变量，供前端查询
        if workflow_run_id:
            workflow_events[workflow_run_id] = {
                'events': events,
                'content': full_content,  # 这里已经是处理后的内容
                'metadata': metadata,
                'timestamp': time.time(),
                'company_name': company_name,
                'task_id': task_id  # 保存task_id
            }

        return full_content, workflow_run_id, events

    except requests.exceptions.Timeout:
        raise Exception("报告生成请求超时，请稍后重试")
    except requests.exceptions.ConnectionError:
        raise Exception("无法连接到报告生成服务，请检查网络连接")
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        # 检查是否是token相关错误
        if "token count exceed" in error_msg.lower() or "token" in error_msg.lower():
            error_msg = "请求的内容过长，超出了API的token限制。请尝试减少输入内容或分批处理。"
        elif "quota" in error_msg.lower():
            error_msg = "API配额已用完，请稍后重试或联系管理员。"
        raise Exception(f"报告生成请求失败: {error_msg}")
    except Exception as e:
        error_msg = str(e)
        current_app.logger.error(f"调用流式报告生成API失败: {error_msg}")
        # 检查是否是token相关错误
        if "token count exceed" in error_msg.lower() or "token" in error_msg.lower():
            error_msg = "请求的内容过长，超出了API的token限制。请尝试减少输入内容或分批处理。"
        elif "quota" in error_msg.lower():
            error_msg = "API配额已用完，请稍后重试或联系管理员。"
        raise Exception(f"调用流式报告生成API失败: {error_msg}")


def call_report_generation_api(company_name, knowledge_name, project_id=None):
    """调用报告生成API - 阻塞模式（保持向后兼容）"""
    try:
        # 新API调用
        report_api_url = current_app.config.get('REPORT_API_URL', 'http://172.16.76.203/v1/chat-messages')
        api_key = current_app.config.get('REPORT_API_KEY', 'app-c8cKydhESsFxtG7QZvZkR5YU')

        current_app.logger.info(f"调用报告生成API: {report_api_url}")
        current_app.logger.info(f"使用公司名称: {company_name}, 知识库名称: {knowledge_name}")

        # 构建请求数据
        request_data = {
            "query": "生成报告",
            "inputs": {
                "company": company_name,
                "knowledge_name": knowledge_name
            },
            "response_mode": "streaming",
            "user": f"user-{project_id}" if project_id else "user-anonymous",
            "conversation_id": ""
        }

        current_app.logger.info(f"请求数据: {request_data}")

        response = requests.post(
            report_api_url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json=request_data,
            timeout=1200  # 10分钟超时
        )

        # 检查HTTP状态码
        if response.status_code != 200:
            error_msg = f"API请求失败，状态码: {response.status_code}"
            try:
                # 尝试读取错误响应
                error_response = response.text
                current_app.logger.error(f"API错误响应: {error_response}")

                # 检查是否是token超限错误
                if "token count exceed" in error_response.lower() or "token" in error_response.lower():
                    error_msg = "请求的内容过长，超出了API的token限制。请尝试减少输入内容或分批处理。"
                elif "quota" in error_response.lower():
                    error_msg = "API配额已用完，请稍后重试或联系管理员。"
                else:
                    error_msg = f"API请求失败: {error_response}"
            except:
                pass
            raise Exception(error_msg)

        report_response = response.json()

        status = report_response["data"]["status"]
        current_app.logger.info(f"报告API响应状态: {status}")

        if status != "succeeded":
            error_text = report_response["data"].get("error", "未知错误")
            current_app.logger.error(f"报告API错误响应: {error_text}")

            # 检查是否是token相关错误
            if "token count exceed" in error_text.lower() or "token" in error_text.lower():
                error_text = "请求的内容过长，超出了API的token限制。请尝试减少输入内容或分批处理。"
            elif "quota" in error_text.lower():
                error_text = "API配额已用完，请稍后重试或联系管理员。"

            raise Exception(f'生成报告失败，状态: {status}, 错误: {error_text}')

        full_content = report_response["data"]["outputs"]["text"]
        workflow_run_id = report_response.get("workflow_run_id", "")

        return full_content, workflow_run_id

    except requests.exceptions.Timeout:
        raise Exception("报告生成请求超时，请稍后重试")
    except requests.exceptions.ConnectionError:
        raise Exception("无法连接到报告生成服务，请检查网络连接")
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        # 检查是否是token相关错误
        if "token count exceed" in error_msg.lower() or "token" in error_msg.lower():
            error_msg = "请求的内容过长，超出了API的token限制。请尝试减少输入内容或分批处理。"
        elif "quota" in error_msg.lower():
            error_msg = "API配额已用完，请稍后重试或联系管理员。"
        raise Exception(f"报告生成请求失败: {error_msg}")
    except Exception as e:
        error_msg = str(e)
        current_app.logger.error(f"调用报告生成API失败: {error_msg}")
        # 检查是否是token相关错误
        if "token count exceed" in error_msg.lower() or "token" in error_msg.lower():
            error_msg = "请求的内容过长，超出了API的token限制。请尝试减少输入内容或分批处理。"
        elif "quota" in error_msg.lower():
            error_msg = "API配额已用完，请稍后重试或联系管理员。"
        raise Exception(f"调用报告生成API失败: {error_msg}")





def parse_dify_streaming_response(response, company_name="", project_id=None, project_room_id=None):
    """
    解析 Dify 流式响应，实时存储事件到数据库

    Args:
        response: requests 的流式响应对象
        company_name: 公司名称
        project_id: 项目ID

    Returns:
        tuple: (workflow_run_id, full_content, metadata, events, task_id)
    """
    workflow_run_id = f"workflow_{int(time.time())}"  # 新接口没有workflow_run_id， ourselves generate one
    full_content = ""
    metadata = {}
    events = []
    sequence_number = 0
    task_id = None  # 用于保存Dify的task_id

    print("开始解析流式响应...")

    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue

        # 检查停止标志
        with workflow_lock:
            if project_id in active_workflows and active_workflows[project_id].get('stop_flag', False):
                print(f"检测到停止标志，终止项目 {project_id} 的流式处理")
                break

        # 解析 SSE 格式数据
        line_str = line.decode('utf-8') if isinstance(line, bytes) else line
        if line_str.startswith('data: '):
            data_str = line_str[6:]  # 移除 'data: ' 前缀

            # 检查是否是结束标记
            if data_str.strip() == '[DONE]':
                # 简化日志：只在调试模式下打印结束标记
                if current_app.config.get('DEBUG', False):
                    print("收到结束标记 [DONE]")
                break

            try:
                # 解析 JSON 数据
                data = json.loads(data_str)
                # 简化日志：只在调试模式下打印完整JSON数据
                if current_app.config.get('DEBUG', False):
                    print(f"解析的 JSON 数据: {json.dumps(data, ensure_ascii=False)[:500]}...")

                # 🔧 修复：改进task_id提取逻辑，确保能正确获取
                # 提取task_id（如果存在且尚未获取）
                if 'task_id' in data:
                    current_task_id = data['task_id']
                    # 如果是第一次获取task_id，或者task_id发生变化，则更新
                    if task_id is None or task_id != current_task_id:
                        task_id = current_task_id
                        print(f"🔑 提取到task_id: {task_id}")
                        # 保存task_id到活跃工作流中
                        with workflow_lock:
                            if project_id in active_workflows:
                                active_workflows[project_id]['task_id'] = task_id
                                print(f"✅ 已保存task_id到项目 {project_id}")
                            else:
                                print(f"⚠️ 项目 {project_id} 不在活跃工作流中")

                # 提取生成的内容
                content_chunk = None
                if 'answer' in data:
                    content_chunk = data['answer']
                elif 'message' in data:
                    content_chunk = data['message']

                # 如果找到内容块，累积到完整内容并广播
                # 注意：不使用strip()检查，因为空格和换行符也是重要的格式信息
                if content_chunk is not None and content_chunk != "":
                    # 累积内容
                    full_content += content_chunk
                    # 简化日志：每累积1000个字符才打印一次长度
                    # 简化日志：只在调试模式下打印累积内容信息
                    if current_app.config.get('DEBUG', False):
                        if len(full_content) % 1000 < len(content_chunk):
                            print(f"累积内容，当前总长度: {len(full_content)}")
                        print(f"内容块详情: {repr(content_chunk[:100])}")

                    # 通过WebSocket广播内容到项目房间
                    try:
                        socketio = current_app.socketio
                        if project_room_id:
                            broadcast_workflow_content(socketio, project_room_id, content_chunk)
                            # 简化日志：只在调试模式下打印广播详情
                            if current_app.config.get('DEBUG', False):
                                print(f"已广播内容块到房间 {project_room_id}: {repr(content_chunk[:50])}")
                    except Exception as e:
                        # 简化日志：只在调试模式下打印WebSocket广播失败详情
                        if current_app.config.get('DEBUG', False):
                            print(f"WebSocket内容广播失败: {e}")

                # 提取事件信息
                if 'event' in data:
                    event_type = data['event']
                    # 简化日志：只在调试模式下打印事件提取信息
                    if current_app.config.get('DEBUG', False):
                        print(f"提取到事件: {event_type}")

                    # 调试：只在调试模式下打印节点事件的详细信息
                    if event_type in ['node_started', 'node_finished'] and current_app.config.get('DEBUG', False):
                        print(f"📊 节点事件详情: {json.dumps(data, ensure_ascii=False, indent=2)}")
                        if 'data' in data:
                            print(f"📊 节点数据: title={data['data'].get('title')}, node_id={data['data'].get('node_id')}")

                    # 映射事件类型到我们系统的事件
                    mapped_event = {
                        'message': 'content_generated',
                        'message_end': 'workflow_finished',
                        'error': 'workflow_error',
                        'node_started': 'node_started',
                        'node_finished': 'node_finished',
                        'parallel_branch_started': 'parallel_branch_started',
                        'parallel_branch_finished': 'parallel_branch_finished'
                    }.get(event_type, event_type)

                    # 简化日志：只在调试模式下打印事件广播信息
                    if current_app.config.get('DEBUG', False):
                        print(f"📤 广播事件: {mapped_event} 到房间: {project_room_id}")

                    events.append(mapped_event)
                    sequence_number += 1

                    # 通过WebSocket广播事件到项目房间
                    try:
                        socketio = current_app.socketio
                        if project_room_id:
                            broadcast_workflow_event(socketio, project_room_id, mapped_event, data)
                    except Exception as e:
                        # 简化日志：只在调试模式下打印WebSocket事件广播失败详情
                        if current_app.config.get('DEBUG', False):
                            print(f"WebSocket事件广播失败: {e}")

                # 提取元数据
                if 'metadata' in data:
                    metadata.update(data['metadata'])
                    # 简化日志：只在调试模式下打印元数据信息
                    if current_app.config.get('DEBUG', False):
                        print(f"提取到元数据: {json.dumps(data['metadata'], ensure_ascii=False)[:100]}...")

            except json.JSONDecodeError as e:
                # 简化日志：只在调试模式下打印JSON解析错误详情
                if current_app.config.get('DEBUG', False):
                    print(f"JSON 解析错误: {e}, 原始数据: {data_str}")
                continue

    # 流式解析完成，广播完成事件到项目房间
    try:
        socketio = current_app.socketio
        if project_room_id:
            broadcast_workflow_complete(socketio, project_room_id, full_content, project_id)
            # 简化日志：只在调试模式下打印广播详情
            if current_app.config.get('DEBUG', False):
                print(f"已广播完成事件到房间 {project_room_id}，最终内容长度: {len(full_content)}")
    except Exception as e:
        # 简化日志：只在调试模式下打印WebSocket完成事件广播失败详情
        if current_app.config.get('DEBUG', False):
            print(f"WebSocket完成事件广播失败: {e}")

    # 清理活跃工作流（无论是正常完成还是被停止）
    with workflow_lock:
        if project_id in active_workflows:
            del active_workflows[project_id]
            # 简化日志：只在调试模式下打印清理信息
            if current_app.config.get('DEBUG', False):
                print(f"已清理项目 {project_id} 的活跃工作流")

    # 对最终内容进行markdown后处理
    if full_content:
        try:
            current_app.logger.info("开始对流式报告内容进行后处理...")
            processed_content = process_markdown_content(full_content)
            current_app.logger.info("流式报告内容后处理完成")
            full_content = processed_content
        except Exception as e:
            current_app.logger.error(f"流式报告内容后处理失败: {e}")
            # 即使后处理失败，仍然返回原始内容

    # 简化日志：只在调试模式下打印详细解析信息
    if current_app.config.get('DEBUG', False):
        print(f"流式解析完成 - workflow_run_id: {workflow_run_id}, task_id: {task_id}, 事件数: {len(events)}, 内容长度: {len(full_content)}")
    else:
        print(f"流式解析完成 - 内容长度: {len(full_content)}")
    
    return workflow_run_id, full_content, metadata, events, task_id


def save_report_to_file(company_name, content, project_id=None):
    """保存报告内容到本地文件"""
    try:
        # 对内容进行后处理，修复表格等格式问题
        current_app.logger.info("开始对报告内容进行后处理...")
        processed_content = process_markdown_content(content)
        current_app.logger.info("报告内容后处理完成")

        # 如果有项目ID，按项目组织文件结构
        if project_id:
            output_dir = os.path.join("output", str(project_id), "reports")
        else:
            output_dir = "output"

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 创建文件名：征信分析报告-时间戳.md
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"征信分析报告-{timestamp}.md"
        file_path = os.path.join(output_dir, filename)

        # 写入处理后的内容
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(processed_content)

        current_app.logger.info(f"报告已保存到文件: {file_path}")
        return file_path

    except Exception as e:
        current_app.logger.error(f"保存报告文件失败: {e}")
        raise Exception(f"保存报告文件失败: {str(e)}")


def call_dify_stop_api(task_id):
    """
    调用Dify的停止接口

    Args:
        task_id: Dify返回的任务ID

    Returns:
        bool: 是否成功停止
    """
    try:
        # 从配置中获取Dify API信息
        from config import Config

        # 🔧 修复：使用与报告生成API相同的配置
        # 构建停止接口URL - 使用与生成API相同的配置
        dify_base_url = current_app.config.get('REPORT_API_URL', 'http://115.190.121.59/v1/chat-messages')
        # 从完整URL中提取基础URL
        if '/v1/chat-messages' in dify_base_url:
            base_url = dify_base_url.replace('/v1/chat-messages', '')
        else:
            base_url = dify_base_url
        stop_url = f"{base_url}/v1/chat-messages/{task_id}/stop"

        # 获取API密钥 - 使用与生成API相同的配置
        api_key = current_app.config.get('REPORT_API_KEY', '')
        if not api_key:
            current_app.logger.error("未配置REPORT_API_KEY")
            return False

        # 构建请求头
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # 构建请求体
        payload = {
            "user": "system-stop"
        }

        current_app.logger.info(f"调用Dify停止接口: {stop_url}")

        # 发送停止请求
        response = requests.post(
            stop_url,
            headers=headers,
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('result') == 'success':
                current_app.logger.info(f"Dify停止接口调用成功: {result}")
                return True
            else:
                current_app.logger.warning(f"Dify停止接口返回失败: {result}")
                return False
        else:
            current_app.logger.error(f"Dify停止接口HTTP错误: {response.status_code}, {response.text}")
            return False

    except Exception as e:
        current_app.logger.error(f"调用Dify停止接口异常: {str(e)}")
        return False