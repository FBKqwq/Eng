# M7-09：M7 增强项单测 + 全量回归

## Agent 角色

测试 Agent — 新建 M7 单测覆盖三条主线，并完成 M1~M6 全量回归；ES/LLM/FastMCP 全 mock。

## 唯一负责文件

```
tests/test_m7_enhancements.py   # 新建
```

> 若 M7-04 改动 graph_scheduled 导致 M4/M6 既有 mock 失配，**仅可校正** `tests/test_m4_scheduled.py` / `tests/test_m6_main.py`（测试文件层），并在 STATUS 备注。

## 禁止修改

- 任何 `app/services/**`、`app/tasks/**`、`app/api/**` 生产逻辑（bug 记备注）

## 前置依赖

- M7-04、M7-07、M7-08 完成

## 详细任务内容（≥14 个 test 函数）

| 主线 | 覆盖点 |
| --- | --- |
| 关系发现 | `discover_relations`：LLM 可用（mock）返回结构化 relations；LLM 不可用降级空列表 + degraded；无 placeholder |
| schema | `RelationChainOutput` / `RelationItem`：默认构造、confidence 钳制 |
| 定时子图 | 子图含 `analyze_relations` 节点；relations 注入报告；关系发现降级时节点 skipped 且报告仍产出（与 M4 等价） |
| ES 工具 | 工具 11/12/13：mock ES 返回结构化结果；peak_bucket / 环比变化字段；超长窗口结构化错误 |
| 辅助工具 | 工具 14 离线生成 URL；15/16 mock ES 透传 service 结果 |
| 注册 | `list_registered_tool_names()` == 16；`get_langchain_tools()` 默认不含写类、含新读类工具 |
| MCP | `create_mcp_server()`：mock/monkeypatch fastmcp 缺失时结构化降级（不报 ImportError）；若可注入 fake FastMCP，断言仅读类工具被注册（不含 6、7） |
| 任务入口 | `run_mcp_server --list`（可用 subprocess 或直接调函数）打印读类工具名 |
| 回归 | 运行 M1~M6 全量；确认 119 passed 基线不退化（必要时校正 test_m4/test_m6） |

要求：`monkeypatch` mock ES/LLM/FastMCP，**不联网、不要求安装 fastmcp**。

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `pytest tests/test_m7_enhancements.py -v` 全绿 |
| AC-02 | M1~M6 全量回归通过（必要时已校正 test_m4/test_m6 并备注） |
| AC-03 | 覆盖关系发现降级、16 工具注册、MCP 读写分离与 fastmcp 缺失降级 |
| AC-04 | 更新 `task_m7/STATUS.md` 中 M7-09 行 |
