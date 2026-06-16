# LangChain 能力层 DEV 文档

## 1. 文档用途说明
维护 `app/services/langchain/` 模型调用层占位与后续实现状态。LangChain 负责 Prompt、模型管理、结构化输出、证据压缩；不得承担流程编排（属 `analysis/`）。

## 2. 模块总览
| 文件 | 职责 | 状态 |
|---|---|---|
| `llm_manager.py` | 多模型、API Key、重试 | 占位 |
| `prompts.py` | 五类 Prompt 模板 | 占位 |
| `output_parsers.py` | Pydantic 输出解析与 JSON 修复重试 | 占位 |
| `evidence_builder.py` | 原始日志压缩为证据包 | 占位 |
| `report_chain.py` | 周期报告 Chain | 占位 |
| `diagnosis_chain.py` | 根因诊断 Chain | 占位 |
| `relation_chain.py` | 隐藏关系发现 Chain | 占位 |
| `alert_chain.py` | 预警解释 Chain | 占位 |

## 3. 模块职责边界
- 应该放在这里：LLM 调用、Prompt、输出解析、证据压缩。
- 不应该放在这里：ES 查询、图节点路由、API 路由、预警持久化。

## 4. 已实现功能清单
- 全部文件占位骨架已建立，函数签名与降级路径注释已对齐总体规划 §2.6/2.7。

## 5. 待开发功能清单
- P0（M3）：`llm_manager` + `prompts` + `output_parsers` + `evidence_builder`。
- P0（M3）：`report_chain` + `diagnosis_chain`。
- P2（M7）：`relation_chain` + `alert_chain`。

## 6. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| LangChain 层 | 占位 | 2026-06-16 | elk-backend-agent | 高 | 无 LLM Key 时所有节点走降级 |

## 7. 禁止重复实现清单
| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| LLM 调用 | `langchain/llm_manager.py` | 禁止在 `analysis/` 图节点内直接 new ChatOpenAI |
| 证据压缩 | `langchain/evidence_builder.py` | 禁止在 Chain 文件内重复写采样逻辑 |

## 8. 真实实现与设计愿景差异
| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 模型调用层 | 按任务选模型、结构化输出、可重试 | 仅占位函数 | M3 配置 `LLM_API_KEY` 后实现 |

## 9. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-06-16 | 按总体规划建立 LangChain 八文件占位骨架 | `app/services/langchain/*.py` | import 通过；`is_llm_available()` 恒为 False | 待 M3 接入真实供应商 |
