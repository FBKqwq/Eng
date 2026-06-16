# M2 任务进度与依赖状态（Agent 共享真相源）

> **用途**：各 Agent 开工前必读；完成后仅更新**自己负责的那一行**。  
> **编排**：`task_m2/README.md`  
> **前置**：`task_m1/STATUS.md` 中 M1-01~M1-11 须均为 `已完成`/`已合并`

---

## 1. 前置检查：M1 里程碑

| 检查项 | 要求 | 当前 |
| --- | --- | --- |
| M1 任务表 | M1-01~M1-11 全部 `已完成`/`已合并` | 已满足（2026-06-16） |
| M1 测试 | `pytest tests/test_m1_*.py` 通过 | 32 passed, 1 skipped（本地复验） |
| ES 四模块 | 无 `placeholder: true` 生产返回 | 已满足 |

**M2 可启动。**

---

## 2. 状态枚举

同 M1：`未开始` | `进行中` | `已完成` | `已合并` | `阻塞`

---

## 3. 派发前依赖检查

| 任务 | 可派发条件 |
| --- | --- |
| M2-01 ~ M2-05 | M1 完成 |
| M2-06 | M2-01~M2-05 均为 `已完成`/`已合并` |
| M2-07 | M2-06 完成 |
| M2-08 | M2-06 完成（可与 M2-07 并行，不同文件） |

---

## 4. 任务状态表

| 任务 | 负责文件 | 状态 | 负责人/Agent | 完成时间 | 分支/PR | 验收摘要 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M2-01 | `app/services/tools/elasticsearch_tools.py` | 未开始 | | | | | 工具 1~5 |
| M2-02 | `app/services/tools/system_tools.py` | 未开始 | | | | | 工具 9 |
| M2-03 | `app/services/tools/rule_tools.py` | 未开始 | | | | | 工具 10 |
| M2-04 | `app/services/tools/report_tools.py` | 未开始 | | | | | 工具 6 |
| M2-05 | `app/services/tools/alert_tools.py` | 未开始 | | | | | 工具 7、8 |
| M2-06 | `app/services/tools/registry.py` + `requirements.txt` | 未开始 | | | | | 含 langchain-core |
| M2-07 | `tests/test_m2_tools.py` | 未开始 | | | | | |
| M2-08 | `app/services/tools/DEV.md` | 未开始 | | | | | 最后或与 M2-07 并行 |

---

## 5. 当前可派发任务

| 可派发任务 | 原因 |
| --- | --- |
| M2-01、M2-02、M2-03、M2-04、M2-05 | M1 已完成；五文件互不冲突，可并行 |

---

## 6. 变更日志

| 时间 | 操作人/Agent | 说明 |
| --- | --- | --- |
| 2026-06-16 | 规划 | 创建 task_m2；M1 验收通过，开放 M2 阶段 A 派发 |
