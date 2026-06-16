# M2 工具层成型 — 任务编排说明

> 对应总体规划：`doc/后端开发总体规划-Services-LangGraph-MCP.md` §3、§4（里程碑 **M2**）  
> 前置里程碑：**M1 数据底座完善**（`task_m1/STATUS.md` 须全部为 `已完成`/`已合并`）  
> 原则：**一个 Agent 只负责一个主脚本**，避免并行改同一文件

---

## 1. M2 目标

将 `app/services/tools/` 从占位升级为 **第一阶段 10 个 LangChain StructuredTool** + `registry.py` 注册中心。

| 项 | 说明 |
| --- | --- |
| **里程碑验收** | 单测中 10 个工具可独立调用并返回**结构化结果**（`ok` / `error` / 业务字段）；`get_langchain_tools()` 非空 |
| **不在 M2** | FastMCP Server（`create_mcp_server`）→ **M7**；LangChain Chain / LangGraph → **M3~M6** |
| **薄适配原则** | 工具只包装 service，不重复业务逻辑；ES 异常在工具内捕获，返回 `{"ok": false, "error": ...}` |

---

## 2. 第一阶段 10 个工具清单

| # | 工具名 | 实现文件 | 包装的 service | 读写 |
| --- | --- | --- | --- | --- |
| 1 | `es_search_logs` | `elasticsearch_tools.py` | `log_query_service.search_logs` | 读 |
| 2 | `es_aggregate_metrics` | `elasticsearch_tools.py` | `aggregation_service` 六模板入口 | 读 |
| 3 | `es_get_trace_context` | `elasticsearch_tools.py` | `context_service.get_trace_context` | 读 |
| 4 | `es_get_service_window` | `elasticsearch_tools.py` | `context_service.get_service_window` | 读 |
| 5 | `es_get_similar_errors` | `elasticsearch_tools.py` | `context_service.get_similar_errors` | 读 |
| 6 | `analysis_write_report` | `report_tools.py` | `report_service.write_report` | **写** |
| 7 | `alert_write_event` | `alert_tools.py` | `alert_service.write_alert` | **写** |
| 8 | `alert_check_duplicate` | `alert_tools.py` | `alert/dedup.check_duplicate` | 读 |
| 9 | `system_health_check` | `system_tools.py` | ES + Kafka + Docker 组合 | 读 |
| 10 | `rule_match_log` | `rule_tools.py` | `rule_engine.match_log` | 读 |

**读写分离**：`get_langchain_tools(include_write_tools=False)` 默认仅暴露读类工具（1~5、8~10）；写类（6、7）供图 `persist` 节点显式传入。

---

## 3. 任务清单与文件归属

| 任务编号 | 文档 | 唯一负责脚本 | 前置依赖 |
| --- | --- | --- | --- |
| M2-01 | M2-01-elasticsearch_tools.md | `app/services/tools/elasticsearch_tools.py` | M1 完成 |
| M2-02 | M2-02-system_tools.md | `app/services/tools/system_tools.py` | M1 完成 |
| M2-03 | M2-03-rule_tools.md | `app/services/tools/rule_tools.py` | M1 完成 |
| M2-04 | M2-04-report_tools.md | `app/services/tools/report_tools.py` | M1 完成 |
| M2-05 | M2-05-alert_tools.md | `app/services/tools/alert_tools.py` | M1 完成 |
| M2-06 | M2-06-registry.md | `app/services/tools/registry.py` | M2-01~05 |
| M2-07 | M2-07-test_tools.md | `tests/test_m2_tools.py`（新建） | M2-06 |
| M2-08 | M2-08-tools_dev.md | `app/services/tools/DEV.md` | M2-06 |

**依赖说明**：

- `report_service` / `alert_service` / `rule_engine.match_log` 当前仍为**占位**，M2 工具仍须真实调用它们并返回结构化结果（可为 `ok: false`），不得再返回 `placeholder: true`。
- M2-06 需新增依赖：`langchain-core`（`StructuredTool`），写入 `requirements.txt` 由 **M2-06 Agent** 在实现 registry 时追加。

---

## 4. 推荐执行顺序

```text
阶段 A（可并行，最多 5 Agent）
├── M2-01  elasticsearch_tools.py   （工具 1~5）
├── M2-02  system_tools.py          （工具 9）
├── M2-03  rule_tools.py            （工具 10）
├── M2-04  report_tools.py          （工具 6）
└── M2-05  alert_tools.py          （工具 7、8）

阶段 B（串行，依赖 A）
└── M2-06  registry.py              （StructuredTool 注册 + get_langchain_tools）

阶段 C（串行，依赖 B）
├── M2-07  tests/test_m2_tools.py
└── M2-08  tools/DEV.md
```

---

## 5. M2 总体验收（Definition of Done）

- [ ] 10 个工具函数去除 `placeholder: true`，统一返回 `{ok: bool, ...}` 结构
- [ ] `get_langchain_tools()` 返回 9 个读工具（默认）或 10 个（`include_write_tools=True`）
- [ ] `list_registered_tool_names()` 与注册列表一致
- [ ] `pytest tests/test_m2_tools.py` 全绿（ES 离线用 mock）
- [ ] `tools/DEV.md` 状态表与开发日志已更新
- [ ] `task_m2/STATUS.md` 全部任务 `已完成`

---

## 6. 跨任务约定

1. 只改自己负责的脚本（M2-06 可改 `requirements.txt` 追加 `langchain-core`）。
2. 不得修改 `services/elasticsearch/*` 业务实现（只 import 调用）。
3. 时间窗 ≤ 24h、`limit`/`top_n` 硬上限与总体规划 §3.3 一致。
4. 工具内捕获异常，不向调用方抛裸异常。
5. 中文注释与文档使用简体中文。
6. 进度维护见 `task_m2/STATUS.md`；派发 Prompt 见 `PROMPT_DISPATCH.md`。

---

## 7. 与后续里程碑关系

```text
M1（已完成）→ M2（本目录）→ M3 LangChain 能力层
                              ↘
                               M4 定时子图 / M5 规则子图（可并行，依赖 M2 工具 + M3 部分能力）
```

M2 完成后，M3 的 Chain 与 M4/M5 的图节点可通过 `registry.get_langchain_tools()` 或直调工具函数获取 ES 能力，而无需在图内拼 DSL。

---

## 8. 已知遗留（不阻塞 M2）

| 项 | 现状 | 何时收敛 |
| --- | --- | --- |
| `report_service` / `alert_service` 占位 | 工具 6、7 返回 `ok: false` 可诊断错误 | M4 / M5 |
| `rule_engine.match_log` 占位 | 工具 10 透传 service 结果 | M5 前 P1 diagnosis 改造 |
| `create_mcp_server()` | 保持占位或显式 `NotImplementedError` | M7 |
| pytest `integration` mark 未注册 | M1 遗留 warning | 可选在 M2-07 加 `pytest.ini` |
