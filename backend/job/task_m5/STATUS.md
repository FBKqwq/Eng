# M5 任务进度与依赖状态（Agent 共享真相源）

> **用途**：各 Agent 开工前必读；完成后仅更新**自己负责的那一行**。  
> **编排**：`task_m5/README.md`  
> **前置**：`task_m1` / `task_m2` / `task_m3` / `task_m4` 的 STATUS 须均全绿

---

## 1. 前置检查：M1 / M2 / M3 / M4 里程碑

| 检查项 | 要求 | 当前 |
| --- | --- | --- |
| M1 任务表 | M1-01~M1-11 全部 `已完成`/`已合并` | 已满足 |
| M2 任务表 | M2-01~M2-08 全部 `已完成`/`已合并` | 已满足 |
| M3 任务表 | M3-01~M3-09 全部 `已完成`/`已合并` | 已满足 |
| M4 任务表 | M4-01~M4-09 全部 `已完成`/`已合并` | 已满足 |
| M1~M4 测试 | `pytest tests/test_m1_*.py test_m2_tools.py test_m3_langchain.py test_m4_scheduled.py` | 90 passed, 3 skipped（2026-06-22 复验） |
| 能力层 | diagnosis_chain / evidence_builder / context_service 可用且可降级 | 已满足 |

**M5 里程碑已收口。**

---

## 2. 状态枚举

`未开始` | `进行中` | `已完成` | `已合并` | `阻塞`

---

## 3. 派发前依赖检查

| 任务 | 可派发条件 |
| --- | --- |
| M5-01、M5-02、M5-03 | M1 完成 |
| M5-04 | M5-03 为 `已完成`/`已合并` |
| M5-05 | M5-01 为 `已完成`/`已合并` |
| M5-06 | M5-04 为 `已完成`/`已合并` |
| M5-07 | M5-06、M5-01、M5-02 均为 `已完成`/`已合并` |
| M5-08 | M5-07 完成 |
| M5-09 | M5-06、M5-07 完成 |
| M5-10 | M5-06、M5-07 完成（可与 M5-08、M5-09 并行） |

---

## 4. 任务状态表

| 任务 | 负责文件 | 状态 | 负责人/Agent | 完成时间 | 分支/PR | 验收摘要 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M5-01 | `alert/alert_service.py` | 已完成 | M5-01 Agent | 2026-06-22 | | AC-01~05：write/list/ack 三函数去 placeholder；复用 get_es_client；active→acknowledged 状态机；mock ES 验证通过 | alerts-* 读写 + 状态机 |
| M5-02 | `alert/dedup.py` | 已完成 | M5-02 Agent | 2026-06-22 | 工作区 | AC-01~AC-04 通过；幂等键+ES查重结构化返回；无 placeholder | M5-07 可依赖 |
| M5-03 | `diagnosis/rule_definitions.py` | 已完成 | M5-03 Agent | 2026-06-22 | | AC-01~04：三类规则共 10 条；PAY_FAIL trigger_subgraph=True；get_rule_definitions 返回完整列表 | 供 M5-04 rule_engine 读取 |
| M5-04 | `diagnosis/rule_engine.py` | 已完成 | M5-04 Agent | 2026-06-22 | | AC-01~04：match_log 读 rule_definitions；PAY_FAIL/5xx 命中；frequency 单条不命中；classify_by_rules 不变 | M5-06 可依赖 |
| M5-05 | `api/v1/alerts.py` | 已完成 | M5-05 Agent | 2026-06-22 | | AC-01~04：/active 与 /{id}/ack 真实调用 alert_service；placeholder=False；items/total/status 透传 | 去占位 |
| M5-06 | `analysis/graph_rule.py` | 已完成 | M5-06 Agent | 2026-06-22 | 工作区 | AC-01~05：七节点 LangGraph 子图；PAY_FAIL 返回 report+alert_candidate+node_trace；节点降级不中断；无 placeholder | M5-07/09/10 可依赖 |
| M5-07 | `analysis/trigger_scanner.py` | 已完成 | M5-07 Agent | 2026-06-22 | 工作区 | AC-01~05：scan_once 闭环（子图→写报告+去重写预警）；APScheduler max_instances=1；无 placeholder | M5-08/09/10 可依赖 |
| M5-08 | `tasks/run_trigger_scanner.py`（新建） | 已完成 | M5-08 Agent | 2026-06-22 | 工作区 | AC-01~03：`--once` 可执行；仅 import trigger_scanner；stdout 摘要/失败 exit(1) | 扫描入口 |
| M5-09 | `tests/test_m5_rule.py`（新建） | 已完成 | M5-09 Agent | 2026-06-22 | 工作区 | AC-01~04：16 passed；全 mock ES/LLM/子图；覆盖 rule_definitions/match_log/alert/dedup/graph_rule/scan_once 闭环与去重 | 全 mock |
| M5-10 | `diagnosis/DEV.md` + `alert/DEV.md` + `analysis/DEV.md` | 已完成 | M5-10 Agent | 2026-06-22 | | AC-01~03：三 DEV.md 与 M5 代码一致；规则语义/状态机/子图闭环已记录 | 文档收敛 |

---

## 5. 当前可派发任务

**无可派发 M5 任务。M5-01~M5-10 均已 `已完成`；M5 里程碑可收口，后续见 M6。**

| 下一阶段 | 说明 |
| --- | --- |
| M6 | `graph_main` 主图收敛、`node_trace` 前端展示对接等（见 `task_m6/` 编排） |

---

## 6. 变更日志

| 时间 | 操作人/Agent | 说明 |
| --- | --- | --- |
| 2026-06-22 | 规划 | 创建 task_m5；M1~M4 验收通过（90 passed），开放 M5 阶段 A 派发 |
| 2026-06-22 | M5-01 Agent | 完成 alert_service：alerts-* 读写 + active→acknowledged 状态机 |
| 2026-06-22 | M5-04 Agent | 完成 rule_engine.match_log：声明式三类规则匹配，去除 placeholder |
| 2026-06-22 | M5-06 Agent | 完成 graph_rule：七节点规则子图（上下文→关联→证据→根因→定级→报告），run_rule_subgraph 返回结构化结果 |
| 2026-06-22 | M5-07 Agent | 完成 trigger_scanner：scan_once 扫描→match_log 复核→子图→写报告+去重写预警；APScheduler 周期调度防重叠 |
| 2026-06-22 | M5-08 Agent | 完成 run_trigger_scanner：`--once` 单次扫描 + 常驻模式；仅 import trigger_scanner |
| 2026-06-22 | M5-09 Agent | 完成 test_m5_rule.py：16 用例全绿，规则闭环/去重/降级路径全 mock 覆盖 |
| 2026-06-22 | M5-10 Agent | 完成三模块 DEV 文档收敛：diagnosis 规则语义、alert 状态机与幂等键、analysis 规则子图与 scan_once 闭环 |
