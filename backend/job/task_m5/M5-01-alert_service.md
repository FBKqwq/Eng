# M5-01：预警持久化 alert_service

## Agent 角色

预警持久化 Agent — 实现 `alerts-*` 索引读写与状态机。

## 唯一负责文件

```
app/services/alert/alert_service.py
```

## 禁止修改

- `index_service.py`（`alerts-*` 模板已就绪，只 import `get_es_client`）
- `dedup.py`、`tools/alert_tools.py`（M2 已薄包装）
- 其他文件

## 前置依赖

- M1 完成（`create_analysis_indices` 已建 `alerts-*` 模板）
- 必读：`elasticsearch/client.py`、`schemas/alert.py`、`index_service._alerts_properties`（只读）

## 开发要求

### 1. `write_alert(alert: dict) -> dict`
- 生成 `alert_id`、`created_at`/`updated_at`，默认 `status=active`、`evidence_count=1`
- 写入 `alerts-*`；返回 `{"ok": True, "alert_id": ...}`；异常结构化错误
- 可选：若传入 `existing_alert_id`，改为更新 evidence_count 与 updated_at（与 dedup 协作；也可由 dedup 负责累加）

### 2. `list_active_alerts(limit=50) -> dict`
- 查询 `status=active`，按 `updated_at` 倒序；返回 `{"ok": True, "items": [...], "total": n, "limit": limit}`

### 3. `acknowledge_alert(alert_id, operator=None) -> dict`
- 将状态 `active → acknowledged`，记录 operator 与时间；未命中结构化返回

### 4. 约定
- ES 错误风格沿用 `log_query_service`；不抛裸异常；去除 placeholder

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | 三函数无 placeholder 键 |
| AC-02 | `write_alert` 返回 alert_id；mock ES 验证 index 调用 |
| AC-03 | `list_active_alerts` 仅返回 active；结构含 items/total |
| AC-04 | `acknowledge_alert` 状态流转正确 |
| AC-05 | 更新 `task_m5/STATUS.md` 本行 |
