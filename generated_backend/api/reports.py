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
from db_models import Project, AnalysisReport, ReportType, ReportStatus

# 导入PDF转换服务
from services.pdf_converter import convert_report_to_pdf, is_pdf_conversion_available
from services.md_to_pdf_converter import MarkdownToPDFConverter
from database import db

# 导入认证装饰器
from api.auth import token_required

# 导入配置（如果需要的话）
# from config import Config

# 全局变量，用于存储每个工作流的事件和内容
workflow_events = {}  # 格式: {workflow_run_id: {'events': [], 'content': '', 'metadata': {}}}

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
                
                # 检查报告状态，如果正在生成则不允许重复生成
                if project.report_status == ReportStatus.GENERATING:
                    return jsonify({"success": False, "error": "报告正在生成中，请稍后再试"}), 400

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
    def stop_report_generation():
        """
        停止正在生成的报告
        """
        # 处理OPTIONS预检请求
        if request.method == 'OPTIONS':
            return jsonify({"success": True}), 200

        # 对POST请求进行token验证
        from api.auth import token_required

        @token_required
        def _handle_stop_request():
            try:
                data = request.get_json()
                project_id = data.get('project_id')
                if not project_id:
                    return jsonify({"success": False, "error": "缺少project_id参数"}), 400

                # 获取项目
                project = Project.query.get(project_id)
                if not project:
                    return jsonify({"success": False, "error": "项目不存在"}), 404

                # 更新项目报告状态为已取消
                project.report_status = ReportStatus.CANCELLED
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

        return _handle_stop_request()

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

            # 验证必要参数
            if not company_name:
                return jsonify({"success": False, "error": "缺少必要参数: company_name"}), 400

            if not dataset_id:
                return jsonify({"success": False, "error": "缺少必要参数: dataset_id"}), 400

            if not project_id:
                return jsonify({"success": False, "error": "缺少必要参数: project_id"}), 400

            # 检查项目是否存在
            project = Project.query.get(project_id)
            if not project:
                return jsonify({"success": False, "error": "项目不存在"}), 404

            # 检查报告状态，如果正在生成则不允许重复生成
            if project.report_status == ReportStatus.GENERATING:
                return jsonify({"success": False, "error": "报告正在生成中，请稍后再试"}), 400

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

            # 更新项目报告状态为正在生成
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

            # 检查解析状态（仅在非测试环境下）
            if dataset_id and not dataset_id.startswith('test_'):
                parsing_complete = check_parsing_status(dataset_id)
                if not parsing_complete:
                    # 通过WebSocket广播错误
                    broadcast_workflow_error(socketio, project_room_id, "文档解析尚未完成，请等待解析完成后再生成报告", project_id)
                    return

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
                    db.session.commit()

                # 通过WebSocket广播报告完成
                broadcast_workflow_complete(socketio, project_room_id, report_content)
            except Exception as api_error:
                current_app.logger.error(f"调用外部API失败: {str(api_error)}")

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
            project = Project.query.get(project_id)
            if not project:
                return jsonify({
                    "success": False,
                    "error": "项目不存在"
                }), 404

            # 如果报告路径为空或None，返回成功但无内容的响应
            if not project.report_path or project.report_path.strip() == "":
                return jsonify({
                    "success": False,
                    "error": "该项目尚未生成报告",
                    "has_report": False,
                    "company_name": project.name
                }), 200  # 改为200状态码，表示请求成功但无报告

            # 检查文件是否存在
            if not os.path.exists(project.report_path):
                # 文件不存在，清空数据库中的路径
                project.report_path = None
                db.session.commit()
                current_app.logger.warning(f"报告文件不存在，已清空数据库路径: {project.report_path}")

                return jsonify({
                    "success": False,
                    "error": "报告文件不存在",
                    "has_report": False,
                    "company_name": project.name
                }), 200  # 改为200状态码

            # 读取报告内容
            try:
                with open(project.report_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查内容是否为空
                if not content or content.strip() == "":
                    return jsonify({
                        "success": False,
                        "error": "报告内容为空",
                        "has_report": False,
                        "company_name": project.name
                    }), 200

                return jsonify({
                    "success": True,
                    "content": content,
                    "file_path": project.report_path,
                    "company_name": project.name,
                    "has_report": True
                })
            except Exception as read_error:
                current_app.logger.error(f"读取报告文件失败: {read_error}")
                return jsonify({
                    "success": False,
                    "error": "读取报告文件失败",
                    "has_report": False,
                    "company_name": project.name
                }), 200  # 改为200状态码

        except Exception as e:
            current_app.logger.error(f"获取项目报告失败: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"获取项目报告失败: {str(e)}",
                "has_report": False
            }), 500

    @app.route('/api/projects/<int:project_id>/report', methods=['DELETE'])
    def delete_project_report(project_id):
        """
        删除项目的报告文件和相关数据
        """
        try:
            project = Project.query.get(project_id)
            if not project:
                return jsonify({
                    "success": False,
                    "error": "项目不存在"
                }), 404

            current_app.logger.info(f"开始删除项目 {project_id} 的报告")

            # 删除报告文件
            if project.report_path and os.path.exists(project.report_path):
                try:
                    os.remove(project.report_path)
                    current_app.logger.info(f"已删除报告文件: {project.report_path}")
                except Exception as file_error:
                    current_app.logger.error(f"删除报告文件失败: {file_error}")
                    # 继续执行，不因为文件删除失败而中断

            # 清空数据库中的报告路径
            project.report_status = ReportStatus.NOT_GENERATED
            project.report_path = None
            db.session.commit()
            current_app.logger.info(f"已清空项目 {project_id} 的报告路径")



            return jsonify({
                "success": True,
                "message": "报告删除成功"
            })

        except Exception as e:
            current_app.logger.error(f"删除项目报告失败: {str(e)}")
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
            success, message, pdf_path = convert_report_to_pdf(md_content, project.name, project.report_path)

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
                converter = MarkdownToPDFConverter()
                html_content = converter.convert_markdown_to_html(md_content, project.report_path)

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
            return jsonify({
                "success": False,
                "error": f"获取HTML报告失败: {str(e)}"
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
                converter = MarkdownToPDFConverter()
                html_content = converter.convert_markdown_to_html(md_content, project.report_path)

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


def check_parsing_status(dataset_id):
    """检查文档解析状态"""
    try:
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


def call_report_generation_api_streaming(company_name, knowledge_name, project_id=None, project_room_id=None):
    """调用报告生成API - 流式模式"""
    try:
        # 新API调用
        report_api_url = current_app.config.get('REPORT_API_URL', 'http://172.16.18.157:18080/v1/chat-messages')
        api_key = current_app.config.get('REPORT_API_KEY', 'app-c8cKydhESsFxtG7QZvZkR5YU')

        current_app.logger.info(f"调用报告生成API (流式): {report_api_url}")
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
        workflow_run_id, full_content, metadata, events = parse_dify_streaming_response(response, company_name, project_id, project_room_id)

        current_app.logger.info(f"流式响应解析完成，workflow_run_id: {workflow_run_id}")
        current_app.logger.info(f"提取到的事件数量: {len(events)}")
        current_app.logger.info(f"内容长度: {len(full_content) if full_content is not None else 0}")

        # 存储流式数据到全局变量，供前端查询
        if workflow_run_id:
            workflow_events[workflow_run_id] = {
                'events': events,
                'content': full_content,
                'metadata': metadata,
                'timestamp': time.time(),
                'company_name': company_name
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


def call_report_generation_api(company_name, knowledge_name):
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
        tuple: (workflow_run_id, full_content, metadata, events)
    """
    workflow_run_id = f"workflow_{int(time.time())}"  # 新接口没有workflow_run_id，我们自己生成一个
    full_content = ""
    metadata = {}
    events = []
    sequence_number = 0

    print("开始解析流式响应...")

    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue

        # 解析 SSE 格式数据
        line_str = line.decode('utf-8') if isinstance(line, bytes) else line
        if line_str.startswith('data: '):
            data_str = line_str[6:]  # 移除 'data: ' 前缀

            # 检查是否是结束标记
            if data_str.strip() == '[DONE]':
                print("收到结束标记 [DONE]")
                break

            try:
                # 解析 JSON 数据
                data = json.loads(data_str)
                print(f"解析的 JSON 数据: {json.dumps(data, ensure_ascii=False)[:500]}...")

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
                    print(f"累积内容，当前总长度: {len(full_content)}")
                    print(f"内容块详情: {repr(content_chunk[:100])}")  # 使用repr显示转义字符

                    # 通过WebSocket广播内容到项目房间
                    try:
                        socketio = current_app.socketio
                        if project_room_id:
                            broadcast_workflow_content(socketio, project_room_id, content_chunk)
                            print(f"已广播内容块到房间 {project_room_id}: {repr(content_chunk[:50])}")
                    except Exception as e:
                        print(f"WebSocket内容广播失败: {e}")

                # 提取事件信息
                if 'event' in data:
                    event_type = data['event']
                    print(f"提取到事件: {event_type}")

                    # 调试：打印节点事件的详细信息
                    if event_type in ['node_started', 'node_finished']:
                        print(f"📊 节点事件详情: {json.dumps(data, ensure_ascii=False, indent=2)}")
                        if 'data' in data:
                            print(f"📊 节点数据: title={data['data'].get('title')}, node_id={data['data'].get('node_id')}")

                    # 映射事件类型到我们系统的事件
                    mapped_event = {
                        'message': 'content_generated',
                        'message_end': 'workflow_finished',
                        'error': 'workflow_error'
                    }.get(event_type, event_type)

                    events.append(mapped_event)
                    sequence_number += 1

                    # 通过WebSocket广播事件到项目房间
                    try:
                        socketio = current_app.socketio
                        if project_room_id:
                            broadcast_workflow_event(socketio, project_room_id, mapped_event, data)
                    except Exception as e:
                        print(f"WebSocket事件广播失败: {e}")

                # 提取元数据
                if 'metadata' in data:
                    metadata.update(data['metadata'])
                    print(f"提取到元数据: {json.dumps(data['metadata'], ensure_ascii=False)[:100]}...")

            except json.JSONDecodeError as e:
                print(f"JSON 解析错误: {e}, 原始数据: {data_str}")
                continue

    # 流式解析完成，广播完成事件到项目房间
    try:
        socketio = current_app.socketio
        if project_room_id:
            broadcast_workflow_complete(socketio, project_room_id, full_content, project_id)
            print(f"已广播完成事件到房间 {project_room_id}，最终内容长度: {len(full_content)}")
    except Exception as e:
        print(f"WebSocket完成事件广播失败: {e}")

    print(f"流式解析完成 - workflow_run_id: {workflow_run_id}, 事件数: {len(events)}, 内容长度: {len(full_content)}")
    return workflow_run_id, full_content, metadata, events


def save_report_to_file(company_name, content, project_id=None):
    """保存报告内容到本地文件"""
    try:
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

        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        current_app.logger.info(f"报告已保存到文件: {file_path}")
        return file_path

    except Exception as e:
        current_app.logger.error(f"保存报告文件失败: {e}")
        raise Exception(f"保存报告文件失败: {str(e)}")
