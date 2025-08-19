"""
征信管理系统后端 Gunicorn 配置文件
专门为文档处理、知识库服务和WebSocket实时通信优化的配置
支持Flask-SocketIO的eventlet异步模式
"""

import os
import multiprocessing

# 基础配置
bind = "0.0.0.0:5001"
backlog = 2048

# Worker 配置 - 针对文档处理和WebSocket通信优化
# 动态调整worker数量以平衡WebSocket支持和性能
cpu_count = multiprocessing.cpu_count()
workers = min(max(2, cpu_count // 2), 4)  # 2-4个worker，根据CPU核心数调整
worker_class = "eventlet"  # 使用eventlet支持WebSocket长连接
worker_connections = 2000  # 增加每个worker的最大连接数
max_requests = 1000  # 适度的请求重启，平衡内存和连接稳定性
max_requests_jitter = 100  # 添加随机性避免同时重启

# 超时配置 - 为长时间文档处理和WebSocket连接优化
timeout = 300  # 设置为5分钟，平衡长连接和资源释放
keepalive = 5  # 保持连接时间
graceful_timeout = 60  # 优雅关闭超时

# 内存和进程管理
worker_tmp_dir = "/dev/shm"  # 使用内存文件系统
max_worker_memory = 2048  # 单个worker最大内存(MB)
worker_memory_high_watermark = 0.8  # 内存高水位线

# 预加载应用
preload_app = True  # 预加载应用，减少内存占用

# 日志配置
accesslog = "-"  # 访问日志输出到stdout
errorlog = "-"   # 错误日志输出到stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程名称
proc_name = "credit-management-backend"

# 安全配置
user = None  # 在容器环境中不需要切换用户
group = None
umask = 0

# 性能优化
worker_process_count = workers
pidfile = "/tmp/gunicorn.pid"

# SSL配置（如果需要）
# keyfile = None
# certfile = None

# 自定义钩子函数
def when_ready(server):
    """服务器准备就绪时的回调"""
    server.log.info("征信管理系统后端服务已准备就绪")
    server.log.info(f"Worker数量: {workers}")
    server.log.info(f"超时时间: {timeout}秒")
    server.log.info(f"最大请求数: {max_requests}")

def worker_int(worker):
    """Worker收到SIGINT信号时的回调"""
    worker.log.info(f"Worker {worker.pid} 收到中断信号")

def pre_fork(server, worker):
    """Worker fork之前的回调"""
    server.log.info(f"启动Worker {worker.age}")

def post_fork(server, worker):
    """Worker fork之后的回调"""
    server.log.info(f"Worker {worker.pid} 已启动")
    
def pre_exec(server):
    """重新加载应用前的回调"""
    server.log.info("准备重新加载应用")

def on_exit(server):
    """服务器退出时的回调"""
    server.log.info("征信管理系统后端服务正在退出")

def worker_abort(worker):
    """Worker异常退出时的回调"""
    worker.log.error(f"Worker {worker.pid} 异常退出")

# 环境变量优化
raw_env = [
    'PYTHONUNBUFFERED=1',
    'PYTHONDONTWRITEBYTECODE=1', 
    'MALLOC_TRIM_THRESHOLD_=100000',  # 内存管理优化
    'PYTHONHASHSEED=random',  # 随机化哈希种子
    'EVENTLET_HUB=poll',  # 优化eventlet性能
]

# 根据环境变量和CPU数量动态调整worker数量
if os.environ.get('GUNICORN_AUTO_WORKERS', '').lower() == 'true':
    # 自动调整worker数量，平衡WebSocket支持和性能
    cpu_count = multiprocessing.cpu_count()
    workers = min(max(2, cpu_count // 2), 4)
    print(f"自动调整Worker数量: {workers} (基于CPU核心数: {cpu_count})")
else:
    # 默认使用多worker模式提升性能
    print(f"默认多Worker模式: {workers}")

# 开发环境特殊配置
if os.environ.get('FLASK_ENV') == 'development':
    reload = True
    reload_engine = 'auto'
    timeout = 0  # 开发环境也允许长连接
else:
    reload = False

# WebSocket 多Worker配置说明:
# - 使用 eventlet worker 类支持 WebSocket 长连接
# - 多worker模式通过Redis/消息队列实现WebSocket状态共享
# - timeout=300 平衡长连接和资源管理
# - max_requests=1000 适度重启worker，避免内存泄漏
# - Flask-SocketIO 应用需要使用 async_mode='eventlet'
# - 需要配置Redis作为消息代理以支持多worker WebSocket通信

# 性能优化建议:
# 1. 设置 GUNICORN_AUTO_WORKERS=true 启用自动worker调整
# 2. 配置Redis消息队列支持多worker WebSocket
# 3. 使用负载均衡器分发HTTP和WebSocket请求
# 4. 监控worker内存使用情况，适时调整max_requests
