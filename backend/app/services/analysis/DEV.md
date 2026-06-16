# Analysis（LangGraph 编排层）DEV 文档

## 1. 文档用途说明
维护 `app/services/analysis/` LangGraph 流程编排层。负责主图路由、定时子图、规则子图、调度与触发扫描；不得直接拼 ES DSL。

## 2. 模块总览
| 文件 | 职责 | 状态 |
|---|---|---|
| `state.py` | 统一 `AnalysisState` TypedDict | 占位 |
| `schemas.py` | TriggerEvent、NodeTraceEntry | 占位 |
| `graph_main.py` | 主图：路由、收敛、预警、持久化 | 占位 |
| `graph_scheduled.py` | 定时子图：周期体检 | 占位 |
| `graph_rule.py` | 规则子图：事件深挖 | 占位 |
| `scheduler.py` | 定时触发（15min） | 占位 |
| `trigger_scanner.py` | 规则扫描触发（30s） | 占位 |

## 3. 模块职责边界
- 应该放在这里：图状态、节点编排、条件分支、node_trace 记录。
- 不应该放在这里：ES 聚合实现、LLM Prompt、HTTP API。

## 4. 已实现功能清单
- `AnalysisState` 字段契约与主/子图文件占位已建立。

## 5. 待开发功能清单
- P0（M4）：`graph_scheduled` 最小版 + `scheduler`。
- P0（M5）：`graph_rule` 最小版 + `trigger_scanner`。
- P1（M6）：`graph_main` 收敛 + `node_trace` 前端展示。

## 6. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| Analysis 层 | 占位 | 2026-06-16 | elk-backend-agent | 高 | LangGraph 依赖未安装 |

## 7. 禁止重复实现清单
| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| ES 聚合 | `elasticsearch/aggregation_service.py` | 禁止在图节点内重写 DSL |
| 工具调用 | `tools/` 薄适配层 | 禁止图节点绕过 tools 直连 service |

## 8. 真实实现与设计愿景差异
| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 一主图+两子图 | LangGraph 编排完整闭环 | 仅占位函数 | M4/M5 按总体规划 §2.8 顺序实现 |

## 9. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-06-16 | 建立 analysis 七文件占位骨架 | `app/services/analysis/*.py` | `run_main_graph` 等返回 placeholder | 待安装 langgraph 并实现真实图 |
