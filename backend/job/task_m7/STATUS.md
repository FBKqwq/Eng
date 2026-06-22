# M7 任务进度与依赖状态（Agent 共享真相源）

> **用途**：各 Agent 开工前必读；完成后仅更新**自己负责的那一行**。  
> **编排**：`task_m7/README.md`  
> **前置**：`task_m1` ~ `task_m6` 的 STATUS 须均全绿

---

## 1. 前置检查：M1 ~ M6 里程碑

| 检查项 | 要求 | 当前 |
| --- | --- | --- |
| M1 任务表 | M1-01~M1-11 全部 `已完成`/`已合并` | 已满足 |
| M2 任务表 | M2-01~M2-08 全部 `已完成`/`已合并` | 已满足 |
| M3 任务表 | M3-01~M3-09 全部 `已完成`/`已合并` | 已满足 |
| M4 任务表 | M4-01~M4-09 全部 `已完成`/`已合并` | 已满足 |
| M5 任务表 | M5-01~M5-10 全部 `已完成`/`已合并` | 已满足 |
| M6 任务表 | M6-01~M6-07 全部 `已完成`/`已合并` | 已满足 |
| M1~M6 测试 | `pytest tests/test_m1_*.py test_m2_tools.py test_m3_langchain.py test_m4_scheduled.py test_m5_rule.py test_m6_main.py` | 119 passed, 3 skipped（2026-06-22 复验） |

**M7 可启动。**

---

## 2. 状态枚举

`未开始` | `进行中` | `已完成` | `已合并` | `阻塞`

---

## 3. 派发前依赖检查

| 任务 | 可派发条件 |
| --- | --- |
| M7-01、M7-02、M7-05、M7-06 | M1/M3 完成（即刻可派发） |
| M7-03 | M7-01、M7-02 均为 `已完成`/`已合并` |
| M7-04 | M7-03 为 `已完成`/`已合并` |
| M7-07 | M7-05、M7-06 均为 `已完成`/`已合并` |
| M7-08 | M7-07 为 `已完成`/`已合并` |
| M7-09 | M7-04、M7-07、M7-08 完成 |
| M7-10 | M7-04、M7-07、M7-08 完成（可与 M7-09 并行） |

---

## 4. 任务状态表

| 任务 | 负责文件 | 状态 | 负责人/Agent | 完成时间 | 分支/PR | 验收摘要 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M7-01 | `langchain/prompts.py` | 已完成 | Prompt Agent | 2026-06-22 | | AC-01~AC-04 通过 | RELATION_PROMPT |
| M7-02 | `langchain/chain_schemas.py` | 已完成 | Schema Agent | 2026-06-22 | | AC-01~AC-04 通过 | RelationChainOutput |
| M7-03 | `langchain/relation_chain.py` | 已完成 | 关系发现 Chain Agent | 2026-06-22 | | AC-01~AC-04 通过：discover_relations LLM 结构化 + 降级空列表 | |
| M7-04 | `analysis/graph_scheduled.py` | 已完成 | 定时子图 Agent | 2026-06-22 | | AC-01~AC-05：七节点含 analyze_relations；relations 注入报告；降级 skipped 报告仍产出 | M7-09/10 可依赖 |
| M7-05 | `tools/elasticsearch_tools.py` | 已完成 | ES 工具 Agent | 2026-06-22 | 工作区 | AC-01~AC-04：工具 11/12/13 + 入参模型；peak_bucket / comparison 环比；超长窗口结构化错误 | M7-07 可派发 |
| M7-06 | `tools/kibana_tools.py`（新建）+ `report_tools.py` + `alert_tools.py` | 已完成 | 辅助工具 Agent | 2026-06-22 | | AC-01~04 通过：工具 14/15/16 实装，Pydantic 入参 + 薄包装 service，异常结构化 | 待 M7-07 注册 |
| M7-07 | `tools/registry.py` + `requirements.txt` | 已完成 | 注册中心 Agent | 2026-06-22 | 工作区 | AC-01~04：16 工具注册、读写分离不变、create_mcp_server 懒加载 FastMCP、缺失结构化降级 | M7-08 可派发 |
| M7-08 | `tasks/run_mcp_server.py`（新建） | 未开始 | | | | | MCP 启动入口 |
| M7-09 | `tests/test_m7_enhancements.py`（新建） | 未开始 | | | | | 含 M1~M6 回归 |
| M7-10 | `langchain/DEV.md` + `analysis/DEV.md` + `tools/DEV.md` | 未开始 | | | | | 文档收口 |

---

## 5. 当前可派发任务

| 可派发任务 | 原因 |
| --- | --- |
| M7-01 | M3 已完成；RELATION_PROMPT 独立可起步 |
| M7-02 | M3 已完成；RelationChainOutput 独立可起步 |
| M7-05 | M1 已完成；es 增强工具独立可起步 |
| M7-06 | M1 已完成；辅助工具独立可起步 |

---

## 6. 变更日志

| 时间 | 操作人/Agent | 说明 |
| --- | --- | --- |
| 2026-06-22 | ES 工具 Agent (M7-05) | 完成工具 11/12/13：es_get_business_funnel、es_detect_traffic_peak、es_compare_time_windows |
| 2026-06-22 | Schema Agent | M7-02 完成：新增 RelationItem / RelationChainOutput，confidence 钳制校验 |
| 2026-06-22 | 关系发现 Chain Agent (M7-03) | 完成 discover_relations：LLM 结构化调用 RelationChainOutput，失败降级空 relations |
| 2026-06-22 | 注册中心 Agent (M7-07) | 工具表扩至 16；实装 create_mcp_server（FastMCP 懒加载，仅读类工具）；requirements 增 fastmcp |
| 2026-06-22 | 定时子图 Agent (M7-04) | 完成 analyze_relations 节点：七节点流、relations 写 state 并注入报告；降级 skipped 不阻断报告 |
