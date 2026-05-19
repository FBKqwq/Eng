# Diagnosis 服务模块 DEV 文档

## 1. 文档用途说明
本文档用于维护 `app/services/diagnosis/` 的规则分流与智能诊断实现状态，确保规则引擎优先、分析编排集中，避免在 API 层重复规则或与 ES/Kafka 逻辑混杂。

## 2. 项目模块总览
| 文件 | 主要职责 |
|---|---|
| `app/services/diagnosis/rule_engine.py` | 基于关键词的规则分流与异常类型归类 |
| `app/services/diagnosis/analyzer.py` | 诊断编排入口：调用规则引擎并组装诊断结果 |

## 3. 模块职责边界
- 应该放在这里：规则分流、诊断流程编排、与 LangChain/LangGraph 的对接封装（若实现）。
- 不应该放在这里：HTTP 路由、Pydantic 契约定义、ES DSL、Kafka 生产。

## 4. 已实现功能清单
- 已实现 `classify_by_rules` 关键词规则分流（超时/支付等分支）。
- `analyze_logs` 已接入规则结果并返回结构化占位诊断（含 route、严重度、建议列表）。
- `DiagnosisRequest.keyword` 已补齐，诊断接口兼容前端自由输入，不再访问不存在字段。
- `analyze_logs` 可通过 ES 日志查询服务拉取上下文摘要和证据日志；ES 不可用时保持稳定返回。

## 5. 待开发功能清单（P0-P3）
- P0：在 ELK 服务启动后完成真实诊断证据命中联调。
- P1：规则引擎扩展为可配置规则表或策略文件，避免硬编码关键词。
- P2：LangChain 调用层封装（prompt、解析、错误处理）。
- P3：LangGraph 状态机编排与可观测节点日志。

## 6. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| Diagnosis Service | 可用但需完善 | 2026-05-18 | codex | 中 | 规则分流与 ES 上下文入口已接通；LLM/图未接通 |

## 7. 禁止重复实现清单
| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| 规则分流 | `app/services/diagnosis/rule_engine.py` | 禁止在 `analyzer.py` 或 `api/v1/diagnosis.py` 重复写同类 if/关键词规则 |
| 诊断结果组装 | `app/services/diagnosis/analyzer.py` | 禁止在 API 路由内拼装完整诊断业务对象 |

## 8. 真实实现与设计愿景差异
| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 智能诊断闭环 | 规则分流 → 上下文检索 → LLM/图式分析 → 可解释结构化结果 | 规则与 ES 上下文入口可用，LLM/图式分析未接入 | 用真实 ES 数据完善证据摘要，再按需接入 LangChain/LangGraph |

## 9. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-05-11 | 初始化 Diagnosis 模块 DEV 文档 | `app/services/diagnosis/DEV.md` | 建立诊断模块维护基线 | 待代码变更后按 13.3 同步更新各表 |
| 2026-05-18 | 修复诊断请求字段不匹配并接入 ES 上下文查询 | `app/schemas/diagnosis.py`、`app/services/diagnosis/analyzer.py`、`app/services/diagnosis/rule_engine.py` | `/api/v1/diagnosis` 不再因 `payload.keyword` 缺失崩溃，可返回规则诊断与上下文摘要 | 当前仍未接 LangChain/LangGraph |
