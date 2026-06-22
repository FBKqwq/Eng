# M7-10：M7 文档收口（DEV.md）

## Agent 角色

文档 Agent — 更新 langchain、analysis、tools 模块 DEV 文档，并标注全规划收口（不碰业务代码）。

## 唯一负责文件

```
app/services/langchain/DEV.md
app/services/analysis/DEV.md
app/services/tools/DEV.md
```

## 禁止修改

- 任何 `.py` 文件

## 前置依赖

- M7-04、M7-07、M7-08 完成（可与 M7-09 并行）

## 详细任务内容

### langchain/DEV.md
1. `relation_chain` 由「占位」→「已实现」：记录 `discover_relations` 输入/输出契约与降级策略。
2. `RELATION_PROMPT` / `RelationChainOutput` 已落地，补充字段说明。
3. 移除「relation 待 M7」类遗留措辞。

### analysis/DEV.md
1. 定时子图节点流更新为七节点：`build_evidence → analyze_relations → generate_report`。
2. 记录 relations 注入报告与降级（skipped）行为。
3. `analyze_relations` 不再标 M7 待实现。

### tools/DEV.md
1. 工具表更新为 16 个（列出 11~16 及其包装的 service 函数与读/写属性）。
2. 记录 `create_mcp_server()` 形态、读写分离（写类 6/7 不对外）、fastmcp 懒加载与降级。
3. 记录 `run_mcp_server` 任务入口用途。

### 收口标注
- 在合适位置注明：**M7 完成即总体规划（M1~M7）全部收口**。

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | 三 DEV.md 与 M7 代码一致，无「待 M7」遗留措辞 |
| AC-02 | 七节点子图、16 工具、MCP Server 形态均已记录 |
| AC-03 | 更新 `task_m7/STATUS.md` 中 M7-10 行；若 M7-01~10 均完成，更新 STATUS 第 5 节为「无可派发任务，M1~M7 全规划收口」 |
