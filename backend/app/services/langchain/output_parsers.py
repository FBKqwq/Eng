"""Pydantic 结构化输出解析（占位）。

职责：LLM 输出解析、格式错误自动重试（轻量模型修 JSON）。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.6
状态：占位 — 待 M3 实现。
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def parse_with_retry(raw_text: str, schema: type[T], *, max_retries: int = 2) -> dict[str, Any]:
    """解析 LLM 输出为 Pydantic 模型，失败时尝试 JSON 修复（占位）。"""
    return {
        "ok": False,
        "placeholder": True,
        "message": "output_parsers 尚未实现",
        "schema": schema.__name__,
        "raw_preview": raw_text[:200] if raw_text else "",
        "max_retries": max_retries,
    }
