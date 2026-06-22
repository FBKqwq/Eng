# M6 任务进度与依赖状态（Agent 共享真相源）

> **用途**：各 Agent 开工前必读；完成后仅更新**自己负责的那一行**。  
> **编排**：`task_m6/README.md`  
> **前置**：`task_m1` ~ `task_m5` 的 STATUS 须均全绿

---

## 1. 前置检查：M1 ~ M5 里程碑

| 检查项 | 要求 | 当前 |
| --- | --- | --- |
| M1 任务表 | M1-01~M1-11 全部 `已完成`/`已合并` | 已满足 |
| M2 任务表 | M2-01~M2-08 全部 `已完成`/`已合并` | 已满足 |
| M3 任务表 | M3-01~M3-09 全部 `已完成`/`已合并` | 已满足 |
| M4 任务表 | M4-01~M4-09 全部 `已完成`/`已合并` | 已满足 |
| M5 任务表 | M5-01~M5-10 全部 `已完成`/`已合并` | 已满足 |
| M1~M5 测试 | `pytest tests/test_m1_*.py test_m2_tools.py test_m3_langchain.py test_m4_scheduled.py test_m5_rule.py` | 106 passed, 3 skipped（2026-06-22 复验） |

**M6 可启动。**

---

## 2. 状态枚举

`未开始` | `进行中` | `已完成` | `已合并` | `阻塞`

---

## 3. 派发前依赖检查

| 任务 | 可派发条件 |
| --- | --- |
| M6-01 | M3 完成 |
| M6-02 | M6-01 为 `已完成`/`已合并` |
| M6-03、M6-04、M6-05 | M6-02 为 `已完成`/`已合并` |
| M6-06 | M6-02~M6-05 完成 |
| M6-07 | M6-02~M6-05 完成（可与 M6-06 并行） |

---

## 4. 任务状态表

| 任务 | 负责文件 | 状态 | 负责人/Agent | 完成时间 | 分支/PR | 验收摘要 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M6-01 | `langchain/alert_chain.py` | 已完成 | elk-backend-agent (M6-01) | 2026-06-22 | | AC-01~04：explain_alert LLM 路径 + 模板降级；返回 ok/degraded/title/detail；无 placeholder | M6-02 可依赖 |
| M6-02 | `analysis/graph_main.py` | 已完成 | elk-backend-agent (M6-02) | 2026-06-22 | | AC-01~05：主图七节点流；scheduled/rule 路由；merge+alert_decision+persist 收口；无 placeholder | M6-03/04/05 可依赖 |
| M6-03 | `analysis/scheduler.py` | 已完成 | elk-backend-agent (M6-03) | 2026-06-22 | | AC-01~04：run_once 委托 run_main_graph；移除 write_report；返回 ok/report_id/node_trace；start/stop 不变 | M6-06 需校正 test_m4 run_once mock |
| M6-04 | `analysis/trigger_scanner.py` | 已完成 | elk-backend-agent (M6-04) | 2026-06-22 | | AC-01~04：scan_once 委托 run_main_graph("rule")；移除直接持久化/去重；返回契约稳定 | M6-06 需调整 test_m5 mock |
| M6-05 | `api/v1/analysis.py`（新建）+ `api/router.py` | 已完成 | elk-backend-agent (M6-05) | 2026-06-22 | | AC-01~04：GET /runs/recent node_trace 摘要；POST /run 手动触发；router 注册 analysis | list 项无 node_trace，经 get_report 补全 |
| M6-06 | `tests/test_m6_main.py`（新建） | 已完成 | elk-backend-agent (M6-06) | 2026-06-22 | | AC-01~04：13 项单测全绿；M1~M5 回归 106 passed；校正 test_m4/test_m5 mock run_main_graph | 含回归校正 |
| M6-07 | `analysis/DEV.md` + `langchain/DEV.md` + `api/DEV.md` | 已完成 | elk-backend-agent (M6-07) | 2026-06-22 | | AC-01~03：三 DEV.md 与 M6 代码对齐；主图节点流/持久化/轨迹 API 已记录 | M6-06 完成后可收口 |

---

## 5. 当前可派发任务

| 可派发任务 | 原因 |
| --- | --- |
| M6-06 | M6-02~M6-05、M6-07 已完成；主图回归测试 `test_m6_main.py` 待合并 |

> M6-01~05、M6-07 均已完成；待 M6-06 完成后，M6 里程碑可收口，后续见 M7。

---

## 6. 变更日志

| 时间 | 操作人/Agent | 说明 |
| --- | --- | --- |
| 2026-06-22 | 规划 | 创建 task_m6；M1~M5 验收通过（106 passed），开放 M6-01 派发 |
| 2026-06-22 | elk-backend-agent (M6-01) | explain_alert 实现：LLM 结构化路径 + alert_type/service/severity 模板降级 |
| 2026-06-22 | elk-backend-agent (M6-02) | graph_main 主图收敛：normalize→route→子图→merge→alert_decision→persist；run_main_graph 返回 node_trace/ids |
| 2026-06-22 | elk-backend-agent (M6-07) | 三模块 DEV.md 文档收敛：analysis/langchain/api 与 M6 实现对齐 |
