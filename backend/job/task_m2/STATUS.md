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
| M2-01 | `app/services/tools/elasticsearch_tools.py` | 已完成 | M2-01 Agent | 2026-06-17 | | AC-01~05：五工具去除 placeholder，薄包装 ES services，统一 ok/error/tool 返回；compileall 与 import 自测通过 | 工具 1~5 |
| M2-02 | `app/services/tools/system_tools.py` | 已完成 | M2-02 Agent | 2026-06-17 | | AC-01~04：组合 ES/Kafka/Docker 健康快照，无 placeholder，三节齐全；registry 已注册 system_health_check；test_m2_tools 覆盖 | 工具 9（状态补录） |
| M2-03 | `app/services/tools/rule_tools.py` | 已完成 | M2-03 Agent | 2026-06-17 | | AC-01~03：包装 match_log、无 placeholder | 工具 10 |
| M2-04 | `app/services/tools/report_tools.py` | 已完成 | M2-04 Agent | 2026-06-17 | | AC-01~03：analysis_write_report 薄包装 write_report、无 placeholder；report_list_recent 第二阶段占位 | 工具 6 |
| M2-05 | `app/services/tools/alert_tools.py` | 已完成 | M2-05 Agent | 2026-06-17 | | AC-01~03：工具 7、8 薄包装 alert_service/dedup，无 placeholder，统一 ok/tool 返回；import 自测通过 | 工具 7、8 |
| M2-06 | `app/services/tools/registry.py` + `requirements.txt` | 已完成 | M2-06 Agent | 2026-06-17 | | AC-01~05：StructuredTool 注册 10 工具、默认 8 读 + 读写分离；langchain-core 已追加；invoke 自测通过；create_mcp_server 占位指向 M7 | 含 langchain-core |
| M2-07 | `tests/test_m2_tools.py` | 已完成 | M2-07 Agent | 2026-06-17 | | AC-01~03：21 passed；mock 覆盖 ES 五工具/六模板聚合/system/rule/report/alert/registry/异常路径/StructuredTool.invoke；新增 pytest.ini 注册 integration mark | 默认读工具 8 个（非任务草稿 9） |
| M2-08 | `app/services/tools/DEV.md` | 已完成 | M2-08 文档 Agent | 2026-06-17 | | AC-01~03：DEV 与代码一致、读写分离与 10 工具清单已记录、create_mcp_server 仍标 M7 | M2-07 已完成；M2-02 仍进行中 |

---

## 5. 当前可派发任务

| 可派发任务 | 原因 |
| --- | --- |
| — | M2-01~M2-08 全部 `已完成`；M2 里程碑已收口，后续见 `task_m3` |

---

## 6. 变更日志

| 时间 | 操作人/Agent | 说明 |
| --- | --- | --- |
| 2026-06-22 | 规划 | 复验 M1+M2 测试 51 passed/3 skipped；补录 M2-02 为已完成（system_tools 实测无占位）；M2 收口，开放 M3 规划 |
| 2026-06-17 | M2-08 文档 Agent | M2-08 完成：tools/DEV.md M2 收敛，10 工具已实现、读写分离已记录 |
| 2026-06-17 | M2-06 Agent | M2-06 完成：registry StructuredTool 注册 + 读写分离 + langchain-core 依赖 |
| 2026-06-17 | M2-01 Agent | M2-01 完成：elasticsearch_tools 五工具真实实现，薄包装 log_query/aggregation/context service |
| 2026-06-16 | 规划 | 创建 task_m2；M1 验收通过，开放 M2 阶段 A 派发 |
