#!/bin/bash

# 征信管理系统快速启动脚本
# 用于同时启动前端和后端服务

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 端口配置
FRONTEND_PORT=3000
BACKEND_PORT=5001

# 检查并杀掉占用指定端口的进程
kill_port() {
    local port=$1
    local service_name=$2
    
    echo -e "${YELLOW}检查端口 $port 是否被占用...${NC}"
    
    # 查找占用端口的进程
    local pid=$(lsof -ti:$port)
    
    if [ ! -z "$pid" ]; then
        echo -e "${RED}发现端口 $port 被进程 $pid 占用，正在终止...${NC}"
        kill -9 $pid 2>/dev/null
        sleep 1
        
        # 再次检查是否成功终止
        local check_pid=$(lsof -ti:$port)
        if [ -z "$check_pid" ]; then
            echo -e "${GREEN}✓ 成功清理端口 $port${NC}"
        else
            echo -e "${RED}✗ 清理端口 $port 失败，可能需要手动处理${NC}"
        fi
    else
        echo -e "${GREEN}✓ 端口 $port 未被占用${NC}"
    fi
}

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 前端和后端目录
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_DIR="$SCRIPT_DIR/generated_backend"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}    征信管理系统快速启动脚本${NC}"
echo -e "${BLUE}======================================${NC}"

# 清理端口
echo -e "${YELLOW}正在清理端口...${NC}"
kill_port $BACKEND_PORT "后端服务"
kill_port $FRONTEND_PORT "前端服务"
echo ""

echo -e "${YELLOW}正在启动后端服务...${NC}"

# 启动后端服务
cd "$BACKEND_DIR"
python app.py &

echo -e "${GREEN}✓ 后端服务已启动${NC}"
echo -e "${GREEN}  - 后端服务地址: http://localhost:$BACKEND_PORT${NC}"

echo -e "${YELLOW}正在启动前端服务...${NC}"

# 启动前端服务
cd "$FRONTEND_DIR"
npm run dev &

echo -e "${GREEN}✓ 前端服务已启动${NC}"
echo -e "${GREEN}  - 前端服务地址: http://localhost:$FRONTEND_PORT${NC}"

echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}🎉 系统启动完成!${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}前端地址: http://localhost:$FRONTEND_PORT${NC}"
echo -e "${GREEN}后端地址: http://localhost:$BACKEND_PORT${NC}"
echo -e "${BLUE}======================================${NC}"

echo -e "${YELLOW}服务已在后台运行，请手动关闭终端或使用 Ctrl+C 退出脚本${NC}"
