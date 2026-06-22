# M7-08：MCP Server 独立任务入口

## Agent 角色

任务入口 Agent — 新建独立 CLI，启动 MCP Server。

## 唯一负责文件

```
app/tasks/run_mcp_server.py   # 新建
```

## 禁止修改

- registry.py（只 import `create_mcp_server`）
- 其他任何文件

## 前置依赖

- M7-07（create_mcp_server）为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.tools.registry import create_mcp_server; print('deps ok')"
```

## 详细任务内容

参照既有 `app/tasks/run_scheduler.py` / `run_trigger_scanner.py` 的 CLI 风格，新建 MCP Server 启动入口：

1. `main()`：调用 `create_mcp_server()`。
   - 若返回结构化降级（fastmcp 未安装 / 出错）：打印清晰中文提示「fastmcp 未安装，无法启动 MCP Server，请先 pip install fastmcp」，`sys.exit(1)`。
   - 若返回 server 实例：打印启动摘要（监听信息/已暴露工具数），调用其运行方法（如 `server.run()`）常驻。
2. 支持 `--help`；可选 `--list` 仅打印将要暴露的读类工具名后退出（便于答辩演示，不实际起服务）。
3. `if __name__ == "__main__": main()`。
4. **仅 import registry**，不引入业务逻辑；异常打印后 `exit(1)`。

### 约定
- 简体中文输出；不要 commit。

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `python -m app.tasks.run_mcp_server --list` 打印读类工具名（不含写类）并退出 0 |
| AC-02 | fastmcp 未安装时启动给出清晰提示并 `exit(1)`，不抛裸异常栈 |
| AC-03 | 仅 import registry，无多余依赖 |
| AC-04 | 更新 `task_m7/STATUS.md` 中 M7-08 行 |
