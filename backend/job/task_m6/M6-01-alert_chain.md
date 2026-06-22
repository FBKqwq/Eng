# M6-01：预警解释 Chain alert_chain

## Agent 角色

预警文案 Agent — 为候选预警生成可解释文案，LLM 不可用时降级模板。

## 唯一负责文件

```
app/services/langchain/alert_chain.py
```

## 禁止修改

- llm_manager / prompts / output_parsers（只 import）
- 其他 langchain / analysis 文件

## 前置依赖

- M3 完成

## 开发要求

### `explain_alert(alert_candidate: dict) -> dict`
- LLM 可用：用 `prompts.get_prompt("alert")` + `llm_manager.invoke_structured("alert", ...)` 生成 `title` / `detail`（简洁中文文案）
- LLM 不可用或失败：**降级**为基于 `alert_candidate`（alert_type/affected_service/severity）的模板文案
- 返回 `{"ok": True, "degraded": bool, "title": ..., "detail": ...}`，**无 placeholder**
- 异常捕获降级，不抛裸异常

### 约定
- 统一走 `llm_manager`，不直接 import LLM SDK
- 简体中文；不要 commit

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | LLM 可用时返回 title/detail |
| AC-02 | LLM 不可用时降级模板文案，degraded=True |
| AC-03 | 无 placeholder 键，不抛裸异常 |
| AC-04 | 更新 `task_m6/STATUS.md` 本行 |
