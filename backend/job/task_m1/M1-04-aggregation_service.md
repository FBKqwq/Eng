# M1-04：聚合服务 aggregation_service

## Agent 角色

Elasticsearch 聚合专项 Agent — **仅实现六类受控聚合模板与统一入口**。

## 唯一负责文件

```
app/services/elasticsearch/aggregation_service.py
```

## 禁止修改

- `field_catalog.py`（只 import 调用，缺函数则阻塞并反馈 M1-01）
- `log_query_service.py`、`context_service.py`、`index_service.py`
- `api/v1/logs.py`（由 M1-06 挂载路由）
- `schemas/log.py`

## 前置依赖

- **M1-01 必须完成**：`validate_aggregate_request`、`resolve_index_pattern` 可用
- 建议 M1-02 完成（拆索引未生效时可回退 `settings.elasticsearch_index_pattern`）

## 开发要求

### 1. 统一入口

```python
def aggregate(request: LogAggregateRequest) -> dict:
    """
    入参：schemas.log.LogAggregateRequest（只读使用，不修改 schema）
    出参：可映射为 LogAggregateResponse 的 dict
    """
```

流程：

1. 校验 `end_time > start_time`，窗口跨度 ≤ 24 小时（超出返回 `ok=False` 或 `available=False`）
2. 调用 `field_catalog.validate_aggregate_request`
3. `top_n = min(request.top_n, 50)`
4. `resolve_index_pattern` 解析索引
5. 组装 DSL，`size: 0`，`client.search(..., aggs=...)`
6. 解析为 `{group_by, interval, buckets, took_ms, available: true}`

### 2. 六类模板函数（必须全部实现）

| 函数 | 目标 log_type | 要点 |
| --- | --- | --- |
| `aggregate_traffic` | application + web_server | date_histogram + 文档计数 |
| `aggregate_errors` | application + web_server | 错误 filter + terms(error_code/status_code) |
| `aggregate_latency` | application + web_server + performance | percentiles + terms 嵌套（p50/p95/p99） |
| `aggregate_behavior_funnel` | behavior | 按 funnel_steps 逐步 filter count + 转化率 |
| `aggregate_security` | security | terms(risk_level) 等 |
| `aggregate_infra_health` | infrastructure + performance | terms(component) + avg(metric) |

各模板函数签名保持 `**kwargs` 或显式 `(start_time, end_time, top_n=10, ...)`，内部可委托 `aggregate()` 或共享 `_run_agg` 私有函数（私有函数写在**本文件内**）。

### 3. 实现铁律

1. **不接受裸 DSL** 作为公开 API 参数
2. 全部聚合 `size: 0`
3. `terms.size = min(top_n, 50)`
4. 时间直方图：`date_histogram` + `fixed_interval`，映射 `TimeInterval`（`1m`/`1h`/`1d`）
5. 多 log_type **单次多索引查询**，禁止两次查询内存合并
6. ES 异常返回风格：

```python
{
    "available": False,
    "error": str,
    "group_by": ...,
    "interval": ...,
    "buckets": [],
    "took_ms": None,
}
```

7. 删除所有 `placeholder: true`

### 4. 依赖导入（允许）

```python
from app.schemas.log import LogAggregateRequest, LogType, TimeInterval
from app.services.elasticsearch.client import get_es_client
from app.services.elasticsearch import field_catalog  # 或具体函数 import
from app.core.config import settings
```

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | traffic | ES 有数据时 `aggregate_traffic` 返回 `available=True` 且 buckets 非空 |
| AC-02 | errors | 存在 ERROR 日志时 `aggregate_errors` 有 error_code 或 status 分布 |
| AC-03 | latency | `aggregate_latency` 含 p95/p99 或等价 extra |
| AC-04 | funnel | 有 behavior 日志时五步均有 count |
| AC-05 | security/infra | 结构正确；无数据时 buckets 为空但不报错 |
| AC-06 | 白名单 | 对 `message` 做 terms 聚合时**服务层拒绝**，请求不到 ES |
| AC-07 | top_n | `top_n=100` 被限制为 50 |
| AC-08 | ES 离线 | `available=False`，不 500 |
| AC-09 | 契约 | 成功响应含 `group_by`、`buckets`、`took_ms` |
| AC-10 | 无占位 | 无 `placeholder: true` |

**数据准备**：`python -m app.tasks.run_log_producer --count 200`

## 完成定义（DoD）

- [ ] 仅修改 `aggregation_service.py`
- [ ] 六模板 + `aggregate()` 全部实现
- [ ] AC-01~AC-10 在 ELK 环境验证通过
- [ ] 不修改 DEV.md

## 下游说明

- M1-06 将添加 `POST /api/v1/logs/aggregate` 调用 `aggregate()`
- M1-09 将编写 `tests/test_m1_aggregation_service.py`
