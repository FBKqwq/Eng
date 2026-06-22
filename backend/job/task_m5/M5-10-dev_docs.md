# M5-10：M5 文档收敛 dev_docs

## Agent 角色

文档 Agent — 更新 diagnosis、alert、analysis 模块 DEV 文档（不碰业务代码）。

## 唯一负责文件

```
app/services/diagnosis/DEV.md
app/services/alert/DEV.md
app/services/analysis/DEV.md
```

## 禁止修改

- 任何 `.py` 文件

## 前置依赖

- M5-06、M5-07 完成（可与 M5-08、M5-09 并行）

## 开发要求

### diagnosis/DEV.md
1. `rule_definitions` / `rule_engine.match_log` 由「占位」→「已实现」
2. 记录三类规则与 trigger_subgraph 语义

### alert/DEV.md
1. `alert_service` 三函数、`dedup.check_duplicate` 由「占位」→「已实现」
2. 记录 `alerts-*` 状态机与幂等键约定

### analysis/DEV.md
1. `graph_rule` / `trigger_scanner` 由「占位（M5）」→「已实现（M5 最小版）」
2. 记录规则子图节点流、scan_once 闭环与去重
3. `graph_main` 仍标 M6；`analyze_relations` 仍标 M7

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | 三 DEV.md 与代码一致 |
| AC-02 | 规则语义、状态机、子图节点流与闭环已记录 |
| AC-03 | 更新 `task_m5/STATUS.md` 本行；若 M5-09 亦完成，备注「M5 里程碑可收口」 |
