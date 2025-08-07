"""
WebSocket事件处理器
用于实时流式输出功能
"""

from flask_socketio import emit, join_room, leave_room
from flask import current_app, request
import json
import time

# 存储活跃的WebSocket连接
active_connections = {}

def register_websocket_handlers(socketio):
    """注册WebSocket事件处理器"""
    
    @socketio.on('connect')
    def handle_connect():
        """客户端连接事件"""
        current_app.logger.info(f"WebSocket客户端连接: {request.sid}")
        emit('connected', {'message': '连接成功'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """客户端断开连接事件"""
        current_app.logger.info(f"WebSocket客户端断开连接: {request.sid}")
        # 清理连接记录
        if request.sid in active_connections:
            del active_connections[request.sid]
    
    @socketio.on('join_workflow')
    def handle_join_workflow(data):
        """加入工作流房间，开始接收流式事件"""
        workflow_run_id = data.get('workflow_run_id')
        if not workflow_run_id:
            emit('error', {'message': '缺少workflow_run_id参数'})
            return
        
        # 加入房间
        join_room(workflow_run_id)
        active_connections[request.sid] = {
            'workflow_run_id': workflow_run_id,
            'joined_at': time.time()
        }
        
        current_app.logger.info(f"客户端 {request.sid} 加入工作流房间: {workflow_run_id}")
        emit('joined_workflow', {
            'workflow_run_id': workflow_run_id,
            'message': f'已加入工作流 {workflow_run_id}'
        })
    
    @socketio.on('leave_workflow')
    def handle_leave_workflow(data):
        """离开工作流房间"""
        workflow_run_id = data.get('workflow_run_id')
        if workflow_run_id:
            leave_room(workflow_run_id)
            current_app.logger.info(f"客户端 {request.sid} 离开工作流房间: {workflow_run_id}")
        
        # 清理连接记录
        if request.sid in active_connections:
            del active_connections[request.sid]
        
        emit('left_workflow', {'workflow_run_id': workflow_run_id})

def broadcast_workflow_event(socketio, workflow_run_id, event_type, event_data=None, content=None):
    """
    向指定工作流房间广播事件
    
    Args:
        socketio: SocketIO实例
        workflow_run_id: 工作流运行ID
        event_type: 事件类型
        event_data: 事件数据
        content: 内容数据
    """
    try:
        message = {
            'event_type': event_type,
            'workflow_run_id': workflow_run_id,
            'timestamp': time.time()
        }
        
        if event_data:
            message['event_data'] = event_data
        
        if content:
            message['content'] = content
        
        # 向房间内的所有客户端广播
        socketio.emit('workflow_event', message, room=workflow_run_id)
        
        current_app.logger.info(f"广播工作流事件: {event_type} 到房间 {workflow_run_id}")
        
    except Exception as e:
        current_app.logger.error(f"广播工作流事件失败: {e}")

def broadcast_workflow_content(socketio, workflow_run_id, content_chunk):
    """
    向指定工作流房间广播内容块

    Args:
        socketio: SocketIO实例
        workflow_run_id: 工作流运行ID
        content_chunk: 内容块
    """
    try:
        # 确保content_chunk不为None
        safe_content = content_chunk if content_chunk is not None else ""

        message = {
            'workflow_run_id': workflow_run_id,
            'content_chunk': safe_content,
            'timestamp': time.time()
        }

        # 向房间内的所有客户端广播
        socketio.emit('workflow_content', message, room=workflow_run_id)

        current_app.logger.info(f"广播工作流内容到房间 {workflow_run_id}: {safe_content[:50]}...")

    except Exception as e:
        current_app.logger.error(f"广播工作流内容失败: {e}")

def broadcast_workflow_complete(socketio, workflow_run_id, final_content):
    """
    向指定工作流房间广播完成事件

    Args:
        socketio: SocketIO实例
        workflow_run_id: 工作流运行ID
        final_content: 最终内容
    """
    try:
        # 确保final_content不为None
        safe_content = final_content if final_content is not None else ""

        message = {
            'workflow_run_id': workflow_run_id,
            'final_content': safe_content,
            'timestamp': time.time()
        }

        # 向房间内的所有客户端广播
        socketio.emit('workflow_complete', message, room=workflow_run_id)

        current_app.logger.info(f"广播工作流完成事件到房间 {workflow_run_id}")

    except Exception as e:
        current_app.logger.error(f"广播工作流完成事件失败: {e}")

def broadcast_workflow_error(socketio, workflow_run_id, error_message):
    """
    向指定工作流房间广播错误事件
    
    Args:
        socketio: SocketIO实例
        workflow_run_id: 工作流运行ID
        error_message: 错误消息
    """
    try:
        message = {
            'workflow_run_id': workflow_run_id,
            'error_message': error_message,
            'timestamp': time.time()
        }
        
        # 向房间内的所有客户端广播
        socketio.emit('workflow_error', message, room=workflow_run_id)
        
        current_app.logger.error(f"广播工作流错误到房间 {workflow_run_id}: {error_message}")
        
    except Exception as e:
        current_app.logger.error(f"广播工作流错误失败: {e}")
