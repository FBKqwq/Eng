# M1-06：日志 API 扩展 logs_api

## Agent 角色

API 层专项 Agent — **仅在 logs 路由挂载聚合接口并完善字段目录接口**。

## 唯一负责文件

```
app/api/v1/logs.py
```

## 禁止修改

- `aggregation_service.py`、`field_catalog.py`（只 import）
- `schemas/log.py`
- `router.py`（logs 路由已挂载，无需改 router 除非新增路由前缀错误 — 一般不需要）

## 前置依赖

- **M1-01 完成**：`get_catalog_for_log_type`、`list_registered_log_types`
- **M1-04 完成**：`aggregate()` 非占位

## 开发要求

### 1. 保留现有接口

- `POST /search` → `search_logs`（不得破坏）

### 2. 完善 `GET /fields`

当前已有占位实现，需调整为：

| 场景 | 响应 |
| --- | --- |
| 带 `log_type` | `{ok: true, log_type, catalog}`；catalog 来自 M1-01，**无 placeholder** |
| 不带 `log_type` | `{ok: true, registered_log_types: [...]}` 列出 7 类 |

未知 `log_type`：`ok: false` + 明确 `message`，HTTP 200（与项目现有风格一致）或 404（二选一，须在实现中统一并写入本任务完成备注）。

### 3. 新增 `POST /aggregate`

```python
@router.post("/aggregate")
def log_aggregate(payload: LogAggregateRequest) -> dict:
    return aggregate(payload)
```

- 入参：`LogAggregateRequest`（`from app.schemas.log import LogAggregateRequest`）
- 调用：`from app.services.elasticsearch.aggregation_service import aggregate`
- 路由层**不写 DSL、不写业务逻辑**，仅校验 + 转发

### 4. 实现约束

- 本文件行数保持精简（目标 < 60 行）
- 不得在本文件定义 Pydantic 模型

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | fields | `GET /api/v1/logs/fields?log_type=application` → `ok=true`，catalog 含 terms_fields |
| AC-02 | fields 列表 | `GET /api/v1/logs/fields` → `registered_log_types` 长度 7 |
| AC-03 | aggregate | `POST /api/v1/logs/aggregate` 合法 body 返回 buckets 结构 |
| AC-04 | search 回归 | `POST /api/v1/logs/search` 仍正常 |
| AC-05 | 无占位 | 响应不含 `placeholder: true` |
| AC-06 | TestClient | `from fastapi.testclient import TestClient` 调用 AC-01~AC-03 通过 |

### `POST /aggregate` 验收用例 body 示例

```json
{
  "start_time": "2026-06-16T00:00:00Z",
  "end_time": "2026-06-16T23:59:59Z",
  "group_by": "service_name",
  "top_n": 10
}
```

## 完成定义（DoD）

- [ ] 仅修改 `app/api/v1/logs.py`
- [ ] AC-01~AC-06 通过
- [ ] 不修改 DEV.md

## 下游说明

- 前端日志筛选器消费 `GET /fields`
- 监控页 / 分析页后续消费 `POST /aggregate`
