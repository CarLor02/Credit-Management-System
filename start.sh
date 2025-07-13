#!/bin/bash

# 征信管理系统快速启动脚本
# 用于同时启动前端和后端服务

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 前端和后端目录
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_DIR="$SCRIPT_DIR/generated_backend"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}    征信管理系统快速启动脚本${NC}"
echo -e "${BLUE}======================================${NC}"

echo -e "${YELLOW}正在启动后端服务...${NC}"

# 启动后端服务
cd "$BACKEND_DIR"
python3 app.py &

echo -e "${GREEN}✓ 后端服务已启动${NC}"
echo -e "${GREEN}  - 后端服务地址: http://localhost:5001${NC}"

echo -e "${YELLOW}正在启动前端服务...${NC}"

# 启动前端服务
cd "$FRONTEND_DIR"
npm run dev &

echo -e "${GREEN}✓ 前端服务已启动${NC}"
echo -e "${GREEN}  - 前端服务地址: http://localhost:3000${NC}"

echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}🎉 系统启动完成!${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}前端地址: http://localhost:3000${NC}"
echo -e "${GREEN}后端地址: http://localhost:5001${NC}"
echo -e "${BLUE}======================================${NC}"

echo -e "${YELLOW}服务已在后台运行，请手动关闭终端或使用 Ctrl+C 退出脚本${NC}"
