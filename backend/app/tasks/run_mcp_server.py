"""独立运行 MCP Server。

用法：
  python -m app.tasks.run_mcp_server          # 常驻启动 MCP Server（stdio）
  python -m app.tasks.run_mcp_server --list   # 列出读类工具名后退出
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any

from app.services.tools.registry import create_mcp_server

_FASTMCP_MISSING_MSG = "fastmcp 未安装，无法启动 MCP Server，请先 pip install fastmcp"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="启动 ELK 日志分析 MCP Server 或列出读类工具")
    p.add_argument(
        "--list",
        action="store_true",
        help="仅打印将要暴露的读类工具名后退出（不启动服务）",
    )
    return p.parse_args()


def _is_degraded(result: Any) -> bool:
    return isinstance(result, dict) and result.get("ok") is False


def _degraded_message(result: dict[str, Any]) -> str:
    error = result.get("error")
    if error == "fastmcp 未安装":
        return _FASTMCP_MISSING_MSG
    return str(error or "创建 MCP Server 失败")


async def _fetch_tool_names_from_server(server: Any) -> list[str]:
    tools = await server.list_tools()
    return [tool.name for tool in tools]


def _list_read_tool_names(result: Any) -> list[str]:
    if _is_degraded(result):
        from app.services.tools.registry import get_langchain_tools

        return [tool.name for tool in get_langchain_tools(include_write_tools=False)]
    return asyncio.run(_fetch_tool_names_from_server(result))


def _print_tool_list(names: list[str]) -> None:
    print(f"[MCP] 读类工具列表（共 {len(names)} 个）：")
    for name in names:
        print(f"  - {name}")


def _print_start_summary(server: Any, tool_count: int) -> None:
    print("[MCP] 启动摘要：")
    print(f"  name={getattr(server, 'name', 'elk-log-analysis')}")
    print("  transport=stdio")
    print(f"  tool_count={tool_count}")
    print("[MCP] 常驻运行中，Ctrl+C 停止…")


def main() -> None:
    args = _parse_args()

    try:
        result = create_mcp_server()
    except Exception as exc:
        print(f"[失败] 创建 MCP Server 时出错：{exc}", file=sys.stderr)
        sys.exit(1)

    if args.list:
        _print_tool_list(_list_read_tool_names(result))
        return

    if _is_degraded(result):
        print(_degraded_message(result), file=sys.stderr)
        sys.exit(1)

    try:
        tool_count = len(_list_read_tool_names(result))
        _print_start_summary(result, tool_count)
        result.run()
    except KeyboardInterrupt:
        print("\n[MCP] 已停止")
    except Exception as exc:
        print(f"[失败] MCP Server 运行异常：{exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
