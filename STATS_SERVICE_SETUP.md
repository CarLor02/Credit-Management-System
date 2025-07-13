# 统计服务设置指南

## 📋 概述

本指南介绍如何设置和使用新的统计服务，包括数据库表创建、服务配置和前端集成。

## 🗄️ 数据库变更

### 新增表结构

#### 1. dashboard_stats 表
存储每日仪表板统计数据，用于历史趋势分析。

```sql
CREATE TABLE dashboard_stats (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    total_projects INTEGER DEFAULT 0,
    completed_projects INTEGER DEFAULT 0,
    processing_projects INTEGER DEFAULT 0,
    collecting_projects INTEGER DEFAULT 0,
    archived_projects INTEGER DEFAULT 0,
    total_documents INTEGER DEFAULT 0,
    completed_documents INTEGER DEFAULT 0,
    processing_documents INTEGER DEFAULT 0,
    failed_documents INTEGER DEFAULT 0,
    total_users INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    average_score REAL DEFAULT 0.0,
    high_risk_projects INTEGER DEFAULT 0,
    medium_risk_projects INTEGER DEFAULT 0,
    low_risk_projects INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. activity_logs 表
存储系统活动日志，用于最近活动展示。

```sql
CREATE TABLE activity_logs (
    id INTEGER PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    user_id INTEGER,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    metadata JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

## 🚀 部署步骤

### 1. 运行数据库迁移

```bash
cd generated_backend
python migrations/add_stats_tables.py
```

这将：
- 创建新的统计表
- 初始化当天的统计数据
- 创建示例活动记录

### 2. 验证表创建

```python
# 在Python shell中验证
from app import app
from db_models import DashboardStats, ActivityLog

with app.app_context():
    # 检查表是否存在
    stats_count = DashboardStats.query.count()
    activities_count = ActivityLog.query.count()
    print(f"统计记录: {stats_count}, 活动记录: {activities_count}")
```

### 3. 设置定时任务

#### 使用 cron (Linux/Mac)

```bash
# 编辑 crontab
crontab -e

# 添加每日凌晨2点执行统计更新
0 2 * * * cd /path/to/project/generated_backend && python tasks/daily_stats_task.py >> logs/cron.log 2>&1
```

#### 使用 Windows 任务计划程序

1. 打开"任务计划程序"
2. 创建基本任务
3. 设置每日执行
4. 操作：启动程序
5. 程序：`python`
6. 参数：`tasks/daily_stats_task.py`
7. 起始于：项目的 `generated_backend` 目录

## 🔧 API 接口

### 新增的统计接口

#### 1. 获取仪表板统计
```
GET /api/stats/dashboard
```

响应格式：
```json
{
  "success": true,
  "data": {
    "projects": {
      "total": 156,
      "completed": 89,
      "processing": 23,
      "collecting": 32,
      "archived": 12,
      "completion_rate": 57.1
    },
    "documents": {
      "total": 342,
      "completed": 298,
      "processing": 15,
      "failed": 29,
      "completion_rate": 87.1
    },
    "users": {
      "total": 24,
      "active": 18
    },
    "risk_analysis": {
      "high_risk": 7,
      "medium_risk": 45,
      "low_risk": 104
    },
    "average_score": 78.5
  }
}
```

#### 2. 获取趋势数据
```
GET /api/stats/trends?period=month&months=6
```

#### 3. 获取最近活动
```
GET /api/logs/recent?limit=10
```

#### 4. 手动更新统计
```
POST /api/stats/update
```

## 🎨 前端集成

### 1. 统计服务使用

```typescript
import { statsService } from '@/services/statsService';

// 获取仪表板数据
const response = await statsService.getDashboardStats();
if (response.success) {
  const statCards = statsService.transformToStatCards(response.data);
  setStats(statCards);
}

// 获取趋势数据
const trendsResponse = await statsService.getTrendsData('month', 6);

// 获取最近活动
const activitiesResponse = await statsService.getRecentActivities(10);
```

### 2. Mock 数据支持

统计服务完全支持 Mock 模式，在开发环境中可以使用模拟数据：

```bash
# 使用 Mock 数据
npm run dev:mock

# 使用真实 API
npm run dev:real
```

## 📊 数据流程

### 1. 统计数据更新流程

```
每日定时任务 → 计算当前统计 → 保存到 dashboard_stats → 缓存供API使用
```

### 2. 活动日志记录流程

```
用户操作 → 触发活动记录 → 保存到 activity_logs → 显示在最近活动
```

### 3. 前端数据获取流程

```
页面加载 → 调用统计API → 数据转换 → 更新UI组件
```

## 🔍 监控和维护

### 1. 日志文件

- `logs/daily_stats.log` - 每日统计任务日志
- `logs/cron.log` - 定时任务执行日志

### 2. 数据清理

定时任务会自动清理：
- 30天前的活动日志
- 90天前的统计数据

### 3. 性能监控

```python
# 检查统计表大小
from db_models import DashboardStats, ActivityLog

stats_count = DashboardStats.query.count()
activities_count = ActivityLog.query.count()

print(f"统计记录数: {stats_count}")
print(f"活动记录数: {activities_count}")
```

## 🐛 故障排除

### 1. 统计数据不更新

检查：
- 定时任务是否正常运行
- 数据库连接是否正常
- 日志文件中的错误信息

解决：
```bash
# 手动运行统计更新
python tasks/daily_stats_task.py

# 检查日志
tail -f logs/daily_stats.log
```

### 2. 前端显示异常

检查：
- API 接口是否返回正确数据
- Mock 配置是否正确
- 浏览器控制台错误信息

解决：
```bash
# 测试 API 接口
curl http://localhost:5001/api/stats/dashboard

# 检查 Mock 配置
echo $NEXT_PUBLIC_USE_MOCK
```

### 3. 活动日志缺失

检查：
- 活动记录代码是否正确调用
- 数据库写入权限
- 用户ID是否有效

## 📈 扩展功能

### 1. 添加新的统计指标

1. 在 `DashboardStats` 模型中添加字段
2. 更新 `StatsService._calculate_current_stats()` 方法
3. 修改前端数据转换逻辑

### 2. 添加新的活动类型

1. 在相应的业务逻辑中调用 `ActivityLogger`
2. 更新前端图标映射
3. 添加相应的显示逻辑

### 3. 自定义报告

可以基于 `dashboard_stats` 表生成各种自定义报告：
- 月度报告
- 季度报告
- 年度报告

## 📝 注意事项

1. **数据一致性**: 统计数据每日更新，实时性要求不高的场景使用缓存数据
2. **性能考虑**: 大量数据时考虑分页和索引优化
3. **备份策略**: 定期备份统计数据，特别是历史趋势数据
4. **权限控制**: 确保只有授权用户可以访问统计接口

## 🎯 下一步计划

1. **实时统计**: 考虑使用 WebSocket 实现实时数据更新
2. **高级分析**: 添加更多维度的数据分析
3. **可视化增强**: 增加更多图表类型和交互功能
4. **导出功能**: 支持统计数据的导出功能
