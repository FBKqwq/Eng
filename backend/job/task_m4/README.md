# M4 定时子图闭环 — 任务编排说明

> 对应总体规划：`doc/后端开发总体规划-Services-LangGraph-MCP.md` §2.4 / §2.8（第 3 步）/ §1.3 report 域（里程碑 **M4**）  
> 前置里程碑：**M1 数据底座** + **M2 工具层** + **M3 LangChain 能力层**（三者 STATUS 须全绿）  
> 原则：**一个 Agent 只负责一个主脚本**，避免并行改同一文件

---

## 1. M4 目标

打通**定时分析闭环**：调度器周期触发 → 定时子图（聚合→证据→报告）→ 报告持久化到 `analysis-results-*`。

| 项 | 说明 |
| --- | --- |
| **里程碑验收** | 手动/周期触发能自动写出一份**周期报告**到 `analysis-results-*`，并可通过 `GET /api/v1/reports/recent` 读取 |
| **最小版范围** | 定时子图**跳过关系发现**（`analyze_relations` 留 M7）；`generate_report` 复用 M3 `report_chain`，LLM 不可用时降级 |
| **不在 M4** | 规则子图（M5）、主图收敛与预警决策（M6）、`relation_chain`（M7）、MCP Server（M7） |

---

## 2. M4 范围与组件

| 组件 | 落点文件 | 依赖 |
| --- | --- | --- |
| 报告持久化 | `report/report_service.py` | M1 `analysis-results-*` 模板 |
| 触发标准化 | `analysis/schemas.py`（`normalize_trigger`） | — |
| 图状态 | `analysis/state.py`（`create_initial_state` + node_trace 辅助） | — |
| 定时子图最小版 | `analysis/graph_scheduled.py` | M2 工具、M3 evidence_builder/report_chain、state、schemas |
| 报告 API | `api/v1/reports.py` | report_service |
| 调度器 | `analysis/scheduler.py` | graph_scheduled、report_service |
| 调度任务入口 | `tasks/run_scheduler.py`（新建） | scheduler |

**复用（不重写）**：`aggregation_service` 六模板、`log_query_service`、`evidence_builder`、`report_chain`。

---

## 3. 任务清单与文件归属

| 任务编号 | 文档 | 唯一负责脚本 | 前置依赖 |
| --- | --- | --- | --- |
| M4-01 | M4-01-report_service.md | `app/services/report/report_service.py` | M1 完成 |
| M4-02 | M4-02-analysis_schemas.md | `app/services/analysis/schemas.py` | M3 完成 |
| M4-03 | M4-03-analysis_state.md | `app/services/analysis/state.py` | M3 完成 |
| M4-04 | M4-04-graph_scheduled.md | `app/services/analysis/graph_scheduled.py` + `requirements.txt`（langgraph） | M4-02、M4-03 |
| M4-05 | M4-05-reports_api.md | `app/api/v1/reports.py` | M4-01 |
| M4-06 | M4-06-scheduler.md | `app/services/analysis/scheduler.py` + `requirements.txt`（apscheduler） | M4-01、M4-04 |
| M4-07 | M4-07-run_scheduler.md | `app/tasks/run_scheduler.py`（新建） | M4-06 |
| M4-08 | M4-08-test_scheduled.md | `tests/test_m4_scheduled.py`（新建） | M4-04、M4-06 |
| M4-09 | M4-09-dev_docs.md | `analysis/DEV.md` + `report/DEV.md` | M4-04、M4-06 |

**依赖说明**：

- `langgraph` 由 **M4-04** 写入 `requirements.txt`；`apscheduler`（或 asyncio 方案）由 **M4-06** 写入。二者分属不同阶段，串行不冲突。
- `analysis-results-*` 索引模板已在 M1 `create_analysis_indices` 就绪，M4 不改 index_service。
- `core/config.py` 的 `analysis_schedule_minutes` 已就绪，M4 不改 config。

---

## 4. 推荐执行顺序

```text
阶段 A（可并行，3 Agent）
├── M4-01  report_service.py     报告持久化
├── M4-02  analysis/schemas.py   normalize_trigger
└── M4-03  analysis/state.py     状态 + node_trace 辅助

阶段 B（可并行，2 Agent）
├── M4-04  graph_scheduled.py（+ langgraph）   依赖 M4-02、M4-03
└── M4-05  reports_api.py                       依赖 M4-01

阶段 C（串行）
└── M4-06  scheduler.py（+ apscheduler）         依赖 M4-01、M4-04

阶段 D（可并行，3 Agent）
├── M4-07  tasks/run_scheduler.py   依赖 M4-06
├── M4-08  tests/test_m4_scheduled.py  依赖 M4-04、M4-06
└── M4-09  analysis/DEV.md + report/DEV.md  依赖 M4-04、M4-06
```

---

## 5. M4 总体验收（Definition of Done）

- [ ] `report_service` 三函数真实读写 `analysis-results-*`，去除 placeholder
- [ ] `normalize_trigger` 产出合法 `TriggerEvent`，非法触发可识别
- [ ] `run_scheduled_subgraph` 跑通：聚合→证据→报告，返回结构化报告 + `node_trace`
- [ ] 调度器可启动/停止；触发一次后 `analysis-results-*` 新增一份报告（mock ES 验证写入调用）
- [ ] `GET /api/v1/reports/recent` 返回真实列表（去占位）
- [ ] `pytest tests/test_m4_scheduled.py` 全绿（ES/LLM 全 mock）
- [ ] `analysis/DEV.md`、`report/DEV.md` 状态表与日志更新
- [ ] `task_m4/STATUS.md` 全部任务 `已完成`

---

## 6. 跨任务约定

1. 只改自己负责的脚本（M4-04 改 requirements 加 langgraph；M4-06 加 apscheduler）。
2. 不改 `index_service.py`、`core/config.py`、`aggregation_service.py`、M3 langchain 文件（只 import）。
3. 图节点失败写入 `state["errors"]` 并降级，不中断整图（§2.2 设计要点）。
4. LLM 不可用时 `generate_report` 退化为纯统计报告（复用 M3 `report_chain` 降级）。
5. ES 写入异常返回结构化错误，不抛裸异常。
6. 中文注释与文档使用简体中文；不要 commit。
7. 进度维护见 `task_m4/STATUS.md`；派发 Prompt 见 `PROMPT_DISPATCH.md`。

---

## 7. 与后续里程碑关系

```text
M3 能力层 → M4 定时子图闭环（本目录）
                ↘
                 M5 规则子图闭环（graph_rule + trigger_scanner + alert 持久化）
                 M6 主图收敛 + reports/alerts 前端展示 + node_trace
```

M4 完成后，M5 复用同一套 `state`/`schemas`/`evidence_builder`，并接入 `diagnosis_chain`；M6 用 `graph_main` 收敛定时与规则两子图。

---

## 8. 已知遗留（不阻塞 M4）

| 项 | 现状 | 何时收敛 |
| --- | --- | --- |
| `analyze_relations` / `relation_chain` | 子图最小版跳过 | M7 |
| `graph_main` 主图 | 占位 | M6 |
| `graph_rule` / `trigger_scanner` | 占位 | M5 |
| `alert_service` / `dedup` 落地 | 占位 | M5 |
| 真实 LLM 联调 | 需配置 `LLM_API_KEY` | 集成环境 |
