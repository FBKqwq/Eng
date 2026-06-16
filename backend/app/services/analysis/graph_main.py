"""LangGraph 主图（占位）。

职责：路由调度、结果收敛、预警决策、持久化；不做具体分析。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.3
状态：占位 — 待 M5/M6 接入 LangGraph。

节点流：normalize_trigger -> build_state -> route -> merge_result -> alert_decision -> persist_result -> END
"""

from __future__ import annotations

from typing import Any

from app.services.analysis.state import create_initial_state


def build_main_graph() -> Any:
    """构建并编译主图（占位，返回 None）。"""
    return None


def run_main_graph(trigger_type: str, **kwargs: Any) -> dict[str, Any]:
    """手动触发主图执行（占位）。"""
    state = create_initial_state(trigger_type, **kwargs)
    return {
        "ok": False,
        "placeholder": True,
        "message": "graph_main 尚未实现，待 M5/M6 接入 LangGraph",
        "trigger_type": trigger_type,
        "state_keys": list(state.keys()),
    }
