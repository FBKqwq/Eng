# M4-09：M4 文档收敛 dev_docs

## Agent 角色

文档 Agent — 更新 analysis 与 report 模块 DEV 文档（不碰业务代码）。

## 唯一负责文件

```
app/services/analysis/DEV.md
app/services/report/DEV.md
```

## 禁止修改

- 任何 `.py` 文件

## 前置依赖

- M4-04、M4-06 完成（可与 M4-07、M4-08 并行）

## 开发要求

### analysis/DEV.md
1. 状态表：`schemas`/`state`/`graph_scheduled`/`scheduler` 由「占位」→「已实现（M4 最小版）」
2. 记录定时子图节点流与降级策略
3. `graph_rule`/`trigger_scanner`/`graph_main` 仍标 M5/M6；`analyze_relations` 标 M7
4. 开发日志追加 M4 条目

### report/DEV.md
1. `report_service` 三函数由「占位」→「已实现」
2. 记录 `analysis-results-*` 写入与查询约定
3. 开发日志追加 M4 条目

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | 两 DEV.md 与代码一致 |
| AC-02 | 子图节点流、降级策略、持久化约定已记录 |
| AC-03 | 更新 `task_m4/STATUS.md` 本行；若 M4-08 亦完成，备注「M4 里程碑可收口」 |
