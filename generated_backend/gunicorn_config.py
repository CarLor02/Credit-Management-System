"""
征信管理系统后端 Gunicorn 配置文件
专门为文档处理、知识库服务和实时通信优化的配置
"""

import os
import multiprocessing

# 基础配置
bind = "0.0.0.0:5001"
backlog = 2048

# Worker 配置 - 针对文档处理优化
workers = 4  # 4个worker，适合CPU密集型的文档处理任务
worker_class = "sync"  # 同步worker，适合长时间运行的任务
worker_connections = 1000  # 每个worker的最大连接数
max_requests = 200  # 减少max_requests，防止内存累积
max_requests_jitter = 20  # 随机化重启，避免同时重启

# 超时配置 - 为长时间文档处理优化
timeout = 600  # 10分钟超时，适合大文档OCR处理
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
]

# 根据可用CPU数量动态调整worker数量（可选）
if os.environ.get('GUNICORN_AUTO_WORKERS', '').lower() == 'true':
    workers = min(4, multiprocessing.cpu_count())
    print(f"自动调整Worker数量为: {workers}")

# 开发环境特殊配置
if os.environ.get('FLASK_ENV') == 'development':
    reload = True
    reload_engine = 'auto'
    timeout = 300  # 开发环境减少超时时间
else:
    reload = False
