# M3-01：LLM 模型管理 llm_manager

## Agent 角色

LLM 接入专项 Agent — 实现多模型管理、可用性探测与结构化调用入口。

## 唯一负责文件

```
app/services/langchain/llm_manager.py
```

## 可附加修改

```
requirements.txt   # 追加 langchain-openai（或兼容供应商客户端）
```

## 禁止修改

- `core/config.py`（LLM 配置项已就绪，只读）
- 其他 langchain / analysis / tools 文件

## 前置依赖

- M2 完成
- 必读：`core/config.py` 的 `llm_provider`/`llm_api_key`/`llm_base_url`/`llm_default_model`/`llm_analysis_model`/`llm_timeout_seconds`/`llm_temperature`

## 开发要求

### 1. `is_llm_available() -> bool`
- 无 `llm_api_key` 时返回 `False`（链层据此降级）
- 有 key 时返回 `True`（不强制真实联网）

### 2. `get_llm(task: TaskKind = "report")`
- `TaskKind = Literal["report", "diagnosis", "relation", "alert", "json_repair"]`
- 按任务选模型：`report`/`alert`/`json_repair` → `llm_default_model`；`diagnosis`/`relation` → `llm_analysis_model`
- 返回 LangChain ChatModel 实例（`ChatOpenAI` 等），配置 base_url/timeout/temperature
- 不可用时返回 `None`

### 3. `invoke_structured(task, prompt, output_schema) -> dict`
- LLM 不可用 → 返回 `{"ok": False, "available": False, "reason": "llm_unavailable"}`（**不带 placeholder**）
- 可用 → 调用模型，结合 `output_parsers.parse_with_retry` 产出结构化 dict（可由调用方传入 parser，或本函数内引用）
- 捕获异常 → `{"ok": False, "error": ...}`，不抛裸异常

### 4. 依赖
- `requirements.txt` 追加 `langchain-openai`（与 langchain-core 版本兼容）

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | 无 API Key 时 `is_llm_available()` 为 False |
| AC-02 | `get_llm` 按任务返回不同模型名（可 mock 验证） |
| AC-03 | `invoke_structured` 在不可用时返回结构化降级 dict，无 placeholder |
| AC-04 | requirements 含 langchain-openai |
| AC-05 | 更新 `task_m3/STATUS.md` 本行 |
