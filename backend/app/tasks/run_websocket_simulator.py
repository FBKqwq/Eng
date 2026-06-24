"""WebSocket 模拟数据推送任务"""
import asyncio
import random
import json
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.api.v1.ws import send_alert_message, send_log_message, send_system_message


async def generate_alert():
    """生成模拟告警数据"""
    alert_levels = ["critical", "warning", "info"]
    alert_types = ["系统异常", "性能告警", "安全威胁", "日志异常"]
    
    return {
        "id": f"alert-{random.randint(1000, 9999)}",
        "level": random.choice(alert_levels),
        "type": random.choice(alert_types),
        "message": f"检测到{random.choice(['高CPU使用率', '内存不足', '网络延迟', '服务异常'])}",
        "service": random.choice(["kafka", "elasticsearch", "logstash", "backend"]),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "count": random.randint(1, 100)
    }


async def generate_log():
    """生成模拟日志数据"""
    log_levels = ["INFO", "WARN", "ERROR", "DEBUG"]
    log_sources = ["app-server", "web-server", "api-gateway", "database"]
    
    return {
        "id": f"log-{random.randint(100000, 999999)}",
        "level": random.choice(log_levels),
        "source": random.choice(log_sources),
        "message": f"Request processed in {random.randint(10, 500)}ms",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": f"trace-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
    }


async def generate_system_status():
    """生成模拟系统状态数据"""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "kafka": {
            "status": "online",
            "active_partitions": random.randint(1, 10),
            "messages_per_second": random.randint(100, 1000)
        },
        "elasticsearch": {
            "status": "online",
            "documents": random.randint(100000, 1000000),
            "health": "green"
        },
        "logstash": {
            "status": "online",
            "pipeline_rate": random.randint(50, 500)
        }
    }


async def run_simulator():
    """运行模拟数据推送"""
    print("WebSocket 模拟器启动...")
    try:
        while True:
            # 随机推送告警
            if random.random() < 0.3:
                alert = await generate_alert()
                await send_alert_message(alert)
                print(f"推送告警: {alert['type']} - {alert['message']}")
            
            # 随机推送日志
            if random.random() < 0.5:
                log = await generate_log()
                await send_log_message(log)
                print(f"推送日志: {log['level']} - {log['source']}")
            
            # 定期推送系统状态
            if random.random() < 0.1:
                status = await generate_system_status()
                await send_system_message(status)
                print("推送系统状态")
            
            await asyncio.sleep(2)
    except KeyboardInterrupt:
        print("WebSocket 模拟器停止")


if __name__ == "__main__":
    asyncio.run(run_simulator())