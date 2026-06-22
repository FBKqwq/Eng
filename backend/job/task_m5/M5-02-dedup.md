# M5-02：预警去重 dedup

## Agent 角色

去重幂等 Agent — 基于幂等键查重，重复时累加 evidence_count。

## 唯一负责文件

```
app/services/alert/dedup.py
```

## 禁止修改

- `alert_service.py`（可 import 查询函数，不改其实现）
- `tools/alert_tools.py`、其他文件

## 前置依赖

- M1 完成（`alerts-*` 模板就绪）

## 开发要求

### 1. `build_idempotency_key(alert_candidate, *, bucket_minutes=10) -> str`
- 幂等键 = `alert_type + affected_service + 时间桶`
- 时间桶：将 `created_at`/now 向下取整到 `bucket_minutes` 粒度

### 2. `check_duplicate(alert_candidate, *, bucket_minutes=10) -> dict`
- 用幂等键查询 `alerts-*` 是否已存在同桶预警
- 命中：`{"ok": True, "is_duplicate": True, "existing_alert_id": ..., "idempotency_key": ...}`，并可累加 `evidence_count`（或返回供 scanner 决策）
- 未命中：`{"ok": True, "is_duplicate": False, "existing_alert_id": None, "idempotency_key": ...}`
- 异常结构化返回；**无 placeholder**

### 3. 约定
- 通过 `get_es_client` 查询，不抛裸异常
- 与 `alert_service` 协作：去重判定在写入前

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `build_idempotency_key` 同输入稳定、同桶一致 |
| AC-02 | `check_duplicate` 命中/未命中均结构化返回 |
| AC-03 | 无 placeholder；异常不抛裸异常 |
| AC-04 | 更新 `task_m5/STATUS.md` 本行 |
