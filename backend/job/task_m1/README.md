# M1 数据底座完善 — Agent 任务编排说明

> 对应总体规划：`doc/后端开发总体规划-Services-LangGraph-MCP.md` §1.2、§4（里程碑 M1）  
> 目标：field_catalog + index_service + aggregation_service + context_service 真实落地  
> 原则：**一个 Agent 只负责一个主脚本**，避免多人同时改同一文件造成冲突

---

## 1. 任务清单与文件归属

| 任务编号 | 文档 | 唯一负责脚本 | 禁止修改 |
| --- | --- | --- | --- |
| M1-01 | [M1-01-field_catalog.md](./M1-01-field_catalog.md) | `app/services/elasticsearch/field_catalog.py` | 其他所有文件 |
| M1-02 | [M1-02-index_service.md](./M1-02-index_service.md) | `app/services/elasticsearch/index_service.py` | 其他所有文件 |
| M1-03 | [M1-03-init_indices.md](./M1-03-init_indices.md) | `app/tasks/init_indices.py`（新建） | 其他所有文件 |
| M1-04 | [M1-04-aggregation_service.md](./M1-04-aggregation_service.md) | `app/services/elasticsearch/aggregation_service.py` | 其他所有文件 |
| M1-05 | [M1-05-context_service.md](./M1-05-context_service.md) | `app/services/elasticsearch/context_service.py` | 其他所有文件 |
| M1-06 | [M1-06-logs_api.md](./M1-06-logs_api.md) | `app/api/v1/logs.py` | 其他所有文件 |
| M1-07 | [M1-07-test_field_catalog.md](./M1-07-test_field_catalog.md) | `tests/test_m1_field_catalog.py`（新建） | 其他所有文件 |
| M1-08 | [M1-08-test_index_service.md](./M1-08-test_index_service.md) | `tests/test_m1_index_service.py`（新建） | 其他所有文件 |
| M1-09 | [M1-09-test_aggregation_service.md](./M1-09-test_aggregation_service.md) | `tests/test_m1_aggregation_service.py`（新建） | 其他所有文件 |
| M1-10 | [M1-10-test_context_service.md](./M1-10-test_context_service.md) | `tests/test_m1_context_service.py`（新建） | 其他所有文件 |
| M1-11 | [M1-11-dev_docs.md](./M1-11-dev_docs.md) | `app/services/elasticsearch/DEV.md`、`app/tasks/DEV.md` | 业务代码文件 |

---

## 2. 推荐执行顺序

```text
阶段 A（可并行）
  M1-01 field_catalog
  M1-02 index_service

阶段 B（依赖 A-02）
  M1-03 init_indices        ← 仅 import 调用 index_service，不改 index_service.py

阶段 C（依赖 A-01；建议 A-02 完成后）
  M1-04 aggregation_service
  M1-05 context_service     ← 与 M1-04 可并行，但互不改对方文件

阶段 D（依赖 C-04、A-01）
  M1-06 logs_api            ← 挂载 POST /aggregate，完善 GET /fields

阶段 E（与各 Service 任务配对，可并行）
  M1-07 ~ M1-10 测试脚本   ← 在对应 Service 合并后再跑

阶段 F（全部完成后）
  M1-11 dev_docs            ← 统一收敛 DEV 文档，避免多人改 DEV.md
```

---

## 3. 跨任务约定（所有 Agent 必须遵守）

1. **只改自己负责的脚本**；需要别人提供的函数时，按接口约定调用，不得越权修改。
2. **不得修改** `schemas/log.py`（契约已完整）；缺字段先在本任务文档记录，由人工决策是否开新任务。
3. ES 错误返回风格对齐 `log_query_service.search_logs()`：`available: false` + `error` + 空集合字段。
4. 完成后响应/返回值中**不得再含** `placeholder: true`（测试 mock 除外）。
5. `search_recent_context()` 留在 `log_query_service.py`，**M1-05 不得修改该文件**；诊断兼容由 context_service 独立实现同等能力。
6. 索引 pattern 解析统一调用 `field_catalog.resolve_index_pattern()`（由 M1-01 提供）。

---

## 4. M1 总体验收（全部任务完成后）

- [ ] 7 类 `FIELD_CATALOG` 注册完整
- [ ] `python -m app.tasks.init_indices` 可幂等执行
- [ ] 六类 `aggregate_*` 对真实 ES 返回正确 buckets
- [ ] 四个 `get_*` 上下文函数对真实 ES 行为正确
- [ ] `POST /api/v1/logs/aggregate` 可用
- [ ] `GET /api/v1/logs/fields?log_type=application` 无 placeholder
- [ ] `pytest tests/test_m1_*.py` 通过（ES 离线用例允许 skip）

---

## 5. 基础设施依赖声明

- Logstash 按 `log_type` 路由到 `app-logs-{log_type}-*` **不属于 M1 后端任务**；M1 验收允许继续使用 `app-logs-*` 单索引 pattern 作为回退。
- ES 账号需具备索引模板管理权限，否则 M1-02/M1-03 验收走「结构化失败」路径。
