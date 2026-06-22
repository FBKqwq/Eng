# M5-05：预警 API alerts_api

## Agent 角色

API 层 Agent — 将 `alerts.py` 从占位响应改为真实调用 `alert_service`。

## 唯一负责文件

```
app/api/v1/alerts.py
```

## 禁止修改

- `alert_service.py`（只 import）
- `schemas/alert.py`、`router.py`

## 前置依赖

- M5-01 为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.alert.alert_service import list_active_alerts, acknowledge_alert; r=list_active_alerts(limit=1); assert 'placeholder' not in r"
```

## 开发要求

### `GET /active`
- 调 `list_active_alerts(limit=...)`，按 `AlertListResponse` 返回真实 items/total，去除强制 placeholder

### `POST /{alert_id}/ack`
- 调 `acknowledge_alert(alert_id, operator=payload.operator)`，按 `AlertAckResponse` 返回真实状态

### 约定
- 薄路由：不写 ES DSL、不定义新 schema；保持响应模型契约

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `/active` 返回 service 真实结果（TestClient 验证） |
| AC-02 | `/{id}/ack` 状态流转结构化返回 |
| AC-03 | 无强制 placeholder 响应 |
| AC-04 | 更新 `task_m5/STATUS.md` 本行 |
