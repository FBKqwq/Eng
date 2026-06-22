# M3-08：LangChain 层单测 test_m3_langchain

## Agent 角色

测试 Agent — 新建 M3 单测，LLM 全程 mock，不联网。

## 唯一负责文件（新建）

```
tests/test_m3_langchain.py
```

## 禁止修改

- `app/services/langchain/*.py` 生产逻辑（发现 bug 记备注，由对应任务 Agent 修）

## 前置依赖

- M3-06、M3-07 完成

## 测试范围

| 类别 | 内容 |
| --- | --- |
| llm_manager | 无 key → `is_llm_available()==False`；`invoke_structured` 降级结构 |
| prompts | `get_prompt` 五类返回非占位（relation 除外） |
| output_parsers | 合法 JSON / 代码块包裹 / 非法文本三路径 |
| evidence_builder | `sampled_count <= max_logs`；ERROR 优先；空输入 |
| chain_schemas | 两模型 `model_validate` |
| report_chain | mock LLM 可用 → 符合 schema；不可用 → degraded 降级 |
| diagnosis_chain | 同上两路径 |
| 无 placeholder | 各产出断言无 `placeholder` 键 |

≥12 个 test 函数；用 `monkeypatch` mock `llm_manager.is_llm_available` 与 `get_llm`/`invoke_structured`。

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `pytest tests/test_m3_langchain.py -v` 全绿 |
| AC-02 | 不依赖真实 LLM/ES |
| AC-03 | 覆盖降级路径 |
| AC-04 | 更新 `task_m3/STATUS.md` 本行 |
