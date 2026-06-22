# M7-03：隐藏关系发现 Chain（discover_relations）

## Agent 角色

关系发现 Chain Agent — 实装 `discover_relations`，LLM 推断隐藏关系，不可用时降级。

## 唯一负责文件

```
app/services/langchain/relation_chain.py
```

## 禁止修改

- prompts / chain_schemas / llm_manager / output_parsers / evidence_builder（只 import）
- 其他 langchain / analysis 文件

## 前置依赖

- M7-01（RELATION_PROMPT）为 `已完成`/`已合并`
- M7-02（RelationChainOutput）为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.langchain.prompts import get_prompt; from app.services.langchain.chain_schemas import RelationChainOutput; from app.services.langchain.llm_manager import llm_manager; print('deps ok' if get_prompt('relation') and not get_prompt('relation').startswith('[M7') else 'prompt not ready')"
```

## 详细任务内容

将当前占位实现替换为投产实现：

### `discover_relations(evidence_package: dict) -> dict`
1. **LLM 可用路径**：
   - 取 `get_prompt("relation")`；
   - 通过 `llm_manager` 的结构化调用（参照 `report_chain` / `diagnosis_chain` 现有调用方式：`invoke_structured` + `output_parsers` 解析为 `RelationChainOutput`）；
   - 把 `evidence_package` 作为输入上下文传入；
   - 成功时返回 `{"ok": True, "degraded": False, "relations": [RelationItem.model_dump(), ...]}`。
2. **降级路径**（LLM 不可用 / 调用失败 / 解析失败）：
   - 返回 `{"ok": True, "degraded": True, "relations": []}`；
   - 不抛异常、不阻塞定时子图（节点据此跳过）。
3. **结构契约**：返回 dict 始终含 `ok` / `degraded` / `relations` 三键；**无 `placeholder` 键**。

### 实现参考
- 参照 `report_chain.py` 的「LLM 可用判定 + 结构化调用 + 解析 + 降级」骨架，保持本层一致风格。
- 不直接 import LLM SDK，统一走 `llm_manager`。

### 约定
- 简体中文；不要 commit。

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | LLM 可用（mock）时返回非空 relations，结构与 RelationChainOutput 对齐 |
| AC-02 | LLM 不可用 / 解析失败时降级返回空 relations、degraded=True，不抛异常 |
| AC-03 | 无 placeholder 键 |
| AC-04 | 更新 `task_m7/STATUS.md` 中 M7-03 行 |
