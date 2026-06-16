# M1-05：上下文服务 context_service

## Agent 角色

Elasticsearch 诊断上下文专项 Agent — **仅实现四个受控上下文查询入口**。

## 唯一负责文件

```
app/services/elasticsearch/context_service.py
```

## 禁止修改

- `log_query_service.py`（含 `search_recent_context`，**本任务不得改动**）
- `diagnosis/analyzer.py`
- `aggregation_service.py`、`field_catalog.py`（可 import `resolve_index_pattern`）

## 前置依赖

- **M1-01 完成**：`resolve_index_pattern` 可用
- 可与 M1-04 并行

## 开发要求

### 1. 必须实现的四个函数

#### `get_trace_context(trace_id: str, *, limit: int = 50) -> dict`

- 跨日志索引查询 `trace_id` 精确匹配
- 按 `timestamp` 升序
- 返回：`{available, error?, items, total, took_ms?}`
- `items` 元素结构与 `log_query_service` 的 item 字段尽量一致（log_id、timestamp、service_name、message、error_code 等）

#### `get_service_window(service: str, start: datetime, end: datetime, *, limit: int = 50) -> dict`

- 过滤 `service_name` + 时间范围
- ERROR/WARN 优先：可通过 sort（log_level 权重）或两次查询合并
- 额外返回：`level_distribution: dict[str, int]`（如 `{"ERROR": 3, "INFO": 10}`）

#### `get_similar_errors(error_code: str, start: datetime, end: datetime, *, limit: int = 50) -> dict`

- 过滤 `error_code` + 时间范围
- 返回：`total`、`by_service: [{key, count}]`、`time_histogram: [{key, count}]`（可用 ES 聚合实现）

#### `get_user_recent_actions(user_id: str, start: datetime, end: datetime, *, limit: int = 50) -> dict`

- 查询 `behavior` + `application` 索引（`resolve_index_pattern`）
- 过滤 `user_id` + 时间范围，按时间升序
- 返回 `items`、`total`

### 2. 通用约束

| 约束 | 值 |
| --- | --- |
| `limit` 硬上限 | 50 |
| 时间窗口最大跨度 | 24 小时 |
| ES 超时 | 与 `log_query_service` 一致（约 2s，可提取常量或本文件定义 `CONTEXT_QUERY_TIMEOUT_SECONDS = 2`） |
| ES 失败 | `available: false` + `error` + 空集合，不抛到 API |

### 3. 与 search_recent_context 的关系

- **不得**修改 `search_recent_context` 去调用本模块（避免改 `log_query_service.py`）
- 本模块独立实现 trace 查询能力；后续集成由 M1-11 或 diagnosis 改造任务处理
- 在模块 docstring 注明：诊断模块未来应迁移至本 service

### 4. 删除占位

- 移除 `_PLACEHOLDER` 及所有 `placeholder: true`

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | trace | 同一 `trace_id` ≥3 条日志时，`get_trace_context` 返回 ≥3 条且时间递增 |
| AC-02 | service 窗口 | `get_service_window` 仅含指定 service；有 ERROR 时 `level_distribution["ERROR"] >= 1` |
| AC-03 | 同类错误 | 5 条相同 `error_code` 时 `get_similar_errors.total >= 5` |
| AC-04 | 用户行为 | 同 `user_id` 的 behavior/application 日志可拉回 |
| AC-05 | 空结果 | 不存在 trace 时 `items=[]`, `total=0`，不异常 |
| AC-06 | limit | `limit=200` 被截断为 50 |
| AC-07 | ES 离线 | `available=False` |
| AC-08 | 无占位 | 无 `placeholder: true` |

**数据提示**：若 simulation 尚未 trace 链路化，可临时用相同 `trace_id` 手动构造 3 条 Kafka 日志验证 AC-01。

## 完成定义（DoD）

- [ ] 仅修改 `context_service.py`
- [ ] 四个函数全部实现
- [ ] AC-01~AC-08 通过
- [ ] 未修改 `log_query_service.py`

## 下游说明

- M1-10 编写 `tests/test_m1_context_service.py`
- M5 `graph_rule` 的 `fetch_context` 节点将经 tools 调用本模块
