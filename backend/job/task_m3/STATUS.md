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
| M3-01 | `langchain/llm_manager.py` + `requirements.txt` | 未开始 | | | | | 含 langchain-openai |
| M3-02 | `langchain/prompts.py` | 未开始 | | | | | report/diagnosis/evidence_summary |
| M3-03 | `langchain/output_parsers.py` | 未开始 | | | | | Pydantic + JSON 修复 |
| M3-04 | `langchain/evidence_builder.py` | 未开始 | | | | | 纯代码压缩 |
| M3-05 | `langchain/chain_schemas.py`（新建） | 未开始 | | | | | 链 I/O 模型 |
| M3-06 | `langchain/report_chain.py` | 未开始 | | | | | 周期报告 + 降级 |
| M3-07 | `langchain/diagnosis_chain.py` | 未开始 | | | | | 根因诊断 + 降级 |
| M3-08 | `tests/test_m3_langchain.py` | 未开始 | | | | | 全 mock |
| M3-09 | `langchain/DEV.md` | 未开始 | | | | | 文档收敛 |

---

## 5. 当前可派发任务

| 可派发任务 | 原因 |
| --- | --- |
| M3-01、M3-02、M3-03、M3-04、M3-05 | M1+M2 已完成；五文件互不冲突，可并行 |

---

## 6. 变更日志

| 时间 | 操作人/Agent | 说明 |
| --- | --- | --- |
| 2026-06-22 | 规划 | 创建 task_m3；M1+M2 验收通过（51 passed），开放 M3 阶段 A 派发 |
