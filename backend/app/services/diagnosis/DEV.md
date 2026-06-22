# Diagnosis 服务模块 DEV 文档

## 1. 文档用途说明
本文档用于维护 `app/services/diagnosis/` 的规则分流与智能诊断实现状态，确保规则引擎优先、分析编排集中，避免在 API 层重复规则或与 ES/Kafka 逻辑混杂。

## 2. 项目模块总览
| 文件 | 主要职责 | 状态 |
|---|---|---|
| `app/services/diagnosis/rule_definitions.py` | 声明式规则表（三类规则共 10 条） | 已实现（M5） |
| `app/services/diagnosis/rule_engine.py` | 规则分流；`match_log` 读取声明式规则并输出 `trigger_subgraph` | 已实现（M5） |
| `app/services/diagnosis/analyzer.py` | 同步诊断门面；复杂任务转交 `analysis/` 层 | 已实现（M1/M3） |

## 3. 模块职责边界
- 应该放在这里：规则分流、诊断流程编排、与 LangChain/LangGraph 的对接封装（若实现）。
- 不应该放在这里：HTTP 路由、Pydantic 契约定义、ES DSL、Kafka 生产。

## 4. 已实现功能清单
- 已实现 `classify_by_rules` 关键词规则分流（超时/支付等分支），供 `/api/v1/diagnosis` 同步诊断 API 使用。
- `analyze_logs` 已接入规则结果并返回结构化诊断（含 route、严重度、建议列表）。
- `DiagnosisRequest.keyword` 已补齐，诊断接口兼容前端自由输入，不再访问不存在字段。
- `analyze_logs` 可通过 ES 日志查询服务拉取上下文摘要和证据日志；ES 不可用时保持稳定返回。
- **`rule_definitions.py`（M5）**：集中声明三类规则，共 10 条；`get_rule_definitions()` 返回完整列表。
- **`rule_engine.match_log`（M5）**：对单条日志事件执行声明式规则匹配，返回结构化命中结果（含 `trigger_subgraph` 标记）。

### 4.1 三类规则与 trigger_subgraph 语义

| 规则类型 `kind` | 条数 | 匹配方式 | 单条日志可命中 | trigger_subgraph 说明 |
|---|---|---|---|---|
| `error_code` | 4 | `log_event.error_code` 精确等于 `match.error_code` | 是 | PAY_FAIL、DB_TIMEOUT、CIRCUIT_OPEN、UNAVAILABLE 均为 `True` |
| `threshold` | 3 | 数值字段与阈值比较（`>=` / `>` 等） | 是 | 5xx（`status_code >= 500`）为 `True`；响应过慢类为 `False`（仅标记，不触发子图） |
| `frequency` | 3 | 依赖 aggregation 计数（`group_by` + 时间窗 + `min_count`） | **否**（单条日志 `match_log` 恒返回未命中） | 定义中标记 `True` 的规则（如 R_FREQ_SERVICE_ERROR）需后续聚合层实现 |

**`trigger_subgraph` 语义**：
- `True`：命中后由 `trigger_scanner` 拉取并复核，进入 `graph_rule.run_rule_subgraph` 深挖链路。
- `False`：规则可命中并返回严重度，但不进入规则子图（如慢响应阈值、频率类占位规则）。
- `match_log` 返回字段：`ok`、`matched`、`rule_id`、`rule_name`、`severity`、`trigger_subgraph`、`log_event_id`。

**规则 ID 一览**（供联调参考）：

| rule_id | kind | trigger_subgraph |
|---|---|---|
| R_PAY_FAIL | error_code | True |
| R_DB_TIMEOUT | error_code | True |
| R_CIRCUIT_OPEN | error_code | True |
| R_UNAVAILABLE | error_code | True |
| R_STATUS_CODE_5XX | threshold | True |
| R_RESPONSE_TIME_SLOW | threshold | False |
| R_REQUEST_TIME_SLOW | threshold | False |
| R_FREQ_SERVICE_ERROR | frequency | True（需聚合，单条不命中） |
| R_FREQ_IP_ACCESS | frequency | False |
| R_FREQ_USER_FAIL | frequency | True（需聚合，单条不命中） |

## 5. 待开发功能清单（P0-P3）
- P0：在 ELK 服务启动后完成真实诊断证据命中联调。
- P1：频率规则聚合层（`frequency` kind）接入 ES 聚合，使 R_FREQ_* 规则可真正触发子图。
- P2：`classify_by_rules` 与 `match_log` 语义收敛（关键词分流 vs 声明式规则统一出口）。
- P3：复杂诊断经 `analysis/graph_main` 主图路由（M6）。

## 6. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| `rule_definitions` | 已实现（M5） | 2026-06-22 | M5-03 Agent | 低 | 10 条声明式规则 |
| `rule_engine.match_log` | 已实现（M5） | 2026-06-22 | M5-04 Agent | 低 | error_code/threshold 可命中；frequency 单条不命中 |
| `rule_engine.classify_by_rules` | 已实现（M1） | 2026-06-16 | elk-backend-agent | 低 | 关键词分流，诊断 API 主路径 |
| `analyzer` | 已实现（M1/M3） | 2026-06-16 | elk-backend-agent | 中 | ES 上下文可降级 |
| Diagnosis Service 整体 | M5 规则层可用 | 2026-06-22 | M5-10 Agent | 中 | 频率规则聚合待 P1 |

## 7. 禁止重复实现清单
| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| 规则分流 | `app/services/diagnosis/rule_engine.py` | 禁止在 `analyzer.py` 或 `api/v1/diagnosis.py` 重复写同类 if/关键词规则 |
| 声明式规则表 | `app/services/diagnosis/rule_definitions.py` | 禁止在 `rule_engine.py` 或 `trigger_scanner.py` 硬编码规则列表 |
| 诊断结果组装 | `app/services/diagnosis/analyzer.py` | 禁止在 API 路由内拼装完整诊断业务对象 |
| 规则子图编排 | `app/services/analysis/graph_rule.py` | 禁止在 diagnosis 域内实现 LangGraph 节点 |

## 8. 真实实现与设计愿景差异
| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 智能诊断闭环 | 规则分流 → 上下文检索 → LLM/图式分析 → 可解释结构化结果 | 声明式 `match_log` + 规则子图（M5）已接通；`classify_by_rules` 仍为关键词路径 | 频率规则聚合；主图收敛（M6） |
| 频率规则 | 短时 ERROR 激增等由 ES 聚合触发 | `frequency` 规则已声明，单条 `match_log` 不命中 | P1 实现聚合扫描或并入 trigger_scanner 扩展查询 |

## 9. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-05-11 | 初始化 Diagnosis 模块 DEV 文档 | `app/services/diagnosis/DEV.md` | 建立诊断模块维护基线 | — |
| 2026-05-18 | 修复诊断请求字段不匹配并接入 ES 上下文查询 | `app/schemas/diagnosis.py`、`analyzer.py`、`rule_engine.py` | `/api/v1/diagnosis` 可返回规则诊断与上下文摘要 | 未接 LangGraph |
| 2026-06-16 | 新增 rule_definitions 与 match_log 占位 | `rule_definitions.py`、`rule_engine.py` | 为 M5 规则子图预留接口 | 已由 M5-03/04 实现 |
| 2026-06-22 | M5-03：声明式规则表 10 条 | `rule_definitions.py` | 三类规则 + trigger_subgraph 标记就绪 | frequency 需聚合层 |
| 2026-06-22 | M5-04：match_log 读 rule_definitions | `rule_engine.py` | PAY_FAIL/5xx 可命中；frequency 单条不命中 | classify_by_rules 仍独立 |
| 2026-06-22 | M5-10：DEV 文档收敛 | `diagnosis/DEV.md` | 三类规则与 trigger_subgraph 语义已记录 | 频率规则 P1 |
