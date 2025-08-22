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
worker_connections = 1000  # 减少连接数避免内存压力
max_requests = 2000  # 增加请求重启阈值，减少频繁重启
max_requests_jitter = 200  # 添加随机性避免同时重启

# 超时配置 - 为长时间流式处理优化
timeout = 0  # 设置为0表示无超时限制，适用于长时间流式处理
keepalive = 2  # 缩短保持连接时间
graceful_timeout = 120  # 增加优雅关闭超时，给流式处理足够时间完成

# 内存和进程管理 - 增强监控
worker_tmp_dir = "/dev/shm"  # 使用内存文件系统
max_worker_memory = 1024  # 降低单个worker最大内存(MB)限制
worker_memory_high_watermark = 0.7  # 降低内存高水位线
worker_memory_check_interval = 5  # 缩短内存检查间隔(秒)

# 预加载应用 - 在流式处理场景下关闭预加载
preload_app = False  # 关闭预加载，减少内存占用和进程间冲突

# 日志配置 - 增强调试信息
accesslog = "-"  # 访问日志输出到stdout
errorlog = "-"   # 错误日志输出到stderr
loglevel = "debug"  # 提升日志级别到debug
capture_output = True  # 捕获worker输出
enable_stdio_inheritance = True  # 继承stdio
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s [Memory: %(p)s] [Worker: %(worker_pid)s]'

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
    try:
        server.log.info("征信管理系统后端服务已准备就绪")
        server.log.info(f"Worker数量: {workers}")
        server.log.info(f"超时时间: {timeout}秒")
        server.log.info(f"最大请求数: {max_requests}")
    except Exception as e:
        server.log.error(f"When-ready回调异常: {e}")

def worker_int(worker):
    """Worker收到SIGINT信号时的回调"""
    try:
        worker.log.critical(f"Worker {worker.pid} 收到中断信号 SIGINT")
        worker.log.critical(f"Worker {worker.pid} 当前内存使用情况: {_get_worker_memory_usage(worker.pid)} MB")
        worker.log.critical(f"Worker {worker.pid} 活动连接数: {getattr(worker, 'connections', 'unknown')}")
        
        # 记录更多调试信息
        worker.log.critical(f"Worker {worker.pid} 当前处理的请求数: {getattr(worker, 'nr', 'unknown')}")
        worker.log.critical(f"Worker {worker.pid} 运行时长: {getattr(worker, 'age', 'unknown')}秒")
        worker.log.critical(f"Worker {worker.pid} 系统内存状态: {_get_system_memory()}")
        
        # 强制进行垃圾回收
        try:
            import gc
            gc.collect()
            worker.log.info(f"Worker {worker.pid} 执行垃圾回收完成")
        except Exception as gc_error:
            worker.log.error(f"Worker {worker.pid} 垃圾回收失败: {gc_error}")
    except Exception as e:
        try:
            worker.log.error(f"Worker interrupt回调异常: {e}")
        except:
            pass  # 如果连日志都无法记录，则静默失败

def pre_fork(server, worker):
    """Worker fork之前的回调"""
    try:
        server.log.info(f"启动Worker {worker.age} - 系统内存状态: {_get_system_memory()}")
    except Exception as e:
        server.log.error(f"Pre-fork回调异常: {e}")

def post_fork(server, worker):
    """Worker fork之后的回调"""
    try:
        server.log.info(f"Worker {worker.pid} 已启动 - 初始内存: {_get_worker_memory_usage(worker.pid)} MB")
    except Exception as e:
        server.log.error(f"Post-fork回调异常: {e}")
    
def pre_exec(server):
    """重新加载应用前的回调"""
    try:
        server.log.info("准备重新加载应用")
    except Exception as e:
        server.log.error(f"Pre-exec回调异常: {e}")

def on_exit(server):
    """服务器退出时的回调"""
    try:
        server.log.info("征信管理系统后端服务正在退出")
    except Exception as e:
        server.log.error(f"On-exit回调异常: {e}")

def worker_abort(worker):
    """Worker异常退出时的回调"""
    try:
        worker.log.error(f"Worker {worker.pid} 异常退出")
        worker.log.error(f"退出时内存使用: {_get_worker_memory_usage(worker.pid)} MB")
        worker.log.error(f"退出时系统内存: {_get_system_memory()}")
        worker.log.error(f"Worker处理的最后请求数: {getattr(worker, 'requests_count', 'unknown')}")
    except Exception as e:
        try:
            worker.log.error(f"Worker abort回调异常: {e}")
        except:
            pass  # 如果连日志都无法记录，则静默失败

def child_exit(server, worker):
    """Worker子进程退出时的回调"""
    # EventletWorker 可能没有 exitcode 属性，需要安全获取
    exit_code = getattr(worker, 'exitcode', 'unknown')
    server.log.warning(f"Worker {worker.pid} 子进程退出，退出码: {exit_code}")
    server.log.warning(f"Worker {worker.pid} 总处理请求数: {worker.nr}")
    server.log.warning(f"Worker {worker.pid} 运行时长: {worker.age}秒")

def worker_exit(server, worker):
    """Worker正常退出时的回调"""
    try:
        server.log.info(f"Worker {worker.pid} 正常退出")
        server.log.info(f"Worker {worker.pid} 最终内存使用: {_get_worker_memory_usage(worker.pid)} MB")
        server.log.info(f"Worker {worker.pid} 处理的请求总数: {worker.nr}")
    except Exception as e:
        server.log.error(f"Worker退出回调异常: {e}")

def nworkers_changed(server, new_value, old_value):
    """Worker数量变化时的回调"""
    try:
        server.log.info(f"Worker数量从 {old_value} 变更为 {new_value}")
    except Exception as e:
        server.log.error(f"Worker数量变化回调异常: {e}")

def worker_connections_changed(server, worker, new_value, old_value):
    """Worker连接数变化时的回调"""
    try:
        server.log.debug(f"Worker {worker.pid} 连接数从 {old_value} 变更为 {new_value}")
    except Exception as e:
        server.log.error(f"Worker连接数变化回调异常: {e}")

def _get_worker_memory_usage(pid):
    """获取worker内存使用情况"""
    try:
        import os
        with open(f'/proc/{pid}/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    return round(int(line.split()[1]) / 1024, 2)
        return "unknown"
    except:
        return "unknown"

def _get_system_memory():
    """获取系统内存使用情况"""
    try:
        import os
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
            total = int([line for line in lines if line.startswith('MemTotal:')][0].split()[1]) / 1024 / 1024
            available = int([line for line in lines if line.startswith('MemAvailable:')][0].split()[1]) / 1024 / 1024
            used_percent = round((total - available) / total * 100, 2)
            return f"总内存: {round(total, 2)}GB, 已用: {used_percent}%"
    except:
        return "unknown"

# 环境变量优化 - 增强调试和监控，优化内存管理
raw_env = [
    'PYTHONUNBUFFERED=1',
    'PYTHONDONTWRITEBYTECODE=1', 
    'MALLOC_TRIM_THRESHOLD_=50000',  # 降低内存管理阈值
    'PYTHONHASHSEED=random',  # 随机化哈希种子
    'EVENTLET_HUB=poll',  # 优化eventlet性能
    'EVENTLET_NOPATCH=1',  # 防止eventlet过度patch
    'PYTHONGC=1',  # 启用垃圾回收
    'PYTHONASYNCIODEBUG=0',  # 在生产环境关闭asyncio调试
    'EVENTLET_THREADPOOL_SIZE=20',  # 限制eventlet线程池大小
    'PYTHONMALLOC=malloc',  # 使用系统malloc而不是Python的调试malloc
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

# WebSocket 流式处理优化配置说明:
# - timeout=0: 取消超时限制，避免长时间流式处理被中断
# - max_requests=500: 降低请求重启阈值，及时释放内存避免累积
# - worker_connections=1000: 适度的连接数，平衡性能和内存使用
# - graceful_timeout=120: 给流式处理足够时间完成
# - preload_app=False: 避免预加载应用导致的进程间冲突
# - EVENTLET_NOPATCH=1: 防止eventlet过度patch导致的异常
# - MALLOC_TRIM_THRESHOLD_=50000: 更积极的内存回收

# 内存管理策略:
# 1. 降低单worker内存限制到1GB，及时重启高内存worker
# 2. 缩短内存检查间隔到5秒，快速响应内存压力
# 3. 使用系统malloc而不是Python调试malloc，减少内存开销
# 4. 在worker退出时强制垃圾回收

# 流式处理监控:
# 1. 增强worker退出时的日志记录，便于诊断
# 2. 监控worker连接数和处理请求数变化
# 3. 记录详细的内存使用情况和系统状态
