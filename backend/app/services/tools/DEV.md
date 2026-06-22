# Tools（MCP / Agent 工具层）DEV 文档

## 1. 文档用途说明
维护 `app/services/tools/` Agent 可调用工具薄适配层。工具只包装 services，不重新实现业务逻辑。

## 2. 模块总览
| 文件 | 职责 | 状态 |
|---|---|---|
| `registry.py` | LangChain StructuredTool 注册；`get_langchain_tools` 读写分离出口 | 已实现（`create_mcp_server` 仍属 M7） |
| `elasticsearch_tools.py` | ES 查询/聚合/上下文 5 工具 | 已实现 |
| `report_tools.py` | 报告写入工具 | 已实现 |
| `alert_tools.py` | 预警写入/去重工具 | 已实现 |
| `rule_tools.py` | 规则匹配工具 | 已实现 |
| `system_tools.py` | 系统健康组合工具 | 已实现 |

## 3. 第一阶段 10 个核心工具（已实现）

| # | 工具名 | 读/写 | 包装目标 | 说明 |
|---|---|---|---|---|
| 1 | `es_search_logs` | 读 | `log_query_service.search_logs` | 关键词、日志类型与时间窗口过滤 |
| 2 | `es_aggregate_metrics` | 读 | `aggregation_service` | 六类模板聚合（流量/错误/延迟/行为漏斗/安全/基础设施） |
| 3 | `es_get_trace_context` | 读 | `context_service` | 按 trace_id 拉取关联日志 |
| 4 | `es_get_service_window` | 读 | `context_service` | 按服务名与时间窗口拉取服务级日志 |
| 5 | `es_get_similar_errors` | 读 | `context_service` | 按错误码与时间窗口统计同类错误 |
| 6 | `analysis_write_report` | 写 | `report_service.write_report` | 持久化分析报告 |
| 7 | `alert_write_event` | 写 | `alert_service` | 写入预警事件 |
| 8 | `alert_check_duplicate` | 读 | `dedup_service` | 检查候选预警是否在时间桶内重复 |
| 9 | `system_health_check` | 读 | ES/Kafka/Docker 健康快照组合 | 无入参，返回组合健康状态 |
| 10 | `rule_match_log` | 读 | `rule_engine.match_log` | 对单条日志事件复核规则命中 |

统一返回约定：`{"ok": bool, "tool": "<name>", ...}`；失败时含 `error` 字段，无 `placeholder`。

## 4. `get_langchain_tools` 读写分离约定

入口：`registry.get_langchain_tools(*, include_write_tools: bool = False)`

| 参数 | 暴露工具 | 数量 |
|---|---|---|
| `include_write_tools=False`（默认） | 读类工具 1~5、8~10 | **8 个** |
| `include_write_tools=True` | 全部 10 个（追加写类 6、7） | **10 个** |

写类工具名（`_WRITE_TOOL_NAMES`）：`analysis_write_report`、`alert_write_event`。

设计意图：LangGraph 分析节点默认仅挂载读工具；`persist` 节点或显式 `include_write_tools=True` 时才暴露写类工具，避免 LLM 在推理阶段随意写入报告/预警。

注册顺序与 `list_registered_tool_names()` 一致（稳定 10 项）。

## 5. MCP Server（第二阶段 M7）

`create_mcp_server()` 当前为占位，抛出 `NotImplementedError`，待 M7 接入 FastMCP 后实装。LangChain 进程内调用路径（`get_langchain_tools`）已可用。

## 6. 已实现功能清单
- [x] ES 五工具薄包装（M2-01）
- [x] `system_health_check` 薄包装（M2-02）
- [x] `rule_match_log` 薄包装（M2-03）
- [x] `analysis_write_report` 薄包装（M2-04）
- [x] `alert_write_event` / `alert_check_duplicate` 薄包装（M2-05）
- [x] `registry` StructuredTool 注册 + 读写分离（M2-06）
- [x] `tests/test_m2_tools.py` 单元测试（M2-07，21 passed）
- [x] 本 DEV 文档 M2 收敛（M2-08）

## 7. 待开发功能清单

| 优先级 | 项 | 说明 |
|---|---|---|
| P0 | `create_mcp_server` FastMCP 实装 | M7 里程碑 |
| P2 | `report_list_recent` / `alert_list_active` | 第二阶段只读列表工具，当前未注册至 registry |
| P3 | MCP 与 LangGraph 节点联调 | 依赖 M7 + 诊断编排 |

## 8. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| Tools 层 | 已实现 | 2026-06-17 | M2-08 文档 Agent | 低 | 10 工具已注册；MCP Server 待 M7 |

## 9. 禁止重复实现清单
| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| ES 查询逻辑 | `elasticsearch/*_service.py` | 禁止在 tools 内重写 DSL |
| 写报告/预警 | `report/`、`alert/` | 禁止 LLM 自由选择写类工具（须走读写分离） |
| StructuredTool 注册 | `registry.py` | 禁止在各 `*_tools.py` 内重复注册 |

## 10. 真实实现与设计愿景差异
| 维度 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 调用形态 | LangChain + MCP 双出口 | LangChain 已通；MCP 占位 | M7 接入 FastMCP |
| 工具暴露策略 | 分析阶段只读、持久化阶段可写 | `include_write_tools` 已实现 | LangGraph 节点按阶段传参 |
| 列表类工具 | 报告/预警近期列表 | 函数存在但未进 registry | 第二阶段评估是否注册 |

## 11. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-06-16 | 建立 tools 六文件占位 + Pydantic 入参模型 | `app/services/tools/*.py` | 工具函数返回 placeholder | — |
| 2026-06-17 | M2-01~06 逐文件实装 + registry 注册 | `elasticsearch_tools.py` 等 | 10 工具无 placeholder，StructuredTool 可 invoke | MCP 仍 M7 |
| 2026-06-17 | M2-07 单元测试 | `tests/test_m2_tools.py` | 21 passed，mock 覆盖全工具与异常路径 | integration mark 已注册 |
| 2026-06-17 | M2-08 文档收敛 | `app/services/tools/DEV.md` | 模块总览/状态表/读写分离/10 工具清单与代码一致 | `create_mcp_server` 待 M7 |
