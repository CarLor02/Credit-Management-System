#!/bin/bash

# 征信管理系统性能监控脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_NAME="credit-management-system"

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 检查服务状态
check_services() {
    print_message $BLUE "=== 服务状态检查 ==="
    
    # 检查容器状态
    if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(backend|frontend|redis)"; then
        print_message $GREEN "✓ 容器服务运行中"
    else
        print_message $RED "✗ 容器服务未运行"
        return 1
    fi
    
    echo ""
    
    # 检查健康状态
    print_message $YELLOW "健康检查:"
    if curl -s http://localhost:5001/health > /dev/null 2>&1; then
        print_message $GREEN "✓ 后端服务健康"
        health_info=$(curl -s http://localhost:5001/health | python3 -m json.tool 2>/dev/null || echo "健康检查响应格式错误")
        echo "$health_info"
    else
        print_message $RED "✗ 后端服务异常"
    fi
}

# 监控资源使用
monitor_resources() {
    print_message $BLUE "=== 资源使用监控 ==="
    
    # Docker容器资源使用
    print_message $YELLOW "容器资源使用:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | grep -E "(backend|frontend|redis|CONTAINER)"
    
    echo ""
    
    # 系统资源
    print_message $YELLOW "系统资源:"
    if command -v top >/dev/null 2>&1; then
        cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//' 2>/dev/null || echo "N/A")
        print_message $YELLOW "CPU使用率: ${cpu_usage}%"
    fi
    
    if command -v df >/dev/null 2>&1; then
        disk_usage=$(df -h / | tail -1 | awk '{print $5}' 2>/dev/null || echo "N/A")
        print_message $YELLOW "磁盘使用: $disk_usage"
    fi
}

# 监控Redis性能
monitor_redis() {
    print_message $BLUE "=== Redis性能监控 ==="
    
    if docker ps | grep -q "${PROJECT_NAME}-redis"; then
        # Redis连接数
        connected_clients=$(docker exec ${PROJECT_NAME}-redis redis-cli info clients 2>/dev/null | grep "connected_clients" | cut -d: -f2 | tr -d '\r' || echo "N/A")
        print_message $YELLOW "Redis连接数: $connected_clients"
        
        # Redis内存使用
        used_memory=$(docker exec ${PROJECT_NAME}-redis redis-cli info memory 2>/dev/null | grep "used_memory_human" | cut -d: -f2 | tr -d '\r' || echo "N/A")
        print_message $YELLOW "Redis内存使用: $used_memory"
        
        # Redis命令统计
        total_commands=$(docker exec ${PROJECT_NAME}-redis redis-cli info stats 2>/dev/null | grep "total_commands_processed" | cut -d: -f2 | tr -d '\r' || echo "N/A")
        print_message $YELLOW "Redis总命令数: $total_commands"
    else
        print_message $YELLOW "Redis服务未启用"
    fi
}

# 性能测试
performance_test() {
    print_message $BLUE "=== 性能测试 ==="
    
    # API响应时间测试
    print_message $YELLOW "API响应时间测试:"
    for i in {1..5}; do
        if command -v curl >/dev/null 2>&1; then
            response_time=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:5001/health 2>/dev/null || echo "N/A")
            print_message $YELLOW "  请求 $i: ${response_time}s"
        else
            print_message $RED "curl命令未找到，跳过响应时间测试"
            break
        fi
    done
}

# 查看日志
view_logs() {
    print_message $BLUE "=== 服务日志 ==="
    
    echo ""
    print_message $YELLOW "后端服务日志 (最近20行):"
    docker logs --tail 20 ${PROJECT_NAME}-backend 2>/dev/null || print_message $RED "无法获取后端日志"
    
    echo ""
    print_message $YELLOW "前端服务日志 (最近10行):"
    docker logs --tail 10 ${PROJECT_NAME}-frontend 2>/dev/null || print_message $RED "无法获取前端日志"
    
    if docker ps | grep -q "${PROJECT_NAME}-redis"; then
        echo ""
        print_message $YELLOW "Redis服务日志 (最近10行):"
        docker logs --tail 10 ${PROJECT_NAME}-redis 2>/dev/null || print_message $RED "无法获取Redis日志"
    fi
}

# 实时监控模式
realtime_monitor() {
    print_message $BLUE "实时监控模式 (按Ctrl+C退出)"
    
    while true; do
        clear
        print_message $BLUE "征信管理系统实时监控 - $(date)"
        echo "=================================="
        
        # 服务状态
        print_message $YELLOW "服务状态:"
        docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(backend|frontend|redis|NAMES)" || print_message $RED "无服务运行"
        
        echo ""
        
        # 资源使用
        print_message $YELLOW "资源使用:"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep -E "(backend|frontend|redis|CONTAINER)" || print_message $RED "无容器运行"
        
        echo ""
        
        # 健康检查
        print_message $YELLOW "健康状态:"
        if curl -s http://localhost:5001/health >/dev/null 2>&1; then
            print_message $GREEN "✓ 系统健康"
        else
            print_message $RED "✗ 系统异常"
        fi
        
        sleep 5
    done
}

# 显示菜单
show_menu() {
    print_message $BLUE "征信管理系统监控工具"
    echo "=================================="
    echo "1. 服务状态检查"
    echo "2. 资源使用监控"
    echo "3. Redis性能监控"
    echo "4. 性能测试"
    echo "5. 查看服务日志"
    echo "6. 实时监控模式"
    echo "7. 全面检查"
    echo "0. 退出"
    echo ""
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        while true; do
            show_menu
            read -p "请选择 (0-7): " choice
            
            case $choice in
                1) check_services ;;
                2) monitor_resources ;;
                3) monitor_redis ;;
                4) performance_test ;;
                5) view_logs ;;
                6) realtime_monitor ;;
                7) 
                    check_services
                    echo ""
                    monitor_resources
                    echo ""
                    monitor_redis
                    echo ""
                    performance_test
                    ;;
                0) print_message $GREEN "退出监控"; exit 0 ;;
                *) print_message $RED "无效选项" ;;
            esac
            
            echo ""
            print_message $YELLOW "按Enter继续..."
            read
        done
    else
        case $1 in
            "check") check_services ;;
            "resources") monitor_resources ;;
            "redis") monitor_redis ;;
            "test") performance_test ;;
            "logs") view_logs ;;
            "realtime") realtime_monitor ;;
            "all")
                check_services
                echo ""
                monitor_resources
                echo ""
                monitor_redis
                echo ""
                performance_test
                ;;
            *) 
                echo "用法: $0 [check|resources|redis|test|logs|realtime|all]"
                echo "或直接运行 $0 进入交互模式"
                ;;
        esac
    fi
}

# 执行主函数
main "$@"
