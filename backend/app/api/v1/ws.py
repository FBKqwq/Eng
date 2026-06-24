from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
import asyncio
import json
from typing import Dict, List, Set
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 存储 WebSocket 连接
active_connections: Dict[str, Set[WebSocket]] = {
    "alerts": set(),
    "logs": set(),
    "system": set()
}


class ConnectionManager:
    def __init__(self, channel: str):
        self.channel = channel
        self.active_connections: Set[WebSocket] = active_connections[channel]

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected to {self.channel} channel. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected from {self.channel} channel. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """向所有连接的客户端广播消息"""
        message_str = json.dumps(message)
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Failed to send message to connection: {e}")
                disconnected.append(connection)
        
        # 移除断开的连接
        for conn in disconnected:
            self.disconnect(conn)


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    manager = ConnectionManager("alerts")
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error in alerts channel: {e}")
        manager.disconnect(websocket)


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    manager = ConnectionManager("logs")
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error in logs channel: {e}")
        manager.disconnect(websocket)


@router.websocket("/ws/system")
async def websocket_system(websocket: WebSocket):
    manager = ConnectionManager("system")
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error in system channel: {e}")
        manager.disconnect(websocket)


async def send_alert_message(alert_data: dict):
    """发送告警消息到所有连接的客户端"""
    manager = ConnectionManager("alerts")
    message = {
        "type": "alert",
        "data": alert_data,
        "timestamp": alert_data.get("timestamp", "")
    }
    await manager.broadcast(message)


async def send_log_message(log_data: dict):
    """发送日志消息到所有连接的客户端"""
    manager = ConnectionManager("logs")
    message = {
        "type": "log",
        "data": log_data,
        "timestamp": log_data.get("timestamp", "")
    }
    await manager.broadcast(message)


async def send_system_message(system_data: dict):
    """发送系统状态消息到所有连接的客户端"""
    manager = ConnectionManager("system")
    message = {
        "type": "system",
        "data": system_data,
        "timestamp": system_data.get("timestamp", "")
    }
    await manager.broadcast(message)