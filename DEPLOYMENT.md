# 征信管理系统部署指南

本文档介绍如何使用提供的脚本一键部署征信管理系统。

## 部署方式

提供了两种部署方式：

### 1. 使用 Docker Compose 部署（推荐）

**文件：** `deploy-compose.sh` + `docker-compose.yml`

**优势：**
- 配置简单，易于管理
- 自动处理服务依赖关系
- 支持健康检查
- 便于扩展和维护

**使用方法：**
```bash
./deploy-compose.sh
```

### 2. 使用原生 Docker 部署

**文件：** `deploy.sh`

**优势：**
- 更细粒度的控制
- 不依赖 Docker Compose
- 适合自定义部署需求

**使用方法：**
```bash
./deploy.sh
```

## 前置要求

### 系统要求
- Linux 或 macOS 系统
- Docker 和 Docker Compose 已安装
- Git 已安装
- curl 命令可用

### 安装 Docker 和 Docker Compose

**Ubuntu/Debian:**
```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**macOS:**
```bash
# 使用 Homebrew
brew install docker docker-compose

# 或下载 Docker Desktop
# https://www.docker.com/products/docker-desktop
```

## 配置说明

### Git 仓库配置

如果需要自动拉取代码，请在脚本中设置 `GIT_REPO_URL` 变量：

```bash
# 编辑部署脚本
vim deploy-compose.sh  # 或 deploy.sh

# 找到这一行并填入您的仓库URL
GIT_REPO_URL="https://github.com/your-username/your-repo.git"
```

### 端口配置

默认端口配置：
- 前端：3000
- 后端：5001

如需修改端口，请编辑 `docker-compose.yml` 文件中的端口映射。

## 部署步骤

### 1. 克隆或进入项目目录
```bash
cd /path/to/credit-management-system
```

### 2. 运行部署脚本
```bash
# 使用 Docker Compose（推荐）
./deploy-compose.sh

# 或使用原生 Docker
./deploy.sh
```

### 3. 等待部署完成
脚本会自动：
- 拉取最新代码（如果配置了Git仓库）
- 构建Docker镜像
- 启动前后端服务
- 等待服务就绪
- 显示访问地址

### 4. 访问系统
- 前端：http://localhost:3000
- 后端：http://localhost:5001

## 常用命令

### Docker Compose 方式

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs
docker-compose logs backend
docker-compose logs frontend

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 重新构建并启动
docker-compose up --build -d
```

### 原生 Docker 方式

```bash
# 查看容器状态
docker ps

# 查看日志
docker logs credit-management-backend
docker logs credit-management-frontend

# 停止容器
docker stop credit-management-backend credit-management-frontend

# 删除容器
docker rm credit-management-backend credit-management-frontend
```

## 故障排除

### 1. 端口被占用
```bash
# 查看端口占用
lsof -i :3000
lsof -i :5001

# 杀掉占用进程
kill -9 <PID>
```

### 2. Docker 镜像构建失败
```bash
# 清理 Docker 缓存
docker system prune -a

# 重新构建
docker-compose build --no-cache
```

### 3. 服务启动失败
```bash
# 查看详细日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 检查容器状态
docker-compose ps
```

### 4. 数据持久化问题
确保以下目录存在且有写权限：
- `./generated_backend/instance`
- `./uploads`
- `./OCR/output`

```bash
# 创建目录并设置权限
mkdir -p generated_backend/instance uploads OCR/output
chmod 755 generated_backend/instance uploads OCR/output
```

## 生产环境部署建议

### 1. 环境变量配置
创建 `.env` 文件配置敏感信息：
```bash
# .env
FLASK_SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
```

### 2. 反向代理
使用 Nginx 作为反向代理：
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:3000;
    }
    
    location /api {
        proxy_pass http://localhost:5001;
    }
}
```

### 3. SSL 证书
使用 Let's Encrypt 配置 HTTPS：
```bash
sudo certbot --nginx -d your-domain.com
```

### 4. 监控和日志
- 配置日志轮转
- 设置监控告警
- 定期备份数据

## 更新部署

重新运行部署脚本即可更新：
```bash
./deploy-compose.sh
```

脚本会自动：
- 拉取最新代码
- 重新构建镜像
- 重启服务
