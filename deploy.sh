#!/bin/bash

# 征信管理系统一键部署脚本 - 高性能WebSocket模式
# 功能：拉取git仓库，使用挂载方式启动前后端服务，支持高性能WebSocket
#
# 使用方法:
#   ./deploy.sh           # 高性能部署（多Worker + Redis）
#   ./deploy.sh --skip-git # 跳过代码拉取，直接部署
#   ./deploy.sh --force-build # 强制重新构建基础镜像

set -e  # 遇到错误立即退出

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 配置参数
PROJECT_NAME="credit-management-system"
FRONTEND_PORT=3000
BACKEND_PORT=5001
REDIS_PORT=6379
DEPLOY_DIR="$(pwd)"
SKIP_GIT=false
FORCE_BUILD=false

# 解析命令行参数
for arg in "$@"; do
    case $arg in
        --skip-git)
            SKIP_GIT=true
            shift
            ;;
        --force-build)
            FORCE_BUILD=true
            shift
            ;;
        -h|--help)
            echo "使用方法:"
            echo "  $0                    # 高性能部署（多Worker + Redis）"
            echo "  $0 --skip-git         # 跳过代码拉取，直接部署"
            echo "  $0 --force-build      # 强制重新构建基础镜像"
            echo "  $0 --help             # 显示帮助信息"
            exit 0
            ;;
        *)
            # 未知参数
            ;;
    esac
done

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 打印标题
print_title() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}    $1${NC}"
    echo -e "${BLUE}======================================${NC}"
}

# 检查命令是否存在
check_command() {
    local cmd=$1
    if ! command -v $cmd &> /dev/null; then
        print_message $RED "错误: $cmd 命令未找到，请先安装 $cmd"
        exit 1
    fi
}

# 检查并杀掉占用指定端口的进程
kill_port() {
    local port=$1
    local service_name=$2
    
    print_message $YELLOW "检查端口 $port 是否被占用..."
    
    # 查找占用端口的进程
    local pid=$(lsof -ti:$port 2>/dev/null || true)
    
    if [ ! -z "$pid" ]; then
        print_message $RED "发现端口 $port 被进程 $pid 占用，正在终止..."
        kill -9 $pid 2>/dev/null || true
        sleep 2
        
        # 再次检查是否成功终止
        local check_pid=$(lsof -ti:$port 2>/dev/null || true)
        if [ -z "$check_pid" ]; then
            print_message $GREEN "✓ 成功清理端口 $port"
        else
            print_message $RED "✗ 清理端口 $port 失败，可能需要手动处理"
        fi
    else
        print_message $GREEN "✓ 端口 $port 未被占用"
    fi
}

# 停止并删除现有容器
cleanup_containers() {
    print_message $YELLOW "清理现有容器..."

    # 停止容器
    docker stop ${PROJECT_NAME}-frontend ${PROJECT_NAME}-backend ${PROJECT_NAME}-redis 2>/dev/null || true

    # 删除容器
    docker rm ${PROJECT_NAME}-frontend ${PROJECT_NAME}-backend ${PROJECT_NAME}-redis 2>/dev/null || true

    print_message $GREEN "✓ 容器清理完成"
}

# 拉取或更新代码
update_code() {
    if [ "$SKIP_GIT" = true ]; then
        print_title "跳过代码更新"
        print_message $YELLOW "已跳过代码拉取，使用当前代码进行部署"
        return
    fi

    print_title "更新代码"

    if [ -d ".git" ]; then
        print_message $YELLOW "检测到Git仓库，正在拉取最新代码..."
        git fetch origin
        git reset --hard origin/$(git rev-parse --abbrev-ref HEAD)
        print_message $GREEN "✓ 代码更新完成"
    else
        print_message $YELLOW "未检测到Git仓库，跳过代码拉取"
        print_message $YELLOW "如需使用Git管理代码，请先初始化Git仓库"
    fi
}

# 检查依赖是否变化
check_dependencies_changed() {
    local service=$1
    local deps_file=""
    local hash_file=""

    if [ "$service" = "backend" ]; then
        deps_file="generated_backend/requirements.txt OCR/requirements.txt"
        hash_file=".backend_deps_hash"
    elif [ "$service" = "frontend" ]; then
        deps_file="frontend/package.json frontend/pnpm-lock.yaml"
        hash_file=".frontend_deps_hash"
    else
        return 1
    fi

    # 计算当前依赖文件的哈希值
    local current_hash=""
    for file in $deps_file; do
        if [ -f "$file" ]; then
            # 兼容 macOS 和 Linux 的 md5 命令
            if command -v md5sum >/dev/null 2>&1; then
                current_hash="${current_hash}$(md5sum "$file" 2>/dev/null || echo "")"
            elif command -v md5 >/dev/null 2>&1; then
                current_hash="${current_hash}$(md5 -q "$file" 2>/dev/null || echo "")"
            else
                current_hash="${current_hash}$(stat -c %Y "$file" 2>/dev/null || echo "")"
            fi
        fi
    done

    # 计算最终哈希值
    if command -v md5sum >/dev/null 2>&1; then
        current_hash=$(echo "$current_hash" | md5sum | cut -d' ' -f1)
    elif command -v md5 >/dev/null 2>&1; then
        current_hash=$(echo "$current_hash" | md5 -q)
    else
        current_hash=$(echo "$current_hash" | cksum | cut -d' ' -f1)
    fi

    # 检查是否存在之前的哈希值
    if [ -f "$hash_file" ]; then
        local old_hash=$(cat "$hash_file")
        if [ "$current_hash" = "$old_hash" ]; then
            return 1  # 依赖未变化
        fi
    fi

    # 保存新的哈希值
    echo "$current_hash" > "$hash_file"
    return 0  # 依赖已变化
}

# 构建后端基础镜像（仅包含依赖）
build_backend_base() {
    print_title "构建后端基础镜像"

    # 检查是否需要重新构建
    if [ "$FORCE_BUILD" = false ] && ! check_dependencies_changed "backend"; then
        if docker image inspect ${PROJECT_NAME}-backend-base:latest >/dev/null 2>&1; then
            print_message $GREEN "✓ 后端依赖未变化，跳过基础镜像构建"
            return
        fi
    fi

    print_message $YELLOW "正在构建后端基础镜像（仅依赖）..."

    # 创建临时 Dockerfile
    cat > Dockerfile.backend.base << 'EOF'
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y python3 python3-pip && \
    ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

RUN apt-get install -y \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    libcairo2 \
    libcairo-gobject2

WORKDIR /app

COPY generated_backend/requirements.txt ./generated_backend/requirements.txt
COPY OCR/requirements.txt ./OCR/requirements.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r generated_backend/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir -r OCR/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制 Gunicorn 配置文件
COPY generated_backend/gunicorn_config.py ./generated_backend/gunicorn_config.py

# 设置环境变量
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app/generated_backend
EOF

    docker build -f Dockerfile.backend.base -t ${PROJECT_NAME}-backend-base:latest .
    rm -f Dockerfile.backend.base
    print_message $GREEN "✓ 后端基础镜像构建完成"
}

# 构建前端基础镜像（仅包含依赖）
build_frontend_base() {
    print_title "构建前端基础镜像"

    # 检查是否需要重新构建
    if [ "$FORCE_BUILD" = false ] && ! check_dependencies_changed "frontend"; then
        if docker image inspect ${PROJECT_NAME}-frontend-base:latest >/dev/null 2>&1; then
            print_message $GREEN "✓ 前端依赖未变化，跳过基础镜像构建"
            return
        fi
    fi

    print_message $YELLOW "正在构建前端基础镜像（仅依赖）..."

    # 创建临时 Dockerfile
    cat > frontend/Dockerfile.base << 'EOF'
FROM node:22.17.0

# 设置工作目录
WORKDIR /app

# 使用国内镜像加速依赖下载（可选）
RUN npm install -g pnpm && \
    npm config set registry https://registry.npmmirror.com

# 拷贝依赖描述文件
COPY package.json pnpm-lock.yaml ./

# 安装依赖（使用缓存）
RUN pnpm install

EXPOSE 3000
EOF

    docker build -f frontend/Dockerfile.base -t ${PROJECT_NAME}-frontend-base:latest ./frontend
    rm -f frontend/Dockerfile.base
    print_message $GREEN "✓ 前端基础镜像构建完成"
}

# 启动Redis服务（高性能模式需要）
start_redis() {
    print_title "启动Redis服务"

    print_message $YELLOW "正在启动Redis容器..."
    docker run -d \
        --name ${PROJECT_NAME}-redis \
        -p ${REDIS_PORT}:6379 \
        --memory=256m \
        --memory-swap=256m \
        redis:7-alpine \
        redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru

    print_message $GREEN "✓ Redis服务已启动"
    print_message $GREEN "  - Redis地址: redis://localhost:${REDIS_PORT}"
    print_message $YELLOW "  - 内存限制: 256MB"
    print_message $YELLOW "  - 持久化: 启用"
    print_message $YELLOW "  - 内存策略: allkeys-lru"
}

# 启动后端服务（使用挂载方式）
start_backend() {
    print_title "启动后端服务"

    print_message $YELLOW "配置为高性能模式（多Worker + Redis）"

    print_message $YELLOW "正在启动后端容器..."
    docker run -d \
        --name ${PROJECT_NAME}-backend \
        -p ${BACKEND_PORT}:5001 \
        --memory=16g \
        --memory-swap=16g \
        --oom-kill-disable=false \
        --cpus="4.0" \
        --network="host" \
        -e GUNICORN_AUTO_WORKERS=true \
        -e USE_REDIS_BROKER=true \
        -e REDIS_URL=redis://localhost:${REDIS_PORT}/0 \
        -e FLASK_ENV=production \
        -e PYTHONPATH=/app \
        -e PYTHONUNBUFFERED=1 \
        -e PYTHONDONTWRITEBYTECODE=1 \
        -v $(pwd)/generated_backend:/app/generated_backend \
        -v $(pwd)/OCR:/app/OCR \
        -v $(pwd)/uploads:/app/uploads \
        ${PROJECT_NAME}-backend-base:latest \
        gunicorn --config gunicorn_config.py app:app

    print_message $GREEN "✓ 后端服务已启动（高性能多Worker模式）"
    print_message $GREEN "  - 后端服务地址: http://localhost:${BACKEND_PORT}"
    print_message $YELLOW "  - Worker数量: 2-4个（自动调整）"
    print_message $YELLOW "  - Redis支持: 启用"
    print_message $YELLOW "  - 内存限制: 16GB"
    print_message $YELLOW "  - CPU限制: 4核"
    print_message $YELLOW "  - Worker类型: eventlet (支持WebSocket)"
    print_message $YELLOW "  - 配置文件: gunicorn_config.py"
    print_message $YELLOW "  - 代码实时同步: 是"
    print_message $YELLOW "  - WebSocket支持: 是"
}

# 启动前端服务（使用挂载方式）
start_frontend() {
    print_title "启动前端服务"

    print_message $YELLOW "正在启动前端容器（使用代码挂载）..."

    # 首先确保本地有 node_modules（从基础镜像复制）
    if [ ! -d "frontend/node_modules" ]; then
        print_message $YELLOW "正在从基础镜像复制 node_modules..."
        docker run --rm \
            -v $(pwd)/frontend:/host_app \
            ${PROJECT_NAME}-frontend-base:latest \
            sh -c "cp -r /app/node_modules /host_app/"
    fi

    # 构建前端项目
    print_message $YELLOW "正在构建前端项目..."
    docker run --rm \
        -v $(pwd)/frontend:/app \
        -w /app \
        ${PROJECT_NAME}-frontend-base:latest \
        pnpm build

    # 启动前端服务
    docker run -d \
        --name ${PROJECT_NAME}-frontend \
        -p ${FRONTEND_PORT}:3000 \
        -v $(pwd)/frontend:/app \
        -w /app \
        ${PROJECT_NAME}-frontend-base:latest \
        pnpm start

    print_message $GREEN "✓ 前端服务已启动（代码挂载模式）"
    print_message $GREEN "  - 前端服务地址: http://localhost:${FRONTEND_PORT}"
    print_message $YELLOW "  - 代码实时同步: 是"
    print_message $YELLOW "  - node_modules: 已同步到本地"
}

# 等待服务启动
wait_for_services() {
    print_title "等待服务启动"

    # 等待Redis服务
    print_message $YELLOW "等待Redis服务启动..."
    local redis_ready=false
    local attempts=0
    local max_attempts=15

    while [ $attempts -lt $max_attempts ] && [ "$redis_ready" = false ]; do
        if docker exec ${PROJECT_NAME}-redis redis-cli ping > /dev/null 2>&1; then
            redis_ready=true
            print_message $GREEN "✓ Redis服务已就绪"
        else
            print_message $YELLOW "等待Redis服务启动... (${attempts}/${max_attempts})"
            sleep 1
            attempts=$((attempts + 1))
        fi
    done

    if [ "$redis_ready" = false ]; then
        print_message $RED "⚠ Redis服务启动超时，请检查日志"
    fi

    print_message $YELLOW "等待后端服务启动..."
    local backend_ready=false
    local attempts=0
    local max_attempts=30

    while [ $attempts -lt $max_attempts ] && [ "$backend_ready" = false ]; do
        if curl -s http://localhost:${BACKEND_PORT}/health > /dev/null 2>&1; then
            backend_ready=true
            print_message $GREEN "✓ 后端服务已就绪"
        else
            print_message $YELLOW "等待后端服务启动... (${attempts}/${max_attempts})"
            sleep 2
            attempts=$((attempts + 1))
        fi
    done

    if [ "$backend_ready" = false ]; then
        print_message $RED "⚠ 后端服务启动超时，请检查日志"
    fi
    
    print_message $YELLOW "等待前端服务启动..."
    local frontend_ready=false
    attempts=0
    
    while [ $attempts -lt $max_attempts ] && [ "$frontend_ready" = false ]; do
        if curl -s http://localhost:${FRONTEND_PORT} > /dev/null 2>&1; then
            frontend_ready=true
            print_message $GREEN "✓ 前端服务已就绪"
        else
            print_message $YELLOW "等待前端服务启动... (${attempts}/${max_attempts})"
            sleep 2
            attempts=$((attempts + 1))
        fi
    done
    
    if [ "$frontend_ready" = false ]; then
        print_message $RED "⚠ 前端服务启动超时，请检查日志"
    fi
}

# 显示部署结果
show_result() {
    print_title "部署完成"

    print_message $GREEN "🎉 征信管理系统部署成功!"
    echo ""
    print_message $GREEN "服务地址:"
    print_message $GREEN "  - 前端: http://localhost:${FRONTEND_PORT}"
    print_message $GREEN "  - 后端: http://localhost:${BACKEND_PORT}"
    print_message $GREEN "  - Redis: redis://localhost:${REDIS_PORT}"
    echo ""
    print_message $BLUE "部署模式:"
    print_message $BLUE "  - 高性能多Worker模式"
    print_message $BLUE "  - Worker数量: 2-4个（自动调整）"
    print_message $BLUE "  - WebSocket支持: 是（Redis消息代理）"
    print_message $BLUE "  - Redis支持: 是"
    print_message $BLUE "  - 性能提升: 2-4倍"
    print_message $BLUE "  - 代码挂载模式，修改实时生效"
    print_message $BLUE "  - 基础镜像缓存，快速部署"
    echo ""
    print_message $YELLOW "常用命令:"
    print_message $YELLOW "  - 查看容器状态: docker ps"
    print_message $YELLOW "  - 查看后端日志: docker logs ${PROJECT_NAME}-backend"
    print_message $YELLOW "  - 查看前端日志: docker logs ${PROJECT_NAME}-frontend"
    print_message $YELLOW "  - 查看Redis日志: docker logs ${PROJECT_NAME}-redis"
    print_message $YELLOW "  - Redis状态检查: docker exec ${PROJECT_NAME}-redis redis-cli info"
    print_message $YELLOW "  - 健康检查: curl http://localhost:${BACKEND_PORT}/health"
    print_message $YELLOW "  - 停止所有服务: docker stop ${PROJECT_NAME}-frontend ${PROJECT_NAME}-backend ${PROJECT_NAME}-redis"
    print_message $YELLOW "  - 重新部署: ./deploy.sh"
    print_message $YELLOW "  - 强制重建: ./deploy.sh --force-build"
    print_message $YELLOW "  - 性能监控: ./monitor.sh"
}

# 主函数
main() {
    print_title "征信管理系统一键部署 - 高性能多Worker模式"
    
    # 检查必要的命令
    print_message $YELLOW "检查系统环境..."
    check_command "docker"
    check_command "git"
    check_command "curl"
    check_command "lsof"
    print_message $GREEN "✓ 系统环境检查通过"
    
    # 清理端口
    print_message $YELLOW "清理端口..."
    kill_port $BACKEND_PORT "后端服务"
    kill_port $FRONTEND_PORT "前端服务"
    kill_port $REDIS_PORT "Redis服务"
    
    # 清理容器
    cleanup_containers
    
    # 更新代码
    update_code

    # 构建基础镜像（仅在依赖变化时）
    build_backend_base
    build_frontend_base

    # 启动服务（使用挂载方式）
    start_redis      # 启动Redis（高性能模式）
    start_backend    # 启动后端
    start_frontend   # 启动前端
    
    # 等待服务启动
    wait_for_services
    
    # 显示结果
    show_result
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
