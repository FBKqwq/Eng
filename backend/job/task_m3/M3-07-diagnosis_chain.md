# M3-07：根因诊断 Chain diagnosis_chain

## Agent 角色

诊断链 Agent — 基于证据包推断根因并生成事件诊断报告，LLM 不可用时降级为规则结论。

## 唯一负责文件

```
app/services/langchain/diagnosis_chain.py
```

## 禁止修改

- llm_manager / prompts / output_parsers / evidence_builder / chain_schemas（只 import）
- report_chain、analysis/*

## 前置依赖

- M3-01 ~ M3-05 均为 `已完成`/`已合并`

## 开发要求

### 1. `infer_root_cause(evidence_package: dict) -> dict`
- LLM 可用：`prompts.get_prompt("diagnosis")` + `invoke_structured("diagnosis", ...)` → 解析为 `DiagnosisChainOutput`
- 降级：基于证据包 top_error_codes / top_services 给出规则化根因与较低置信度
- 返回含 `ok`、`degraded`、`root_cause`、`confidence` 等，**无 placeholder**

### 2. `generate_event_report(evidence_package: dict) -> dict`
- 可与 `infer_root_cause` 合并为一次 LLM 调用（推荐），输出事件诊断报告结构
- 降级同上

### 3. 约定
- 统一走 `llm_manager`，不直接 import LLM SDK
- 异常捕获降级，不抛裸异常
- 字段与 `DiagnosisChainOutput` 对齐；可复用 `schemas/diagnosis.py` 枚举

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | mock LLM 可用时返回符合 `DiagnosisChainOutput` 的结构 |
| AC-02 | LLM 不可用时降级且 `degraded: True`，不报错 |
| AC-03 | 两函数均无 placeholder 键 |
| AC-04 | 更新 `task_m3/STATUS.md` 本行 |
