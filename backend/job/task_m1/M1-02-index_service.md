# M1-02：索引模板 index_service

## Agent 角色

Elasticsearch 索引模板专项 Agent — **仅实现 composable / index template 的创建与幂等管理**。

## 唯一负责文件

```
app/services/elasticsearch/index_service.py
```

## 禁止修改

- `field_catalog.py`、`aggregation_service.py`、`context_service.py`
- `app/tasks/init_indices.py`（由 M1-03 负责，仅调用本模块公开函数）
- `client.py`（复用 `get_es_client()`，不修改其实现）

## 前置依赖

- 可与 M1-01 并行
- 只读参考：`schemas/log.py` 公共字段与 7 类专有字段

## 开发要求

### 1. 保留并使用的模块常量

- `INDEX_PREFIX = "app-logs"`
- `LOG_TYPES`：7 类列表（可保留现有）

### 2. 必须实现的函数

| 函数 | 职责 |
| --- | --- |
| `create_component_templates()` | PUT 8 个 component template：`logs-common` + 7 类专有 |
| `create_index_templates()` | PUT 7 个 index template，pattern 为 `app-logs-{log_type}-*` |
| `create_analysis_indices()` | PUT `analysis-results-*`、`alerts-*` 的最小 mapping 模板（供 M4/M5 预留） |
| `init_all_indices()` | 顺序调用上述三步，汇总 `{ok, steps: [...]}` |
| `verify_templates()` | 只读检查关键模板是否存在，返回 `{ok, missing: []}` |

### 3. Mapping 约定

- 枚举 / 维度字段 → `keyword`
- 耗时、计数、指标 → `long` 或 `float`
- `message` → `text` + fields.keyword
- `timestamp` → `date`
- 公共字段至少覆盖：`log_id`、`log_level`、`log_type`、`event_type`、`service_name`、`trace_id`、`user_id`、`status`

实现方式：在 `index_service.py` 内用 Python dict 定义 mapping JSON，通过 `get_es_client()` 调用 ES Indices API。

### 4. 错误与权限处理

- ES 不可达、401/403、无 `manage_index_templates` 权限：返回 `{ok: false, error: "可诊断中文/英文信息"}`，**不向调用方抛未捕获异常**
- 模板已存在：幂等更新或跳过，第二次 `init_all_indices()` 不得失败
- 删除所有 `placeholder: true` 返回

### 5. 实现约束

- 不修改 `core/config.py`；ES 连接仅用现有 `get_es_client()`
- 不写 CLI；任务入口由 M1-03 负责

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 本地 ES 在线 | `init_all_indices()` 返回 `ok: true`，`steps` 长度为 3 |
| AC-02 | 模板可查 | `verify_templates()` 的 `missing` 为空 |
| AC-03 | application 模板 | ES `GET _index_template/app-logs-application` 存在且 index_patterns 含 `app-logs-application-*` |
| AC-04 | 分析索引预留 | `analysis-results`、`alerts` 相关模板存在 |
| AC-05 | 幂等 | 连续调用 `init_all_indices()` 两次均 `ok: true` |
| AC-06 | ES 离线 | `init_all_indices()` 返回 `ok: false` 且含 `error`，进程不崩溃 |
| AC-07 | 无占位 | 返回值不含 `placeholder: true` |

## 完成定义（DoD）

- [ ] 仅修改 `index_service.py`
- [ ] 公开函数签名与上表一致
- [ ] AC-01~AC-07 通过（AC-01/03 在 ES 可用环境执行）
- [ ] 不修改 DEV.md

## 下游消费说明

- M1-03 的 `init_indices.py` 将 **仅** 调用 `init_all_indices()`，不得复制 mapping 定义
