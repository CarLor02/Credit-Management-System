#!/bin/bash

# 征信管理系统一键部署脚本
# 功能：拉取git仓库，构建Docker镜像，启动前后端服务

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
DEPLOY_DIR="$(pwd)"

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
    docker stop ${PROJECT_NAME}-frontend ${PROJECT_NAME}-backend 2>/dev/null || true
    
    # 删除容器
    docker rm ${PROJECT_NAME}-frontend ${PROJECT_NAME}-backend 2>/dev/null || true
    
    print_message $GREEN "✓ 容器清理完成"
}

# 拉取或更新代码
update_code() {
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

# 构建后端镜像
build_backend() {
    print_title "构建后端镜像"
    
    print_message $YELLOW "正在构建后端Docker镜像..."
    docker build -f Dockerfile.backend -t ${PROJECT_NAME}-backend:latest .
    print_message $GREEN "✓ 后端镜像构建完成"
}

# 构建前端镜像
build_frontend() {
    print_title "构建前端镜像"
    
    print_message $YELLOW "正在构建前端Docker镜像..."
    docker build -f frontend/Dockerfile -t ${PROJECT_NAME}-frontend:latest ./frontend
    print_message $GREEN "✓ 前端镜像构建完成"
}

# 启动后端服务
start_backend() {
    print_title "启动后端服务"
    
    print_message $YELLOW "正在启动后端容器..."
    docker run -d \
        --name ${PROJECT_NAME}-backend \
        -p ${BACKEND_PORT}:5001 \
        -v $(pwd)/generated_backend/instance:/app/generated_backend/instance \
        -v $(pwd)/uploads:/app/uploads \
        ${PROJECT_NAME}-backend:latest
    
    print_message $GREEN "✓ 后端服务已启动"
    print_message $GREEN "  - 后端服务地址: http://localhost:${BACKEND_PORT}"
}

# 启动前端服务
start_frontend() {
    print_title "启动前端服务"
    
    print_message $YELLOW "正在启动前端容器..."
    docker run -d \
        --name ${PROJECT_NAME}-frontend \
        -p ${FRONTEND_PORT}:3000 \
        ${PROJECT_NAME}-frontend:latest
    
    print_message $GREEN "✓ 前端服务已启动"
    print_message $GREEN "  - 前端服务地址: http://localhost:${FRONTEND_PORT}"
}

# 等待服务启动
wait_for_services() {
    print_title "等待服务启动"
    
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
    echo ""
    print_message $YELLOW "常用命令:"
    print_message $YELLOW "  - 查看容器状态: docker ps"
    print_message $YELLOW "  - 查看后端日志: docker logs ${PROJECT_NAME}-backend"
    print_message $YELLOW "  - 查看前端日志: docker logs ${PROJECT_NAME}-frontend"
    print_message $YELLOW "  - 停止服务: docker stop ${PROJECT_NAME}-frontend ${PROJECT_NAME}-backend"
    print_message $YELLOW "  - 重新部署: ./deploy.sh"
}

# 主函数
main() {
    print_title "征信管理系统一键部署"
    
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
    
    # 清理容器
    cleanup_containers
    
    # 更新代码
    update_code
    
    # 构建镜像
    build_backend
    build_frontend
    
    # 启动服务
    start_backend
    start_frontend
    
    # 等待服务启动
    wait_for_services
    
    # 显示结果
    show_result
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
