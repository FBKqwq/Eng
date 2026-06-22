# M3-02：Prompt 模板 prompts

## Agent 角色

Prompt 工程 Agent — 填充周期报告 / 根因诊断 / 证据摘要的中文 Prompt 模板。

## 唯一负责文件

```
app/services/langchain/prompts.py
```

## 禁止修改

- 其他 langchain 文件、chain_schemas

## 前置依赖

- M2 完成

## 开发要求

### 1. 真实模板常量
将占位字符串替换为可用的 `ChatPromptTemplate` 或带占位符的字符串模板：
- `REPORT_PROMPT`：周期报告，输入证据包，要求输出指定 JSON 字段（与 `chain_schemas.ReportChainOutput` 对齐）
- `DIAGNOSIS_PROMPT`：根因诊断，输入证据包，输出根因/置信度/建议（与 `DiagnosisChainOutput` 对齐）
- `EVIDENCE_SUMMARY_PROMPT`：证据摘要压缩
- `ALERT_PROMPT`：保留（M5/M6 用，可填基础版）
- `RELATION_PROMPT`：保留占位标注 M7

### 2. 约定
- 模板需明确要求「仅输出 JSON，不要额外解释」，便于 output_parser 解析
- 字段名与 chain_schemas 保持一致（与 M3-05 协调；以 README §2 字段为准）
- `get_prompt(name)` 返回对应模板

### 3. 不得
- 不在本文件调用 LLM 或定义 Pydantic 业务模型

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | 五个模板常量无「占位」字样（relation 除外，可标 M7） |
| AC-02 | report/diagnosis 模板含 JSON 输出要求与字段说明 |
| AC-03 | `get_prompt` 正确映射 |
| AC-04 | 更新 `task_m3/STATUS.md` 本行 |
