# LangChain 能力层 DEV 文档

## 1. 文档用途说明

维护 `app/services/langchain/` 模型调用层实现状态。LangChain 负责 Prompt、模型管理、结构化输出、证据压缩；不得承担流程编排（属 `analysis/`）。

## 2. 模块总览

| 文件 | 职责 | 状态 | 里程碑 |
|---|---|---|---|
| `llm_manager.py` | 多模型、API Key、重试、结构化调用入口 | 已实现 | M3-01 |
| `prompts.py` | 五类 Prompt 模板（report/diagnosis/evidence_summary/alert/relation） | 已实现 | M3-02 |
| `output_parsers.py` | Pydantic 输出解析、JSON 提取/清洗、可选 LLM 修复重试 | 已实现 | M3-03 |
| `evidence_builder.py` | 原始日志压缩为证据包（分层采样、ERROR 优先） | 已实现 | M3-04 |
| `chain_schemas.py` | 链层 I/O 模型（ReportChainOutput / DiagnosisChainOutput） | 已实现 | M3-05 |
| `report_chain.py` | 周期报告 Chain（LLM + summary/metrics 规则降级） | 已实现 | M3-06 |
| `diagnosis_chain.py` | 根因诊断 Chain（LLM + 规则降级） | 已实现 | M3-07 |
| `relation_chain.py` | 隐藏关系发现 Chain | 占位 | **M7** |
| `alert_chain.py` | 预警解释 Chain | 已实现 | **M6-01** |

## 3. 模块职责边界

- 应该放在这里：LLM 调用、Prompt、输出解析、证据压缩、链层结构化输出模型。
- 不应该放在这里：ES 查询、图节点路由、API 路由、预警持久化。

## 4. 已实现功能清单

### M3 已完成（2026-06-22）

- **`llm_manager`**：`is_llm_available()` / `get_llm(task)` / `invoke_structured()`；按任务类型选模型（diagnosis/relation → analysis 模型，其余 → default）；无 Key 或 langchain-openai 未安装时返回 None / 降级 dict。
- **`prompts`**：report、diagnosis、evidence_summary、alert 四套可用模板；relation 模板占位标注 M7；`get_prompt(name)` 未知名称返回空串。
- **`output_parsers`**：`parse_with_retry()` 三路径——直接 JSON 提取 → 代码清洗（去尾逗号）→ 可选 `json_repair` 轻量 LLM 修复；失败返回 `{ok: false, error, raw_preview}`。
- **`evidence_builder`**：`build_evidence_package()` 纯代码压缩；ERROR/WARN 分层采样、分组统计、空输入安全返回。
- **`chain_schemas`**：`ReportChainOutput` / `DiagnosisChainOutput` 字段与 prompts 模板对齐，供 parsers 与两条主 Chain 共用。
- **`report_chain`**：`generate_periodic_report()` LLM 结构化路径 + `_build_template_report()` 规则降级；返回含 `ok`、`degraded`、`report_type`、`title`、`risk_level`、`summary`、`key_findings`、`recommendations`。
- **`diagnosis_chain`**：`infer_root_cause()` / `generate_event_report()` 共用 `_resolve_diagnosis()`；LLM 路径 + `_rule_degrade_diagnosis()` 规则降级；返回含 `ok`、`degraded` 及 DiagnosisChainOutput 字段。
- **`alert_chain`（M6-01）**：`explain_alert()` LLM 结构化路径（`ALERT_PROMPT` + `_AlertLlmOutput`）+ `_build_template_alert()` 模板降级；返回含 `ok`、`degraded`、`title`、`detail`；由主图 `alert_decision` 节点调用。
- **`tests/test_m3_langchain.py`（M3-08）**：22 个用例全 mock；覆盖 llm_manager 降级、prompts、output_parsers 三路径、evidence_builder、chain_schemas、report/diagnosis 双路径、无 `placeholder` 键。

### 仍为占位

- **`relation_chain`**：`discover_relations()` 返回 `placeholder: true`，待 M7 实现。

## 5. 待开发功能清单

- P2（M7）：`relation_chain` + `RELATION_PROMPT` + 关系发现 schema。

## 6. 模块状态表

| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/Agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| `llm_manager` | 已实现 | 2026-06-22 | elk-backend-agent (M3-01) | 低 | 依赖 `LLM_API_KEY`；无 Key 时链层走降级 |
| `prompts` | 已实现 | 2026-06-22 | Prompt 工程 Agent (M3-02) | 低 | relation 模板仅占位说明 |
| `output_parsers` | 已实现 | 2026-06-22 | output-parsers-agent (M3-03) | 低 | LLM 修复路径依赖 `json_repair` 任务模型 |
| `evidence_builder` | 已实现 | 2026-06-22 | elk-backend-agent (M3-04) | 低 | 纯代码，无 LLM 依赖 |
| `chain_schemas` | 已实现 | 2026-06-22 | elk-backend-agent (M3-05) | 低 | 链层字段真相源 |
| `report_chain` | 已实现 | 2026-06-22 | elk-backend-agent (M3-06) | 低 | LLM 不可用时规则模板报告 |
| `diagnosis_chain` | 已实现 | 2026-06-22 | elk-backend-agent (M3-07) | 低 | 规则降级 confidence 固定 0.4 |
| `relation_chain` | 占位 | 2026-06-16 | elk-backend-agent | 高 | **M7** 实现 |
| `alert_chain` | 已实现 | 2026-06-22 | elk-backend-agent (M6-01) | 低 | LLM + alert_type/service/severity 模板降级 |
| LangChain 层（整体） | **M3 + M6 alert 主链路完成** | 2026-06-22 | elk-backend-agent (M6-07) | 低 | relation 待 M7 |

## 7. 降级策略与依赖关系

### 7.1 全局 LLM 可用性

```
settings.llm_api_key 非空
  → is_llm_available() == True
  → get_llm(task) 尝试 ChatOpenAI
  → invoke_structured() 调用 + parse_with_retry()
```

无 API Key、`langchain-openai` 未安装、或 `get_llm` 失败时，各 Chain **不抛异常**，改走本地规则/模板路径，并在返回中标记 `degraded: true`（或 parsers 返回 `ok: false` 由 Chain 捕获后降级）。

### 7.2 各组件降级行为

| 组件 | LLM 可用 | LLM 不可用 / 失败 |
|---|---|---|
| `llm_manager.invoke_structured` | 调用模型 + 解析 | `{ok: false, available: false, reason: "llm_unavailable"}` 或 `{ok: false, error: ...}` |
| `output_parsers.parse_with_retry` | 提取 JSON → 校验 → 可选 LLM 修复 | 返回 `{ok: false, error, raw_preview}`；修复路径在 `get_llm("json_repair")` 为 None 时跳过 |
| `report_chain` | `invoke_structured("report")` 成功 → `degraded: false` | `_build_template_report()`：由 summary/metrics 规则推断 risk_level、拼接 findings 与 recommendations → `degraded: true` |
| `diagnosis_chain` | `invoke_structured("diagnosis")` 成功 → `degraded: false` | `_rule_degrade_diagnosis()`：基于 top_error_codes/top_services 规则根因，confidence=0.4 → `degraded: true` |
| `relation_chain` | — | 恒返回 `placeholder: true`（M7 前无降级正文） |
| `alert_chain` | `invoke_structured("alert")` 成功 → `degraded: false` | `_build_template_alert()`：基于 alert_type/affected_service/severity 规则文案 → `degraded: true`；LLM 异常亦降级 |

### 7.3 Chain 依赖关系

```text
evidence_builder.build_evidence_package()
        │
        ├─► report_chain.generate_periodic_report()
        │         ├─ prompts.get_prompt("report")
        │         ├─ llm_manager.invoke_structured → output_parsers.parse_with_retry
        │         └─ chain_schemas.ReportChainOutput
        │
        └─► diagnosis_chain.infer_root_cause() / generate_event_report()
                  ├─ prompts.get_prompt("diagnosis")
                  ├─ llm_manager.invoke_structured → output_parsers.parse_with_retry
                  └─ chain_schemas.DiagnosisChainOutput

relation_chain.discover_relations()     ── 待 M7，依赖 prompts("relation") + 未来 schema
alert_chain.explain_alert()             ── M6 已实现；主图 alert_decision 调用
```

**上游**：`analysis/` 图节点调用 Chain，不直接调用 `llm_manager`。  
**下游契约**：`schemas/report.py`、`schemas/diagnosis.py` 的枚举类型被 `chain_schemas` 引用；链返回 dict 供图节点组装 API 响应。

## 8. 禁止重复实现清单

| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| LLM 调用 | `langchain/llm_manager.py` | 禁止在 `analysis/` 图节点内直接 new ChatOpenAI |
| 证据压缩 | `langchain/evidence_builder.py` | 禁止在 Chain 文件内重复写采样逻辑 |
| 链 I/O 模型 | `langchain/chain_schemas.py` | 禁止在 `schemas/*.py` 重复定义 ReportChainOutput / DiagnosisChainOutput |
| JSON 解析修复 | `langchain/output_parsers.py` | 禁止在各 Chain 内手写 parse 逻辑 |

## 9. 真实实现与设计愿景差异

| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 模型调用层 | 按任务选模型、结构化输出、可重试 | M3 已实现主链路 | 配置 `LLM_API_KEY` 后启用 LLM 路径 |
| 周期/诊断 Chain | LLM 增强 + 规则兜底 | 已实现双路径 + M3-08 单测覆盖 | — |
| 预警解释 | 候选预警可解释文案 | M6 `explain_alert` 已实现 LLM + 模板降级 | — |
| 关系发现 | 跨维度隐藏关系推断 | relation_chain 占位 | M7 填充 schema + Chain |

## 10. 开发日志区

| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-06-16 | 按总体规划建立 LangChain 八文件占位骨架 | `app/services/langchain/*.py` | import 通过；`is_llm_available()` 恒为 False | 待 M3 接入真实供应商 |
| 2026-06-22 | M3-01：llm_manager 真实实现 | `llm_manager.py`, `requirements.txt` | is_llm_available/get_llm/invoke_structured 可用 | 无 Key 时走降级 |
| 2026-06-22 | M3-02：五类 Prompt 模板 | `prompts.py` | report/diagnosis/evidence_summary/alert 可用；relation 标 M7 | relation 待 M7 |
| 2026-06-22 | M3-03：结构化输出解析 | `output_parsers.py` | JSON/代码块/清洗/可选 LLM 修复三路径 | — |
| 2026-06-22 | M3-04：证据包压缩 | `evidence_builder.py` | ERROR 优先分层采样、空输入安全 | — |
| 2026-06-22 | M3-05：链 I/O 模型 | `chain_schemas.py` | ReportChainOutput/DiagnosisChainOutput 可校验 | — |
| 2026-06-22 | M3-06：周期报告 Chain | `report_chain.py` | LLM + 模板降级；`degraded` 字段稳定 | — |
| 2026-06-22 | M3-07：根因诊断 Chain | `diagnosis_chain.py` | infer_root_cause/generate_event_report；规则降级 | — |
| 2026-06-22 | M3-08：LangChain 层单测 | `tests/test_m3_langchain.py` | 22 passed；全 mock；覆盖降级与三路径解析 | — |
| 2026-06-22 | **M3-09：文档收敛，标记 M3 主链路完成** | `DEV.md` | 七文件状态更新为已实现；降级策略与依赖关系已记录；relation→M7、alert→M5/M6 | relation/alert Chain 待后续里程碑 |
| 2026-06-22 | M6-01：alert_chain 实现 | `alert_chain.py` | explain_alert LLM + 模板降级；ok/degraded/title/detail | — |
| 2026-06-22 | **M6-07：文档收敛（M6 alert 部分）** | `DEV.md` | alert_chain 标已实现；降级策略与主图调用关系已记录 | relation_chain 待 M7 |
