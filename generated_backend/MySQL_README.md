# MySQL数据库配置说明

## 概述

征信管理系统后端已精简为**仅支持MySQL数据库**，具备完整的自动初始化功能。

## 核心文件

系统包含3个核心数据库文件：

1. **`database.py`** - 数据库连接、初始化和自动创建功能
2. **`db_models.py`** - 数据库模型定义  
3. **`seed_data.py`** - 种子数据（用户数据）

## 自动初始化功能

启动时系统会自动：

1. ✅ 创建MySQL数据库（如果不存在）
2. ✅ 创建所有必需的数据库表（如果不存在）
3. ✅ 创建数据库索引
4. ✅ 创建种子用户数据（如果数据库为空）

## 环境配置

设置以下环境变量：

```bash
# MySQL数据库配置
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=credit_db
```

## 种子用户数据

系统会自动创建4个测试用户：

| 用户名 | 邮箱 | 密码 | 角色 |
|--------|------|------|------|
| admin | admin@example.com | admin123 | 管理员 |
| user1 | user1@example.com | user123 | 普通用户 |
| user2 | user2@example.com | user123 | 普通用户 |
| user3 | user3@example.com | user123 | 普通用户 |

## 启动应用

```bash
python app.py
```

启动时会看到类似输出：
```
✓ 数据库已存在: credit_db
✓ 数据库表已存在 (14 个表)
✓ 数据库连接配置完成: mysql+pymysql://root:***@localhost:3306/credit_db
✓ MySQL数据库连接正常
```

## 健康检查

访问健康检查端点验证数据库连接：
```
http://localhost:5001/health
```

## 注意事项

- 🔒 **安全提示**: 生产环境请修改默认密码
- 📊 **数据持久化**: 系统不会删除现有数据
- 🚀 **零配置**: 无需手动创建数据库或表
- 🔧 **自动修复**: 缺失的表会自动重建
