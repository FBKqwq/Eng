# M3 任务进度与依赖状态（Agent 共享真相源）

> **用途**：各 Agent 开工前必读；完成后仅更新**自己负责的那一行**。  
> **编排**：`task_m3/README.md`  
> **前置**：`task_m1/STATUS.md` 与 `task_m2/STATUS.md` 须均全绿

---

## 1. 前置检查：M1 / M2 里程碑

| 检查项 | 要求 | 当前 |
| --- | --- | --- |
| M1 任务表 | M1-01~M1-11 全部 `已完成`/`已合并` | 已满足 |
| M2 任务表 | M2-01~M2-08 全部 `已完成`/`已合并` | 已满足（2026-06-22 复验） |
| M1+M2 测试 | `pytest tests/test_m1_*.py tests/test_m2_tools.py` | 51 passed, 3 skipped（本地复验） |
| 工具层 | `get_langchain_tools()` 可用，10 工具无 placeholder | 已满足 |

**M3 可启动。**

---

## 2. 状态枚举

`未开始` | `进行中` | `已完成` | `已合并` | `阻塞`

---

## 3. 派发前依赖检查

| 任务 | 可派发条件 |
| --- | --- |
| M3-01 ~ M3-05 | M2 完成 |
| M3-06 | M3-01~M3-05 均为 `已完成`/`已合并` |
| M3-07 | M3-01~M3-05 均为 `已完成`/`已合并` |
| M3-08 | M3-06、M3-07 完成 |
| M3-09 | M3-06、M3-07 完成（可与 M3-08 并行，不同文件） |

---

## 4. 任务状态表

| 任务 | 负责文件 | 状态 | 负责人/Agent | 完成时间 | 分支/PR | 验收摘要 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M3-01 | `langchain/llm_manager.py` + `requirements.txt` | 已完成 | elk-backend-agent (M3-01) | 2026-06-22 | | AC-01~05 通过：is_llm_available/get_llm/invoke_structured 实现；追加 langchain-openai | 含 langchain-openai |
| M3-02 | `langchain/prompts.py` | 已完成 | Prompt 工程 Agent | 2026-06-22 | | AC-01~04 通过 | report/diagnosis/evidence_summary/alert 模板；relation 标 M7 |
| M3-03 | `langchain/output_parsers.py` | 已完成 | output-parsers-agent | 2026-06-22 | | AC-01~03 通过：JSON/代码块/非法文本三路径；无 placeholder | Pydantic + JSON 修复 |
| M3-04 | `langchain/evidence_builder.py` | 已完成 | elk-backend-agent (M3-04) | 2026-06-22 | | AC-01~05：分层采样、ERROR 优先、空输入、无 placeholder | 纯代码压缩 |
| M3-05 | `langchain/chain_schemas.py`（新建） | 已完成 | elk-backend-agent (M3-05) | 2026-06-22 | | AC-01~04：ReportChainOutput/DiagnosisChainOutput 可 import 与 model_validate；字段含默认值；未改 schemas/*.py | 链 I/O 模型 |
| M3-06 | `langchain/report_chain.py` | 已完成 | elk-backend-agent (M3-06) | 2026-06-22 | | AC-01~04：LLM 路径 invoke_structured + 模板降级；无 placeholder；字段对齐 ReportChainOutput | 周期报告 + 降级 |
| M3-07 | `langchain/diagnosis_chain.py` | 已完成 | elk-backend-agent (M3-07) | 2026-06-22 | | AC-01~04：infer_root_cause/generate_event_report；LLM+规则降级；无 placeholder | 根因诊断 + 降级 |
| M3-08 | `tests/test_m3_langchain.py` | 已完成 | elk-backend-agent (M3-08) | 2026-06-22 | | AC-01~04：22 passed；mock LLM/ES；覆盖降级、三路径解析、ERROR 优先、无 placeholder | 全 mock |
| M3-09 | `langchain/DEV.md` | 已完成 | 文档 Agent (M3-09) | 2026-06-22 | | AC-01~03：七文件已实现、降级策略与依赖已记录；relation→M7、alert→M5/M6 | 文档收敛；**M3 里程碑可收口** |

---

## 5. 当前可派发任务

**无可派发 M3 任务，后续见 M4。**

M3-01~M3-09 均已 `已完成`（2026-06-22 复验：M3-08 单测 22 passed）。

---

## 6. 变更日志

| 时间 | 操作人/Agent | 说明 |
| --- | --- | --- |
| 2026-06-22 | elk-backend-agent (M3-06) | 实现 report_chain.generate_periodic_report：LLM 结构化调用 + summary/metrics 规则降级 |
| 2026-06-22 | elk-backend-agent (M3-08) | 新建 tests/test_m3_langchain.py：22 passed，全 mock，覆盖降级与解析三路径 |
| 2026-06-22 | 文档 Agent (M3-09) | langchain/DEV.md 收敛：M3 七文件标已实现，记录降级策略与 Chain 依赖；relation→M7、alert→M5/M6 |
