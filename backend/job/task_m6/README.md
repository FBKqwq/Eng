# M6 主图收敛与前端展示 — 任务编排说明

> 对应总体规划：`doc/后端开发总体规划-Services-LangGraph-MCP.md` §2.3 / §1.3（里程碑 **M6**）  
> 前置里程碑：**M1~M5 全部 STATUS 全绿**  
> 原则：**一个 Agent 只负责一个主脚本**，避免并行改同一文件

---

## 1. M6 目标

用 `graph_main` 收敛定时与规则两子图，统一**结果归一化 → 预警决策 → 持久化**，并向前端暴露**最新报告、活跃预警与图执行轨迹（node_trace）**。

| 项 | 说明 |
| --- | --- |
| **里程碑验收** | 前端可见：①最新分析报告（`/reports/recent`、`/reports/{id}`）②活跃预警（`/alerts/active`）③图执行轨迹（`/analysis/runs/recent`、`/analysis/run`）|
| **收敛要点** | 持久化（写报告/写预警）统一收口到主图 `persist_result` 节点；定时/规则两子图作为 subgraph 节点挂载，**不再各自持久化** |
| **不在 M6** | `relation_chain` 隐藏关系发现（M7）、第二阶段工具与 MCP Server（M7） |

---

## 2. M6 范围与组件

| 组件 | 落点文件 | 依赖 |
| --- | --- | --- |
| 预警解释 Chain | `langchain/alert_chain.py` | M3 llm_manager/prompts |
| 主图 | `analysis/graph_main.py` | graph_scheduled(M4)、graph_rule(M5)、alert_chain、dedup(M5)、report_service(M4)、alert_service(M5) |
| 调度器收敛 | `analysis/scheduler.py` | graph_main |
| 扫描器收敛 | `analysis/trigger_scanner.py` | graph_main |
| 分析轨迹 API | `api/v1/analysis.py`（新建）+ `api/router.py` | graph_main、report_service |
| 单测 | `tests/test_m6_main.py`（新建） | 上述 |
| 文档 | `analysis/DEV.md` + `langchain/DEV.md` + `api/DEV.md` | 上述 |

**复用（不重写）**：`run_scheduled_subgraph`、`run_rule_subgraph`、`report_service`、`alert_service`、`dedup`、`evidence_builder`。

---

## 3. 主图节点流（§2.3）

```text
normalize_trigger -> build_state -> route（条件边：trigger_type）
  ├── scheduled -> 定时子图（run_scheduled_subgraph 作为节点）
  └── rule      -> 规则子图（run_rule_subgraph 作为节点）
  -> merge_result -> alert_decision -> persist_result -> END
```

| 节点 | 职责 | 依赖 |
| --- | --- | --- |
| `normalize_trigger` | 统一触发为 TriggerEvent | `analysis/schemas` |
| `build_state` | 初始化 task_id、时间窗 | `analysis/state` |
| `route` | 条件边按 trigger_type 分发 | — |
| `merge_result` | 子图报告归一化为统一 report + 汇总 node_trace | — |
| `alert_decision` | 规则 severity≥high / 定时 risk_level=high 出预警；调 `dedup.check_duplicate`；`alert_chain` 生成文案 | dedup、alert_chain |
| `persist_result` | 写报告（含 node_trace）+ 视情况写预警 | report_service、alert_service |

---

## 4. 任务清单与文件归属

| 任务编号 | 文档 | 唯一负责脚本 | 前置依赖 |
| --- | --- | --- | --- |
| M6-01 | M6-01-alert_chain.md | `langchain/alert_chain.py` | M3 完成 |
| M6-02 | M6-02-graph_main.md | `analysis/graph_main.py` | M6-01 |
| M6-03 | M6-03-scheduler.md | `analysis/scheduler.py` | M6-02 |
| M6-04 | M6-04-trigger_scanner.md | `analysis/trigger_scanner.py` | M6-02 |
| M6-05 | M6-05-analysis_api.md | `api/v1/analysis.py`（新建）+ `api/router.py` | M6-02 |
| M6-06 | M6-06-test_main.md | `tests/test_m6_main.py`（新建，必要时同步调整 test_m4/test_m5） | M6-02~05 |
| M6-07 | M6-07-dev_docs.md | `analysis/DEV.md` + `langchain/DEV.md` + `api/DEV.md` | M6-02~05 |

**依赖说明**：

- 无新增第三方依赖（langgraph/apscheduler 已就绪）。
- **回归风险**：M6-03/04 将 `run_once`/`scan_once` 改为委托 `graph_main`，持久化移入主图 `persist_result`。两函数对外返回契约（`{ok, report_id/alert_ids, node_trace}`）须保持稳定；如确有变化，由 **M6-06** 同步调整 `test_m4_scheduled.py` / `test_m5_rule.py`（仅测试文件）。
- `api/router.py` 仅由 **M6-05** 编辑（新增 analysis 路由注册）。

---

## 5. 推荐执行顺序

```text
阶段 A：M6-01  alert_chain.py
阶段 B：M6-02  graph_main.py            依赖 M6-01
阶段 C（可并行，3 Agent，依赖 M6-02）
├── M6-03  scheduler.py（委托 graph_main）
├── M6-04  trigger_scanner.py（委托 graph_main）
└── M6-05  api/v1/analysis.py + router.py
阶段 D（可并行，2 Agent，依赖 C）
├── M6-06  tests/test_m6_main.py（+ 回归校正）
└── M6-07  analysis/langchain/api DEV
```

---

## 6. M6 总体验收（Definition of Done）

- [ ] `alert_chain.explain_alert` 产出预警文案，LLM 不可用时降级（模板）
- [ ] `run_main_graph("scheduled"|"rule", ...)` 跑通：route→子图→merge→alert_decision→persist，返回 `node_trace` + ids
- [ ] 持久化仅在主图 `persist_result` 发生；预警决策含 dedup
- [ ] scheduler/trigger_scanner 委托主图，对外契约稳定
- [ ] `GET /api/v1/analysis/runs/recent` 返回近期图执行轨迹；`POST /api/v1/analysis/run` 手动触发并返回 node_trace
- [ ] `/reports/recent`、`/reports/{id}`、`/alerts/active` 联通真实数据
- [ ] `pytest tests/test_m6_main.py` 全绿；M1~M5 全量回归通过
- [ ] `analysis/DEV.md`、`langchain/DEV.md`、`api/DEV.md` 更新
- [ ] `task_m6/STATUS.md` 全部任务 `已完成`

---

## 7. 跨任务约定

1. 只改自己负责的脚本；`router.py` 仅 M6-05 编辑。
2. 不改 `index_service.py`、`core/config.py`、`graph_scheduled.py`、`graph_rule.py`、`report_service.py`、`alert_service.py`、`dedup.py`（只 import）。
3. 持久化统一收口主图 `persist_result`，子图不再持久化。
4. 图节点失败写 `state["errors"]` 并降级，不中断整图。
5. LLM 不可用时 `alert_chain` 与子图链均降级。
6. ES 写入异常返回结构化错误，不抛裸异常。
7. 中文注释与文档使用简体中文；不要 commit。
8. 进度维护见 `task_m6/STATUS.md`；派发 Prompt 见 `PROMPT_DISPATCH.md`。

---

## 8. 与后续里程碑关系

```text
M6 主图收敛与前端展示（本目录）
   ↘ M7 增强项：relation_chain 隐藏关系发现 + 第二阶段工具 + MCP Server 形态
```

M6 完成后整体闭环可演示；M7 在主图/定时子图接入 `analyze_relations` 节点，并对外暴露 MCP Server。

---

## 9. 已知遗留（不阻塞 M6）

| 项 | 现状 | 何时收敛 |
| --- | --- | --- |
| `analyze_relations` / `relation_chain` | 跳过/占位 | M7 |
| 第二阶段工具（11~16）、`create_mcp_server` | 占位 | M7 |
| 真实 LLM 联调 | 需配置 `LLM_API_KEY` | 集成环境 |
