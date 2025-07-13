"""
每日统计数据更新任务
可以通过cron job或其他调度器定期执行
"""

import sys
import os
from datetime import datetime, date
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_stats.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def update_daily_stats():
    """更新每日统计数据"""
    try:
        from app import app
        from services.stats_service import StatsService
        
        with app.app_context():
            logger.info("开始更新每日统计数据...")
            
            success = StatsService.update_daily_stats()
            
            if success:
                logger.info("每日统计数据更新成功")
                return True
            else:
                logger.error("每日统计数据更新失败")
                return False
                
    except Exception as e:
        logger.error(f"更新每日统计数据时发生错误: {e}")
        return False

def cleanup_old_activities(days_to_keep=30):
    """清理旧的活动日志"""
    try:
        from app import app
        from db_models import ActivityLog
        from database import db
        from datetime import timedelta
        
        with app.app_context():
            logger.info(f"开始清理 {days_to_keep} 天前的活动日志...")
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # 删除旧的活动日志
            deleted_count = ActivityLog.query.filter(
                ActivityLog.created_at < cutoff_date
            ).delete()
            
            db.session.commit()
            
            logger.info(f"清理了 {deleted_count} 条旧活动日志")
            return True
            
    except Exception as e:
        logger.error(f"清理旧活动日志时发生错误: {e}")
        return False

def cleanup_old_stats(days_to_keep=90):
    """清理旧的统计数据"""
    try:
        from app import app
        from db_models import DashboardStats
        from database import db
        from datetime import timedelta
        
        with app.app_context():
            logger.info(f"开始清理 {days_to_keep} 天前的统计数据...")
            
            cutoff_date = date.today() - timedelta(days=days_to_keep)
            
            # 删除旧的统计数据
            deleted_count = DashboardStats.query.filter(
                DashboardStats.date < cutoff_date
            ).delete()
            
            db.session.commit()
            
            logger.info(f"清理了 {deleted_count} 条旧统计数据")
            return True
            
    except Exception as e:
        logger.error(f"清理旧统计数据时发生错误: {e}")
        return False

def generate_weekly_report():
    """生成周报（可选功能）"""
    try:
        from app import app
        from db_models import DashboardStats
        from datetime import timedelta
        
        with app.app_context():
            logger.info("开始生成周报...")
            
            # 获取过去7天的统计数据
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
            
            weekly_stats = DashboardStats.query.filter(
                DashboardStats.date >= start_date,
                DashboardStats.date <= end_date
            ).order_by(DashboardStats.date).all()
            
            if not weekly_stats:
                logger.warning("没有找到周报数据")
                return False
            
            # 计算周报指标
            total_projects_start = weekly_stats[0].total_projects if weekly_stats else 0
            total_projects_end = weekly_stats[-1].total_projects if weekly_stats else 0
            projects_growth = total_projects_end - total_projects_start
            
            avg_score = sum(s.average_score for s in weekly_stats) / len(weekly_stats)
            
            # 生成周报内容
            report_content = f"""
# 征信管理系统周报
**报告期间**: {start_date} 至 {end_date}

## 核心指标
- 项目总数: {total_projects_end} (增长: {projects_growth})
- 平均评分: {avg_score:.1f}
- 活跃用户: {weekly_stats[-1].active_users if weekly_stats else 0}

## 趋势分析
- 项目增长趋势: {'上升' if projects_growth > 0 else '下降' if projects_growth < 0 else '平稳'}
- 风险项目占比: {(weekly_stats[-1].high_risk_projects / max(weekly_stats[-1].total_projects, 1) * 100):.1f}%

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            # 保存周报到文件
            os.makedirs('reports', exist_ok=True)
            report_filename = f"reports/weekly_report_{end_date.strftime('%Y%m%d')}.md"
            
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"周报生成成功: {report_filename}")
            return True
            
    except Exception as e:
        logger.error(f"生成周报时发生错误: {e}")
        return False

def run_daily_tasks():
    """运行所有每日任务"""
    logger.info("开始执行每日任务...")
    
    tasks = [
        ("更新每日统计", update_daily_stats),
        ("清理旧活动日志", lambda: cleanup_old_activities(30)),
        ("清理旧统计数据", lambda: cleanup_old_stats(90)),
    ]
    
    success_count = 0
    
    for task_name, task_func in tasks:
        logger.info(f"执行任务: {task_name}")
        try:
            if task_func():
                logger.info(f"任务 '{task_name}' 执行成功")
                success_count += 1
            else:
                logger.error(f"任务 '{task_name}' 执行失败")
        except Exception as e:
            logger.error(f"任务 '{task_name}' 执行异常: {e}")
    
    # 每周一生成周报
    if datetime.now().weekday() == 0:  # 0 = Monday
        logger.info("执行周报生成任务")
        try:
            if generate_weekly_report():
                logger.info("周报生成成功")
                success_count += 1
            else:
                logger.error("周报生成失败")
        except Exception as e:
            logger.error(f"周报生成异常: {e}")
    
    logger.info(f"每日任务执行完成，成功: {success_count}/{len(tasks)}")
    return success_count == len(tasks)

if __name__ == '__main__':
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    # 运行每日任务
    success = run_daily_tasks()
    
    # 退出码
    sys.exit(0 if success else 1)
