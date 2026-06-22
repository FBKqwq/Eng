# M6-07：M6 文档收敛 dev_docs

## Agent 角色

文档 Agent — 更新 analysis、langchain、api 模块 DEV 文档（不碰业务代码）。

## 唯一负责文件

```
app/services/analysis/DEV.md
app/services/langchain/DEV.md
app/api/DEV.md
```

## 禁止修改

- 任何 `.py` 文件

## 前置依赖

- M6-02 ~ M6-05 完成（可与 M6-06 并行）

## 开发要求

### analysis/DEV.md
1. `graph_main` 由「占位（M6）」→「已实现」；记录主图节点流与持久化收口
2. 说明 scheduler / trigger_scanner 已收敛为委托主图
3. `analyze_relations` 仍标 M7

### langchain/DEV.md
1. `alert_chain` 由「占位」→「已实现」；记录降级策略
2. `relation_chain` 仍标 M7

### api/DEV.md
1. 新增 `/api/v1/analysis/runs/recent`、`/api/v1/analysis/run` 说明
2. 补充 node_trace 前端展示用途

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | 三 DEV.md 与 M6 代码一致 |
| AC-02 | 主图节点流、持久化收口、轨迹 API 已记录 |
| AC-03 | 更新 `task_m6/STATUS.md` 本行；若 M6-06 亦完成，备注「M6 里程碑可收口」 |
