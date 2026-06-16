"""LLM 模型管理（占位）。

职责：多模型、API Key、参数、重试统一管理；按任务类型选择模型。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.6 / §2.7
状态：占位 — 待 M3 接入真实 LLM 供应商。
"""

from __future__ import annotations

from typing import Any, Literal

TaskKind = Literal["report", "diagnosis", "relation", "alert", "json_repair"]

_PLACEHOLDER = {
    "ok": False,
    "placeholder": True,
    "message": "llm_manager 尚未实现，待 M3 配置 LLM_API_KEY 后接入",
}


def get_llm(task: TaskKind = "report") -> Any:
    """按任务类型返回 LangChain ChatModel 实例（占位）。"""
    return None


def is_llm_available() -> bool:
    """检测 LLM 是否可用；不可用时图节点走降级路径。"""
    return False


def invoke_structured(task: TaskKind, prompt: str, output_schema: type) -> dict[str, Any]:
    """结构化 LLM 调用入口（占位）。"""
    return {**_PLACEHOLDER, "task": task, "output_schema": output_schema.__name__}
