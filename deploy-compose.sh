#!/bin/bash

# 征信管理系统一键部署脚本 (使用 Docker Compose)
# 功能：拉取git仓库，使用Docker Compose构建和启动前后端服务

set -e  # 遇到错误立即退出

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 配置参数
PROJECT_NAME="credit-management-system"
COMPOSE_FILE="docker-compose.yml"

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

# 停止现有服务
stop_services() {
    print_title "停止现有服务"
    
    print_message $YELLOW "停止现有Docker Compose服务..."
    docker-compose -f $COMPOSE_FILE down --remove-orphans 2>/dev/null || true
    print_message $GREEN "✓ 现有服务已停止"
}

# 构建和启动服务
deploy_services() {
    print_title "构建和启动服务"
    
    print_message $YELLOW "构建Docker镜像..."
    docker-compose -f $COMPOSE_FILE build --no-cache
    print_message $GREEN "✓ 镜像构建完成"
    
    print_message $YELLOW "启动服务..."
    docker-compose -f $COMPOSE_FILE up -d
    print_message $GREEN "✓ 服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    print_title "等待服务就绪"
    
    print_message $YELLOW "等待服务启动..."
    
    # 等待后端服务
    local backend_ready=false
    local attempts=0
    local max_attempts=60
    
    while [ $attempts -lt $max_attempts ] && [ "$backend_ready" = false ]; do
        if docker-compose -f $COMPOSE_FILE ps backend | grep -q "Up"; then
            if curl -s http://localhost:5001/health > /dev/null 2>&1; then
                backend_ready=true
                print_message $GREEN "✓ 后端服务已就绪"
            fi
        fi
        
        if [ "$backend_ready" = false ]; then
            print_message $YELLOW "等待后端服务启动... (${attempts}/${max_attempts})"
            sleep 3
            attempts=$((attempts + 1))
        fi
    done
    
    if [ "$backend_ready" = false ]; then
        print_message $RED "⚠ 后端服务启动超时，请检查日志: docker-compose logs backend"
    fi
    
    # 等待前端服务
    local frontend_ready=false
    attempts=0
    
    while [ $attempts -lt $max_attempts ] && [ "$frontend_ready" = false ]; do
        if docker-compose -f $COMPOSE_FILE ps frontend | grep -q "Up"; then
            if curl -s http://localhost:3000 > /dev/null 2>&1; then
                frontend_ready=true
                print_message $GREEN "✓ 前端服务已就绪"
            fi
        fi
        
        if [ "$frontend_ready" = false ]; then
            print_message $YELLOW "等待前端服务启动... (${attempts}/${max_attempts})"
            sleep 3
            attempts=$((attempts + 1))
        fi
    done
    
    if [ "$frontend_ready" = false ]; then
        print_message $RED "⚠ 前端服务启动超时，请检查日志: docker-compose logs frontend"
    fi
}

# 显示服务状态
show_status() {
    print_title "服务状态"
    
    print_message $YELLOW "当前服务状态:"
    docker-compose -f $COMPOSE_FILE ps
    echo ""
}

# 显示部署结果
show_result() {
    print_title "部署完成"
    
    print_message $GREEN "🎉 征信管理系统部署成功!"
    echo ""
    print_message $GREEN "服务地址:"
    print_message $GREEN "  - 前端: http://localhost:3000"
    print_message $GREEN "  - 后端: http://localhost:5001"
    echo ""
    print_message $YELLOW "常用命令:"
    print_message $YELLOW "  - 查看服务状态: docker-compose ps"
    print_message $YELLOW "  - 查看所有日志: docker-compose logs"
    print_message $YELLOW "  - 查看后端日志: docker-compose logs backend"
    print_message $YELLOW "  - 查看前端日志: docker-compose logs frontend"
    print_message $YELLOW "  - 停止服务: docker-compose down"
    print_message $YELLOW "  - 重启服务: docker-compose restart"
    print_message $YELLOW "  - 重新部署: ./deploy-compose.sh"
}

# 主函数
main() {
    print_title "征信管理系统一键部署 (Docker Compose)"
    
    # 检查必要的命令
    print_message $YELLOW "检查系统环境..."
    check_command "docker"
    check_command "docker-compose"
    check_command "git"
    check_command "curl"
    print_message $GREEN "✓ 系统环境检查通过"
    
    # 检查Docker Compose文件
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_message $RED "错误: 未找到 $COMPOSE_FILE 文件"
        exit 1
    fi
    
    # 更新代码
    update_code
    
    # 停止现有服务
    stop_services
    
    # 部署服务
    deploy_services
    
    # 等待服务就绪
    wait_for_services
    
    # 显示状态
    show_status
    
    # 显示结果
    show_result
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
