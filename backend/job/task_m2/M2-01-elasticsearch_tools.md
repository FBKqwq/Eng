# M2-01：Elasticsearch 五工具 elasticsearch_tools

## Agent 角色

工具层 ES 读工具专项 Agent — **仅实现工具 1~5**，薄包装 M1 已完成的 ES services。

## 唯一负责文件

```
app/services/tools/elasticsearch_tools.py
```

## 禁止修改

- `services/elasticsearch/*`（只 import 调用）
- `registry.py`、其他 `tools/*.py`
- `DEV.md`（M2-08）

## 前置依赖

- M1 全部完成（`task_m1/STATUS.md`）
- 必读：`log_query_service.search_logs`、`aggregation_service.aggregate`、
  `context_service` 三个公开函数签名与返回结构

## 开发要求

### 1. 去除占位

删除 `_PLACEHOLDER` 与所有 `placeholder: true` 返回；保留并完善已有 Pydantic Input 模型。

### 2. 五个工具实现

| 工具 | 调用 |
| --- | --- |
| `es_search_logs` | 构造 `LogQueryRequest` → `search_logs` |
| `es_aggregate_metrics` | 构造 `LogAggregateRequest` → `aggregate`（六模板统一入口） |
| `es_get_trace_context` | `get_trace_context(trace_id, limit=...)` |
| `es_get_service_window` | `get_service_window(service, start, end)` |
| `es_get_similar_errors` | `get_similar_errors(error_code, start, end)` |

### 3. 统一约定

- 时间窗：入参校验跨度 ≤ 24h（与 service 一致或工具层前置校验）
- `limit` / `top_n` 硬上限 50
- `try/except` 捕获异常，返回 `{"ok": false, "error": "...", "tool": "..."}` 
- 成功时透传 service 的 `ok` 与业务字段，可加 `tool` 键便于 trace

### 4. 不得

- 在工具内拼 ES DSL
- 向调用方抛未捕获异常

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | 五函数均无 `placeholder` 键 |
| AC-02 | `es_search_logs` 入参非法时返回 `ok: false` 而非抛异常 |
| AC-03 | `es_aggregate_metrics` 六模板字面量与 `aggregation_service` 对齐 |
| AC-04 | 模块可 `import` 且无循环依赖 |
| AC-05 | 更新 `task_m2/STATUS.md` 本行 |

## 完成后

在 `task_m2/STATUS.md` 填写：状态 `已完成`、验收摘要、完成时间。
