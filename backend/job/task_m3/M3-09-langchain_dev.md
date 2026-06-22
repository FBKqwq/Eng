# M3-09：langchain 模块文档收敛

## Agent 角色

文档 Agent — 更新 `langchain/DEV.md`，标记 M3 完成状态（不碰业务代码）。

## 唯一负责文件

```
app/services/langchain/DEV.md
```

## 前置依赖

- M3-06、M3-07 完成（可与 M3-08 并行）

## 开发要求

1. 模块状态表：`llm_manager`/`prompts`/`output_parsers`/`evidence_builder`/`chain_schemas`/`report_chain`/`diagnosis_chain` 由「占位」→「已实现」
2. 记录降级策略（LLM 不可用时各 Chain 行为）
3. `relation_chain` 标注 M7、`alert_chain` 标注 M5/M6
4. 开发日志追加 M3 完成条目

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | DEV.md 与代码一致 |
| AC-02 | 降级策略、依赖关系已记录 |
| AC-03 | 更新 `task_m3/STATUS.md` 本行；若 M3-08 亦完成，备注「M3 里程碑可收口」 |
