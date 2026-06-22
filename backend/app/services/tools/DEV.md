# Tools（MCP / Agent 工具层）DEV 文档

## 1. 文档用途说明

维护 `app/services/tools/` Agent 可调用工具薄适配层。工具只包装 services，不重新实现业务逻辑。

> **M7 收口说明**：16 工具注册、`create_mcp_server` FastMCP 懒加载与 `run_mcp_server` 任务入口均已实装；**M7 完成即总体规划（M1~M7）全部收口**（测试收口见 M7-09）。

## 2. 模块总览

| 文件 | 职责 | 状态 |
|---|---|---|
| `registry.py` | LangChain StructuredTool 注册；`get_langchain_tools` 读写分离；`create_mcp_server` FastMCP 出口 | 已实现（M2-06 + M7-07） |
| `elasticsearch_tools.py` | ES 查询/聚合/上下文/漏斗/峰值/环比 8 工具 | 已实现（M2 + M7-05） |
| `kibana_tools.py` | Kibana Discover 链接生成 | 已实现（M7-06） |
| `report_tools.py` | 报告写入 + 近期列表 | 已实现（M2 + M7-06） |
| `alert_tools.py` | 预警写入/去重/活跃列表 | 已实现（M2 + M7-06） |
| `rule_tools.py` | 规则匹配工具 | 已实现 |
| `system_tools.py` | 系统健康组合工具 | 已实现 |

独立任务入口：`app/tasks/run_mcp_server.py`（M7-08）——常驻 stdio MCP Server 或 `--list` 列出读类工具。

## 3. 十六个核心工具（已实现）

| # | 工具名 | 读/写 | 包装目标 | 说明 |
|---|---|---|---|---|
| 1 | `es_search_logs` | 读 | `log_query_service.search_logs` | 关键词、日志类型与时间窗口过滤 |
| 2 | `es_aggregate_metrics` | 读 | `aggregation_service` | 六类模板聚合（流量/错误/延迟/行为漏斗/安全/基础设施） |
| 3 | `es_get_trace_context` | 读 | `context_service` | 按 trace_id 拉取关联日志 |
| 4 | `es_get_service_window` | 读 | `context_service` | 按服务名与时间窗口拉取服务级日志 |
| 5 | `es_get_similar_errors` | 读 | `context_service` | 按错误码与时间窗口统计同类错误 |
| 6 | `analysis_write_report` | 写 | `report_service.write_report` | 持久化分析报告（默认不对外暴露） |
| 7 | `alert_write_event` | 写 | `alert_service` | 写入预警事件（默认不对外暴露） |
| 8 | `alert_check_duplicate` | 读 | `dedup_service` | 检查候选预警是否在时间桶内重复 |
| 9 | `system_health_check` | 读 | ES/Kafka/Docker 健康快照组合 | 无入参，返回组合健康状态 |
| 10 | `rule_match_log` | 读 | `rule_engine.match_log` | 对单条日志事件复核规则命中 |
| 11 | `es_get_business_funnel` | 读 | `aggregation_service`（行为漏斗） | 各环节转化与流失统计 |
| 12 | `es_detect_traffic_peak` | 读 | `aggregation_service`（流量峰值） | 识别时间桶峰值与 `peak_bucket` |
| 13 | `es_compare_time_windows` | 读 | `aggregation_service`（双窗对比） | 双时间窗口指标环比；超长窗口返回结构化错误 |
| 14 | `kibana_generate_link` | 读 | `kibana_tools`（离线拼装） | 生成 Kibana Discover 跳转链接，不访问网络 |
| 15 | `report_list_recent` | 读 | `report_service.list_recent` | 查询最近分析报告列表 |
| 16 | `alert_list_active` | 读 | `alert_service.list_active` | 查询当前活跃预警事件列表 |

统一返回约定：`{"ok": bool, "tool": "<name>", ...}`；失败时含 `error` 字段，无 `placeholder`。

## 4. `get_langchain_tools` 读写分离约定

入口：`registry.get_langchain_tools(*, include_write_tools: bool = False)`

| 参数 | 暴露工具 | 数量 |
|---|---|---|
| `include_write_tools=False`（默认） | 读类工具 1~5、8~10、11~16 | **14 个** |
| `include_write_tools=True` | 全部 16 个（追加写类 6、7） | **16 个** |

写类工具名（`_WRITE_TOOL_NAMES`）：`analysis_write_report`、`alert_write_event`。

设计意图：

- LangGraph 分析节点默认仅挂载读工具。
- `persist` 节点或显式 `include_write_tools=True` 时才暴露写类工具，避免 LLM 在推理阶段随意写入报告/预警。
- **MCP Server 仅暴露读类 14 个**；写类 6、7 不对外注册。

注册顺序与 `list_registered_tool_names()` 一致（稳定 16 项）。

## 5. MCP Server（M7-07 / M7-08）

### 5.1 `create_mcp_server()` 形态

```text
create_mcp_server()
  ├─ fastmcp 未安装 → {"ok": false, "error": "fastmcp 未安装"}（不抛异常）
  └─ 成功 → FastMCP("elk-log-analysis") 实例
        └─ 遍历 get_langchain_tools(include_write_tools=False)
              └─ mcp.add_tool(...)  # 仅 14 个读类工具
```

- **懒加载**：`from fastmcp import FastMCP` 在函数体内 import；未安装时不影响 LangChain 进程内 `get_langchain_tools`。
- **适配层**：`_structured_tool_to_mcp_callable` 将 StructuredTool 转为 FastMCP 可注册签名（单 Pydantic 入参或无参）。
- **常驻**：由 task 层调用 `server.run()`（stdio transport）。

### 5.2 `run_mcp_server` 任务入口（`app/tasks/run_mcp_server.py`）

| 用法 | 行为 |
|---|---|
| `python -m app.tasks.run_mcp_server --list` | 打印读类工具名（共 14 个）后退出；fastmcp 缺失时回退 `get_langchain_tools` 列表 |
| `python -m app.tasks.run_mcp_server` | 创建 MCP Server 并 `run()` 常驻；fastmcp 缺失时 stderr 提示并 `exit(1)` |
| 依赖边界 | 仅 import `registry.create_mcp_server`，不直接拼装工具 |

## 6. 已实现功能清单

- [x] ES 五工具薄包装（M2-01）
- [x] `system_health_check` 薄包装（M2-02）
- [x] `rule_match_log` 薄包装（M2-03）
- [x] `analysis_write_report` 薄包装（M2-04）
- [x] `alert_write_event` / `alert_check_duplicate` 薄包装（M2-05）
- [x] `registry` StructuredTool 注册 + 读写分离（M2-06）
- [x] `tests/test_m2_tools.py` 单元测试（M2-07，21 passed）
- [x] 本 DEV 文档 M2 收敛（M2-08）
- [x] ES 增强工具 11/12/13（M7-05）
- [x] `kibana_generate_link` / `report_list_recent` / `alert_list_active`（M7-06）
- [x] 16 工具注册 + `create_mcp_server` FastMCP 懒加载（M7-07）
- [x] `run_mcp_server` 任务入口（M7-08）

## 7. 待开发功能清单

| 优先级 | 项 | 说明 |
|---|---|---|
| P3 | `test_m7_enhancements` | M7-09：16 工具、MCP 降级、七节点子图回归 |
| P3 | MCP 与 LangGraph 节点联调 | 依赖诊断编排接入 MCP 客户端 |

## 8. 模块状态表

| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| `elasticsearch_tools` | 已实现 | 2026-06-22 | ES 工具 Agent (M7-05) | 低 | 工具 1~5、11~13 |
| `kibana_tools` | 已实现 | 2026-06-22 | 辅助工具 Agent (M7-06) | 低 | 工具 14 |
| `report_tools` / `alert_tools` | 已实现 | 2026-06-22 | 辅助工具 Agent (M7-06) | 低 | 写工具 + 列表读工具 15/16 |
| `registry` | 已实现 | 2026-06-22 | 注册中心 Agent (M7-07) | 低 | 16 注册；MCP 仅 14 读类 |
| `run_mcp_server` | 已实现 | 2026-06-22 | 任务入口 Agent (M7-08) | 低 | --list / 常驻 stdio |
| Tools 层（整体） | **M2 + M7 完成** | 2026-06-22 | 文档 Agent (M7-10) | 低 | LangChain + MCP 双出口可用 |

## 9. 禁止重复实现清单

| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| ES 查询逻辑 | `elasticsearch/*_service.py` | 禁止在 tools 内重写 DSL |
| 写报告/预警 | `report/`、`alert/` | 禁止 LLM 自由选择写类工具（须走读写分离） |
| StructuredTool 注册 | `registry.py` | 禁止在各 `*_tools.py` 内重复注册 |
| MCP Server 创建 | `registry.create_mcp_server` | 禁止在 task 层重复拼装 FastMCP |

## 10. 真实实现与设计愿景差异

| 维度 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 调用形态 | LangChain + MCP 双出口 | 均已实装；fastmcp 缺失时 MCP 结构化降级 | 集成环境 `pip install fastmcp` |
| 工具暴露策略 | 分析阶段只读、持久化阶段可写 | `include_write_tools` 已实现；MCP 仅读类 | LangGraph 节点按阶段传参 |
| 工具数量 | 第一阶段 10 + M7 增强 6 | 16 工具全注册 | M7-09 单测覆盖 |

## 11. 开发日志区

| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-06-16 | 建立 tools 六文件占位 + Pydantic 入参模型 | `app/services/tools/*.py` | 工具函数返回 placeholder | — |
| 2026-06-17 | M2-01~06 逐文件实装 + registry 注册 | `elasticsearch_tools.py` 等 | 10 工具无 placeholder，StructuredTool 可 invoke | — |
| 2026-06-17 | M2-07 单元测试 | `tests/test_m2_tools.py` | 21 passed，mock 覆盖全工具与异常路径 | integration mark 已注册 |
| 2026-06-17 | M2-08 文档收敛 | `app/services/tools/DEV.md` | 模块总览/状态表/读写分离/10 工具清单与代码一致 | — |
| 2026-06-22 | M7-05：ES 增强工具 11~13 | `elasticsearch_tools.py` | funnel / peak / compare 薄包装 | — |
| 2026-06-22 | M7-06：辅助工具 14~16 | `kibana_tools.py` 等 | 链接生成 + 列表查询 | — |
| 2026-06-22 | M7-07：16 工具注册 + MCP Server | `registry.py`, `requirements.txt` | create_mcp_server 懒加载 FastMCP | — |
| 2026-06-22 | M7-08：run_mcp_server 任务入口 | `tasks/run_mcp_server.py` | --list 14 读类；缺失 fastmcp exit(1) | — |
| 2026-06-22 | **M7-10：文档收口** | `tools/DEV.md` | 16 工具表、MCP 形态、读写分离、run_mcp_server 已记录 | 单测见 M7-09 |
