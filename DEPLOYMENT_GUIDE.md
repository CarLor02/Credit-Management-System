# 征信管理系统部署指南 - 另一台机器部署

## 📋 部署前准备

### 1. 目标机器要求
- **操作系统**: Linux (推荐 Ubuntu 20.04+)
- **内存**: 至少 4GB
- **存储**: 至少 20GB 可用空间
- **Docker**: 版本 20.10+
- **Python**: 版本 3.9+

### 2. 端口检查
确保以下端口可用：
- `3306`: MySQL数据库
- `5001`: 后端API服务
- `3000`: 前端服务 (如果需要)

## 🚀 快速部署步骤

### 第一步：准备目标机器

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装Docker
sudo apt install docker.io docker-compose -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# 3. 安装Python和工具
sudo apt install python3 python3-pip python3-venv git -y

# 4. 重新登录使Docker用户组生效
exit
```

### 第二步：获取项目代码

```bash
# 方法1: 从Git仓库克隆
git clone https://github.com/CarLor02/Credit-Management-System.git
cd Credit-Management-System/generated_backend

# 方法2: 从原机器复制
# 在原机器上打包:
# tar -czf credit-system.tar.gz Credit-Management-System/
# 传输到目标机器后解压:
# tar -xzf credit-system.tar.gz
# cd Credit-Management-System/generated_backend
```

### 第三步：一键部署MySQL

```bash
# 直接使用现有的setup_mysql.sh脚本
chmod +x setup_mysql.sh
bash setup_mysql.sh
```

脚本会自动：
- ✅ 检查Docker环境
- ✅ 创建MySQL数据目录
- ✅ 启动MySQL容器
- ✅ 等待MySQL服务就绪
- ✅ 生成生产环境配置文件

### 第四步：部署后端应用

```bash
# 1. 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 使用生产环境配置
cp .env.production .env.local

# 4. 测试MySQL连接
python test_mysql_setup.py

# 5. 初始化数据库
python create_db.py

# 6. 启动应用
python app.py
```

## 🔧 配置调整 (可选)

### 安全配置

1. **修改默认密码**：
```bash
# 修改.env.local中的密码
nano .env.local
```

2. **配置防火墙**：
```bash
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 3306  # MySQL (如果需要外部访问)
sudo ufw allow 5001  # 后端API
```

### 生产环境优化

1. **使用systemd服务**：
```bash
# 创建服务文件
sudo nano /etc/systemd/system/credit-system.service
```

2. **配置Nginx反向代理** (可选)：
```bash
sudo apt install nginx -y
# 配置Nginx转发5001端口到80端口
```

## 📊 验证部署

### 检查服务状态
```bash
# MySQL容器状态
docker ps | grep credit-mysql

# 数据库连接测试
python test_mysql_setup.py

# 查看应用日志
tail -f logs/app.log
```

### API测试
```bash
# 测试健康检查接口
curl http://localhost:5001/api/health

# 测试用户注册
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"123456"}'
```

## 🛠 故障排除

### 常见问题

1. **Docker权限问题**：
```bash
sudo chmod 666 /var/run/docker.sock
```

2. **端口占用**：
```bash
sudo netstat -tlnp | grep 3306
sudo lsof -i :5001
```

3. **MySQL连接失败**：
```bash
docker logs credit-mysql
docker exec -it credit-mysql mysql -u root -pRootPass123!
```

### 日志查看
```bash
# MySQL日志
docker logs credit-mysql

# 应用日志
tail -f logs/app.log

# 系统日志
journalctl -u credit-system
```

## 📋 部署清单

- [ ] 目标机器环境准备完成
- [ ] Docker安装并运行正常
- [ ] 项目代码已获取
- [ ] MySQL容器部署成功
- [ ] 数据库连接测试通过
- [ ] Python依赖安装完成
- [ ] 数据库初始化完成
- [ ] 应用启动成功
- [ ] API接口测试通过
- [ ] 防火墙配置完成 (如需要)

## 📞 技术支持

如遇到问题，请检查：
1. Docker服务状态：`systemctl status docker`
2. MySQL容器状态：`docker ps -a`
3. 应用日志：查看logs目录下的日志文件
4. 网络连接：确保端口未被占用

---
**部署完成后，系统将在 http://目标机器IP:5001 上提供服务**
