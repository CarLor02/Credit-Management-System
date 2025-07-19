"""
报告生成API
"""

import os
import time
import requests
from flask import request, jsonify, current_app

# 导入配置（如果需要的话）
# from config import Config

def register_report_routes(app):
    """注册报告相关路由"""
    
    @app.route('/api/generate_report', methods=['POST'])
    def generate_report():
        """
        生成报告的独立API接口
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "error": "缺少请求数据"}), 400

            # 获取参数
            dataset_id = data.get('dataset_id')
            company_name = data.get('company_name')
            knowledge_name = data.get('knowledge_name')

            # 验证必要参数
            if not company_name:
                return jsonify({"success": False, "error": "缺少必要参数: company_name"}), 400

            if not dataset_id:
                return jsonify({"success": False, "error": "缺少必要参数: dataset_id"}), 400

            # 如果没有提供knowledge_name，使用company_name作为默认值
            if not knowledge_name:
                knowledge_name = company_name
                current_app.logger.info(f"未提供knowledge_name，使用company_name作为默认值: {knowledge_name}")

            current_app.logger.info(f"开始生成报告 - 公司: {company_name}, 知识库: {knowledge_name}")

            # 检查解析状态
            if dataset_id:
                parsing_complete = check_parsing_status(dataset_id)
                if not parsing_complete:
                    return jsonify({
                        "success": False,
                        "error": "文档解析尚未完成，请等待解析完成后再生成报告",
                        "parsing_complete": False
                    }), 400

            # 调用报告生成API
            report_content, workflow_run_id = call_report_generation_api(company_name, knowledge_name)
            
            # 保存报告到本地文件
            file_path = save_report_to_file(company_name, report_content)
            
            current_app.logger.info(f"报告生成成功，已保存到: {file_path}")

            return jsonify({
                "success": True,
                "message": "报告生成成功",
                "workflow_run_id": workflow_run_id,
                "content": report_content,
                "file_path": file_path,
                "parsing_complete": True
            })

        except Exception as e:
            current_app.logger.error(f"生成报告失败: {str(e)}")
            return jsonify({"success": False, "error": f"生成报告失败: {str(e)}"}), 500


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


def call_report_generation_api(company_name, knowledge_name):
    """调用报告生成API"""
    try:
        # 真实API调用
        report_api_url = current_app.config.get('REPORT_API_URL', 'http://172.16.76.203/v1/workflows/run')
        api_key = current_app.config.get('REPORT_API_KEY', 'app-zLDrndvfJ81HaTWD3gXXVJaq')

        current_app.logger.info(f"调用报告生成API: {report_api_url}")
        current_app.logger.info(f"使用公司名称: {company_name}, 知识库名称: {knowledge_name}")

        # 构建请求数据
        request_data = {
            "inputs": {
                "company": company_name,
                "knowledge_name": knowledge_name
            },
            "response_mode": "blocking",
            "user": "root"
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

        response.raise_for_status()
        report_response = response.json()

        status = report_response["data"]["status"]
        current_app.logger.info(f"报告API响应状态: {status}")

        if status != "succeeded":
            error_text = report_response["data"].get("error", "未知错误")
            current_app.logger.error(f"报告API错误响应: {error_text}")
            raise Exception(f'生成报告失败，状态: {status}, 错误: {error_text}')

        full_content = report_response["data"]["outputs"]["text"]
        workflow_run_id = report_response.get("workflow_run_id", "")

        return full_content, workflow_run_id

    except requests.exceptions.Timeout:
        raise Exception("报告生成请求超时")
    except requests.exceptions.ConnectionError:
        raise Exception("无法连接到报告生成服务")
    except requests.exceptions.RequestException as e:
        raise Exception(f"报告生成请求失败: {str(e)}")
    except Exception as e:
        current_app.logger.error(f"调用报告生成API失败: {str(e)}")
        raise Exception(f"调用报告生成API失败: {str(e)}")





def save_report_to_file(company_name, content):
    """保存报告内容到本地文件"""
    try:
        output_dir = "output"
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建文件名：公司名称-时间戳.md
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        safe_company_name = company_name.replace("/", "-").replace("\\", "-").replace(":", "-")
        filename = f"{safe_company_name}-{timestamp}.md"
        file_path = os.path.join(output_dir, filename)
        
        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        current_app.logger.info(f"报告已保存到文件: {file_path}")
        return file_path
        
    except Exception as e:
        current_app.logger.error(f"保存报告文件失败: {e}")
        raise Exception(f"保存报告文件失败: {str(e)}")
