# M3-03：结构化输出解析 output_parsers

## Agent 角色

输出解析 Agent — 实现 LLM 文本 → Pydantic 模型解析与 JSON 修复重试。

## 唯一负责文件

```
app/services/langchain/output_parsers.py
```

## 禁止修改

- 其他 langchain 文件

## 前置依赖

- M2 完成

## 开发要求

### 1. `parse_with_retry(raw_text, schema, *, max_retries=2) -> dict`
- 尝试从 `raw_text` 提取 JSON（容忍 ```json 代码块包裹、前后多余文本）
- 用 `schema.model_validate` 校验
- 解析失败：可调用轻量 LLM（`llm_manager.get_llm("json_repair")`）修复，或纯代码清洗重试，直到 `max_retries`
- 成功：返回 `{"ok": True, "data": <model.model_dump()>}`
- 全部失败：返回 `{"ok": False, "error": ..., "raw_preview": raw_text[:200]}`，**不带 placeholder**，不抛裸异常

### 2. 约定
- 纯解析路径不依赖网络；LLM 修复为可选增强，LLM 不可用时跳过修复直接走代码清洗
- 提供一个内部 `_extract_json(text) -> str | None` 辅助

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | 合法 JSON 文本 → `ok: True` 且 data 通过 schema 校验 |
| AC-02 | 含代码块包裹的 JSON 可被提取解析 |
| AC-03 | 非法文本 → `ok: False` 且不抛异常 |
| AC-04 | 更新 `task_m3/STATUS.md` 本行 |
