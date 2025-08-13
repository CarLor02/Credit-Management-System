#!/bin/bash

# 征信管理系统MySQL数据库设置脚本

echo "=== 征信管理系统 MySQL 数据库设置 ==="
echo

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装，请先安装Docker"
    exit 1
fi

# 检查Docker是否运行
if ! docker info &> /dev/null; then
    echo "错误: Docker 未运行，请启动Docker"
    exit 1
fi

echo "✓ Docker 已安装并运行"

# 创建MySQL数据目录
echo "创建MySQL数据目录..."
mkdir -p ./mysql_data
echo "✓ MySQL数据目录创建完成"

# 启动MySQL容器
echo "启动MySQL容器..."
docker run -d --name credit-mysql \
  -p 3306:3306 \
  -v $(pwd)/mysql_data:/var/lib/mysql \
  -e MYSQL_ROOT_PASSWORD=RootPass123! \
  -e MYSQL_DATABASE=credit_db \
  -e MYSQL_USER=credit_user \
  -e MYSQL_PASSWORD=UserPass123! \
  --health-cmd="mysqladmin ping -p\$MYSQL_ROOT_PASSWORD || exit 1" \
  --health-interval=30s --health-retries=3 --health-timeout=5s \
  mysql:8.0 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci

if [ $? -eq 0 ]; then
    echo "✓ MySQL容器启动成功"
else
    echo "✗ MySQL容器启动失败"
    exit 1
fi

# 等待MySQL启动
echo "等待MySQL服务启动..."
sleep 10

# 检查MySQL健康状态
echo "检查MySQL健康状态..."
timeout=60
elapsed=0

while [ $elapsed -lt $timeout ]; do
    if docker exec credit-mysql mysqladmin ping -h localhost -u root -pRootPass123! &> /dev/null; then
        echo "✓ MySQL服务已就绪"
        break
    fi
    sleep 2
    elapsed=$((elapsed + 2))
    echo "等待中... (${elapsed}s/${timeout}s)"
done

if [ $elapsed -ge $timeout ]; then
    echo "✗ MySQL服务启动超时"
    exit 1
fi

# 创建环境配置文件
echo "创建环境配置文件..."
cat > .env.production << EOF
# 征信管理系统生产环境配置
FLASK_ENV=production
DEBUG=False
SECRET_KEY=\$(openssl rand -hex 32)
JWT_SECRET_KEY=\$(openssl rand -hex 32)

# 数据库配置 - MySQL专用
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=RootPass123!
MYSQL_DATABASE=credit_db
MYSQL_CHARSET=utf8mb4

# SQLAlchemy配置
SQLALCHEMY_ECHO=False

# 服务器配置
HOST=0.0.0.0
PORT=5001

# 文件上传配置
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# 日志配置
LOG_LEVEL=INFO
EOF

echo "✓ 生产环境配置文件创建完成: .env.production"

echo
echo "=== 设置完成 ==="
echo "MySQL容器信息:"
echo "  容器名称: credit-mysql"
echo "  端口: 3306"
echo "  数据库: credit_db"
echo "  Root用户: root"
echo "  Root密码: RootPass123!"
echo "  数据目录: $(pwd)/mysql_data"
echo
echo "部署到另一台机器的步骤:"
echo "1. 将整个项目代码复制到目标机器"
echo "2. 在目标机器上运行此脚本: bash setup_mysql.sh"
echo "3. 安装Python依赖: pip install -r requirements.txt"
echo "4. 测试数据库连接: python test_mysql_setup.py"
echo "5. 初始化数据库: python create_db.py"
echo "6. 启动应用: python app.py"
echo
echo "管理命令:"
echo "  停止MySQL: docker stop credit-mysql"
echo "  启动MySQL: docker start credit-mysql"
echo "  删除容器: docker rm -f credit-mysql"
echo "  查看日志: docker logs credit-mysql"
echo "  备份数据: docker exec credit-mysql mysqldump -u root -pRootPass123! --all-databases > backup.sql"
echo
echo "防火墙配置 (如需要):"
echo "  开放3306端口: sudo ufw allow 3306"
echo "  开放5001端口: sudo ufw allow 5001"
