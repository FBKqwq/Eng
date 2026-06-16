# M1-01：字段目录 field_catalog

## Agent 角色

Elasticsearch 字段目录专项 Agent — **仅实现 80+ 日志类型的声明式字段白名单**。

## 唯一负责文件

```
app/services/elasticsearch/field_catalog.py
```

## 禁止修改

- `aggregation_service.py`、`context_service.py`、`index_service.py`
- `api/`、`schemas/`、`tasks/`
- 任何其他文件（含 `DEV.md`，由 M1-11 统一维护）

## 前置依赖

- 无（本任务为 M1 第一站，可与 M1-02 并行）
- 须阅读：`schemas/log.py` 中 7 类 Log 模型与枚举（只读参考）

## 开发要求

### 1. 全量注册 `FIELD_CATALOG`

为以下 7 个 `log_type` 各建一条目录项：

`behavior` | `application` | `web_server` | `performance` | `security` | `infrastructure` | `audit`

每条至少包含：

| 键 | 说明 |
| --- | --- |
| `filter_fields` | 可用于 bool filter 的字段列表 |
| `terms_fields` | 允许 terms 聚合的 keyword 维度 |
| `metric_fields` | 允许 avg/sum/percentiles 的数值字段 |
| `trace_capable` | bool，是否支持 trace 查询 |
| `user_capable` | bool，是否支持 user_id 查询 |

**类专有扩展**（必须实现）：

- `behavior`：增加 `funnel_steps` 列表，顺序为  
  `page_view` → `product_click` → `add_to_cart` → `checkout_click` → `pay_button_click`
- `web_server`：覆盖 Nginx 常见 terms/metric（如 `request_uri`、`status_code`、`request_time`、`upstream_response_time`）
- `security`：含 `risk_level`、`rule_id` 等
- `infrastructure`：含 `component`、`resource_type` 及 lag 相关字段

字段名须与 `schemas/log.py` 及 `simulation/log_generator.py` 产出字段对齐。

### 2. 必须实现的函数

```python
def get_catalog_for_log_type(log_type: str) -> dict[str, Any]:
    """已知类型返回完整目录；未知类型返回 ok=False 与明确 message，不含 placeholder 键。"""

def list_registered_log_types() -> list[str]:
    """固定返回 7 个 log_type。"""

def validate_aggregate_field(log_type: str, field: str, field_kind: str) -> bool:
    """field_kind 取值：filter | terms | metric。"""

def resolve_index_pattern(log_types: list[str] | None = None) -> str:
    """
    将 log_type 列表转为 ES index pattern。
    - None 或空列表 → 使用 settings.elasticsearch_index_pattern（从 config 读取）
    - 单类型 → app-logs-{log_type}-*
    - 多类型 → 逗号拼接，如 app-logs-application-*,app-logs-web-server-*
  回退：若拆索引尚未生效，可同时兼容 app-logs-*（在文档字符串说明行为）。
    """

def validate_aggregate_request(
    log_types: list[str] | None,
    group_by: str,
    metric_field: str | None = None,
) -> dict[str, Any]:
    """
    返回 {"ok": bool, "errors": list[str]}。
    校验 group_by 在 terms_fields 内；metric_field 在 metric_fields 内。
    log_types 为空时，group_by 须在任一类 catalog 的 terms_fields 并集内。
    """
```

### 3. 实现约束

- 删除现有占位常量 `_PLACEHOLDER` 及所有 `placeholder: true` 返回。
- 不发起 ES 请求；纯声明与校验逻辑。
- 所有中文注释使用简体中文。

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 类型覆盖 | `list_registered_log_types()` 长度 = 7 |
| AC-02 | behavior 漏斗 | `get_catalog_for_log_type("behavior")["funnel_steps"]` 含 5 步且顺序正确 |
| AC-03 | 非法 terms | `validate_aggregate_field("application", "message", "terms")` 为 `False` |
| AC-04 | 合法 terms | `validate_aggregate_field("application", "error_code", "terms")` 为 `True` |
| AC-05 | 索引 pattern | `resolve_index_pattern(["application","web_server"])` 含两个 pattern 片段 |
| AC-06 | 批量校验 | `validate_aggregate_request(..., group_by="message")` 返回 `ok=False` |
| AC-07 | import | `python -c "from app.services.elasticsearch.field_catalog import FIELD_CATALOG; assert len(FIELD_CATALOG)==7"` 成功 |

## 完成定义（DoD）

- [ ] 仅修改 `field_catalog.py`
- [ ] 7 类目录完整，无 placeholder
- [ ] 上述 7 项验收全部通过
- [ ] 不修改 DEV.md（交给 M1-11）

## 下游消费说明（供其他 Agent 只读）

- M1-04 `aggregation_service` 将调用 `validate_aggregate_request`、`resolve_index_pattern`
- M1-06 `GET /logs/fields` 将调用 `get_catalog_for_log_type`
