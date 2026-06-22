# M3-06：周期报告 Chain report_chain

## Agent 角色

报告链 Agent — 基于证据包生成周期分析报告，LLM 不可用时降级为模板报告。

## 唯一负责文件

```
app/services/langchain/report_chain.py
```

## 禁止修改

- llm_manager / prompts / output_parsers / evidence_builder / chain_schemas（只 import）
- diagnosis_chain、analysis/*

## 前置依赖

- M3-01 ~ M3-05 均为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.langchain.llm_manager import is_llm_available; from app.services.langchain.prompts import get_prompt; from app.services.langchain.output_parsers import parse_with_retry; from app.services.langchain.evidence_builder import build_evidence_package; from app.services.langchain.chain_schemas import ReportChainOutput; print('deps ok')"
```

## 开发要求

### `generate_periodic_report(evidence_package: dict) -> dict`
流程：
1. LLM 可用：用 `prompts.get_prompt("report")` + `llm_manager.invoke_structured("report", ...)` → `output_parsers` 解析为 `ReportChainOutput`
2. LLM 不可用或解析失败：**降级**为基于证据包 `summary`/`metrics` 的模板拼接报告（`risk_level` 由指标规则给出）
3. 统一返回结构化 dict（含 `ok`、`degraded: bool`、报告字段），**无 placeholder**

### 约定
- 不直接 import LLM SDK，统一走 `llm_manager`
- 任一异常捕获后降级，不抛裸异常
- 报告字段与 `ReportChainOutput` 对齐

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | mock LLM 可用时返回符合 `ReportChainOutput` 的结构 |
| AC-02 | LLM 不可用时返回降级报告且 `degraded: True`，不报错 |
| AC-03 | 无 placeholder 键 |
| AC-04 | 更新 `task_m3/STATUS.md` 本行 |
