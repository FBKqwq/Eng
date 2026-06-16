# Tools（MCP / Agent 工具层）DEV 文档

## 1. 文档用途说明
维护 `app/services/tools/` Agent 可调用工具薄适配层。工具只包装 services，不重新实现业务逻辑。

## 2. 模块总览
| 文件 | 职责 | 状态 |
|---|---|---|
| `registry.py` | LangChain Tool + MCP Server 双形态注册 | 占位 |
| `elasticsearch_tools.py` | ES 查询/聚合/上下文 5 工具 | 占位 |
| `report_tools.py` | 报告读写工具 | 占位 |
| `alert_tools.py` | 预警读写/去重工具 | 占位 |
| `rule_tools.py` | 规则匹配工具 | 占位 |
| `system_tools.py` | 系统健康组合工具 | 占位 |

## 3. 第一阶段 10 个核心工具（占位已声明）
`es_search_logs`、`es_aggregate_metrics`、`es_get_trace_context`、`es_get_service_window`、`es_get_similar_errors`、`analysis_write_report`、`alert_write_event`、`alert_check_duplicate`、`system_health_check`、`rule_match_log`

## 4. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| Tools 层 | 占位 | 2026-06-16 | elk-backend-agent | 高 | registry 未注册真实 StructuredTool |

## 5. 禁止重复实现清单
| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| ES 查询逻辑 | `elasticsearch/*_service.py` | 禁止在 tools 内重写 DSL |
| 写报告/预警 | `report/`、`alert/` | 禁止 LLM 自由选择写类工具 |

## 6. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-06-16 | 建立 tools 六文件占位 + Pydantic 入参模型 | `app/services/tools/*.py` | 工具函数返回 placeholder | 待 M2 接入 registry 与 service |
