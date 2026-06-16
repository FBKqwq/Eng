# Alert 持久化域 DEV 文档

## 1. 文档用途说明
维护 `app/services/alert/` 预警写入、查询与去重，目标索引 `alerts-*`。

## 2. 模块总览
| 文件 | 职责 | 状态 |
|---|---|---|
| `alert_service.py` | write_alert / list_active_alerts / acknowledge_alert | 占位 |
| `dedup.py` | check_duplicate / 幂等键构建 | 占位 |

## 3. API 对接
- `GET /api/v1/alerts/active` → `list_active_alerts`
- `POST /api/v1/alerts/{id}/ack` → `acknowledge_alert`

## 4. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| Alert 域 | 占位 | 2026-06-16 | elk-backend-agent | 高 | alerts-* 索引未建 |

## 5. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-06-16 | 建立 alert 占位 + alerts API | `alert_service.py`、`dedup.py`、`api/v1/alerts.py`、`schemas/alert.py` | API 可访问，返回 placeholder | 待 M5 实现去重与持久化 |
