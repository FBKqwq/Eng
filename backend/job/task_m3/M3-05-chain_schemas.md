# M3-05：Chain I/O 模型 chain_schemas

## Agent 角色

Schema Agent — 新建链层输入输出 Pydantic 模型，供 report/diagnosis chain 与 output_parser 共用。

## 唯一负责文件（新建）

```
app/services/langchain/chain_schemas.py
```

## 禁止修改

- `schemas/diagnosis.py`、`schemas/report.py`（如需复用枚举，只 import）
- 其他 langchain 文件

## 前置依赖

- M2 完成
- 可参考（只读）：`schemas/diagnosis.py` 的 `SeverityLevel`、`ActionSuggestion`、`RootCauseCandidate`

## 开发要求

### 1. `ReportChainOutput`（周期报告 LLM 输出）
建议字段：
- `report_type: Literal["periodic"]`
- `title: str`
- `risk_level: str`（low/medium/high）
- `summary: str`
- `key_findings: list[str]`
- `recommendations: list[str]`

### 2. `DiagnosisChainOutput`（根因诊断 LLM 输出）
建议字段：
- `root_cause: str`
- `confidence: float`（0~1）
- `severity: str`
- `affected_services: list[str]`
- `evidence_refs: list[str]`
- `action_suggestions: list[str]`

### 3. 约定
- 可复用 `schemas/diagnosis.py` 的枚举（import，不改原文件）
- 字段名须与 `prompts.py`（M3-02）模板要求一致；以本文件为字段真相源，M3-02/06/07 对齐
- 为可选字段提供默认值，降低 LLM 漏字段导致校验失败的概率

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | 两个模型可 import 且能 `model_validate` 合法 dict |
| AC-02 | 关键字段齐全，含合理默认值 |
| AC-03 | 未修改 `schemas/*.py` 原文件 |
| AC-04 | 更新 `task_m3/STATUS.md` 本行 |
