# M7-07：工具注册扩展 + MCP Server 实装

## Agent 角色

注册中心 Agent — 把工具表扩到 16 个，并基于 FastMCP 实装 `create_mcp_server()`。

## 唯一负责文件

```
app/services/tools/registry.py
requirements.txt
```

## 禁止修改

- elasticsearch_tools / kibana_tools / report_tools / alert_tools（只 import 工具函数与入参模型）
- 其他 tools / service 文件

## 前置依赖

- M7-05（工具 11/12/13）为 `已完成`/`已合并`
- M7-06（工具 14/15/16）为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.tools import elasticsearch_tools, report_tools, alert_tools, kibana_tools; print('deps ok')"
```

## 详细任务内容

### 1. 扩展工具表至 16 个
- `_TOOL_NAMES` 追加：`es_get_business_funnel`、`es_detect_traffic_peak`、`es_compare_time_windows`、`kibana_generate_link`、`report_list_recent`、`alert_list_active`（顺序 11~16）。
- `_all_tool_specs()` 追加 6 项规格（name/description/func/args_schema/model_bound），与现有 10 项同结构。
- 6 个新工具均为**读类**，不加入 `_WRITE_TOOL_NAMES`。
- `list_registered_tool_names()` 须返回 16 个名称（更新文档字符串「共 16 个」）。
- `get_langchain_tools(include_write_tools=...)` 行为不变：默认排除写类（6、7），新读类工具默认包含。

### 2. 实装 `create_mcp_server()`（§3.4）
- **懒加载 FastMCP**：函数内部 `try: from fastmcp import FastMCP` / `except ImportError: return {"ok": False, "error": "fastmcp 未安装"}`，**绝不在模块顶层 import fastmcp**（保证未安装时测试仍可导入 registry）。
- 创建 FastMCP server，把工具注册为 MCP 工具：**仅暴露读类工具**（即 `get_langchain_tools(include_write_tools=False)` 的全部，对应 1-5、8-10、11-16）；写类工具 6、7 **不注册**。
- 返回创建好的 server 实例（或在缺少 fastmcp 时返回结构化降级 dict）。
- 提供一个可被 task 层调用的形态（如返回 server 对象，由 `run_mcp_server` 决定 `server.run()`）。

### 3. requirements.txt
- 新增 `fastmcp`（不固定到不存在的版本；让包管理器解析最新）。
- 注释说明：MCP Server 形态为第二阶段能力，registry 懒加载，缺失不影响核心链路与测试。

### 约定
- 读写分离铁律：写类工具绝不进入 MCP server。
- 简体中文；不要 commit。

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `list_registered_tool_names()` 返回 16 个；`get_langchain_tools()` 含新读类工具、默认不含写类 |
| AC-02 | `create_mcp_server()` 在 fastmcp 已安装时返回 server，仅含读类工具（不含 analysis_write_report / alert_write_event） |
| AC-03 | fastmcp 未安装时 `import registry` 不报错，`create_mcp_server()` 结构化降级 |
| AC-04 | requirements.txt 增加 fastmcp；更新 `task_m7/STATUS.md` 中 M7-07 行 |
