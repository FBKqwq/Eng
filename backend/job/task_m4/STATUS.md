# M4 任务进度与依赖状态（Agent 共享真相源）

> **用途**：各 Agent 开工前必读；完成后仅更新**自己负责的那一行**。  
> **编排**：`task_m4/README.md`  
> **前置**：`task_m1` / `task_m2` / `task_m3` 的 STATUS 须均全绿

---

## 1. 前置检查：M1 / M2 / M3 里程碑

| 检查项 | 要求 | 当前 |
| --- | --- | --- |
| M1 任务表 | M1-01~M1-11 全部 `已完成`/`已合并` | 已满足 |
| M2 任务表 | M2-01~M2-08 全部 `已完成`/`已合并` | 已满足 |
| M3 任务表 | M3-01~M3-09 全部 `已完成`/`已合并` | 已满足 |
| M1+M2+M3 测试 | `pytest tests/test_m1_*.py tests/test_m2_tools.py tests/test_m3_langchain.py` | 73 passed, 3 skipped（2026-06-22 复验） |
| 能力层 | report_chain / evidence_builder 可用且可降级 | 已满足 |

**M4 可启动。**

---

## 2. 状态枚举

`未开始` | `进行中` | `已完成` | `已合并` | `阻塞`

---

## 3. 派发前依赖检查

| 任务 | 可派发条件 |
| --- | --- |
| M4-01、M4-02、M4-03 | M1/M3 完成 |
| M4-04 | M4-02、M4-03 均为 `已完成`/`已合并` |
| M4-05 | M4-01 为 `已完成`/`已合并` |
| M4-06 | M4-01、M4-04 均为 `已完成`/`已合并` |
| M4-07 | M4-06 完成 |
| M4-08 | M4-04、M4-06 完成 |
| M4-09 | M4-04、M4-06 完成（可与 M4-07、M4-08 并行） |

---

## 4. 任务状态表

| 任务 | 负责文件 | 状态 | 负责人/Agent | 完成时间 | 分支/PR | 验收摘要 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M4-01 | `report/report_service.py` | 已完成 | elk-backend-agent | 2026-06-22 | | AC-01~05：三函数真实 ES 读写，无 placeholder | analysis-results-* 读写 |
| M4-02 | `analysis/schemas.py` | 已完成 | elk-backend-agent | 2026-06-22 | | AC-01~04：normalize_trigger + make_node_trace，无 placeholder | |
| M4-03 | `analysis/state.py` | 已完成 | 状态契约 Agent | 2026-06-22 | | AC-01~03 通过：create_initial_state / append_node_trace / record_error | 无 placeholder |
| M4-04 | `analysis/graph_scheduled.py` + `requirements.txt` | 已完成 | elk-backend-agent | 2026-06-22 | | AC-01~05：LangGraph 六节点跑通，降级不崩，requirements 含 langgraph | 跳过 analyze_relations |
| M4-05 | `api/v1/reports.py` | 已完成 | elk-backend-agent | 2026-06-22 | | AC-01~04：/recent 与 /{id} 真实调 report_service，无强制 placeholder | 去占位 |
| M4-06 | `analysis/scheduler.py` + `requirements.txt` | 已完成 | elk-backend-agent | 2026-06-22 | | AC-01~05：run_once 子图→write_report 闭环，APScheduler max_instances=1，无 placeholder | 含 apscheduler |
| M4-07 | `tasks/run_scheduler.py`（新建） | 已完成 | elk-backend-agent | 2026-06-22 | | AC-01~03：run_scheduler 常驻/--once 入口，仅调 scheduler | 调度入口 |
| M4-08 | `tests/test_m4_scheduled.py`（新建） | 已完成 | elk-backend-agent | 2026-06-22 | | AC-01~04：17 passed，report_service/子图/scheduler 全 mock，含降级与闭环 | 全 mock |
| M4-09 | `analysis/DEV.md` + `report/DEV.md` | 已完成 | elk-backend-agent | 2026-06-22 | | AC-01~03：两 DEV.md 与代码一致，子图流/降级/持久化约定已记录 | 文档收敛；M4 里程碑可收口 |

---

## 5. 当前可派发任务

无可派发 M4 任务，后续见 M5。

---

## 6. 变更日志

| 时间 | 操作人/Agent | 说明 |
| --- | --- | --- |
| 2026-06-22 | elk-backend-agent (M4-06) | M4-06 完成：scheduler run_once 闭环 + APScheduler 周期调度（max_instances=1）+ apscheduler 依赖 |
| 2026-06-22 | elk-backend-agent (M4-04) | M4-04 完成：graph_scheduled LangGraph 六节点 + langgraph 依赖；跳过 analyze_relations |
| 2026-06-22 | elk-backend-agent (M4-09) | M4-09 完成：analysis/DEV.md + report/DEV.md 文档收敛；子图节点流、降级策略、analysis-results-* 约定已记录 |
| 2026-06-22 | elk-backend-agent (M4-09 复验) | M4-01~09 全部已完成；STATUS 第 5 节刷新为「无可派发 M4 任务，后续见 M5」；M4-09 备注 M4 里程碑可收口 |
