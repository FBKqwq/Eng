"""LLM 模型管理。

职责：多模型、API Key、参数、重试统一管理；按任务类型选择模型。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.6 / §2.7
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from app.core.config import settings
from app.services.langchain.output_parsers import parse_with_retry

logger = logging.getLogger(__name__)

TaskKind = Literal["report", "diagnosis", "relation", "alert", "json_repair"]

_ANALYSIS_TASKS: frozenset[TaskKind] = frozenset({"diagnosis", "relation"})


def is_llm_available() -> bool:
    """检测 LLM 是否可用；无 API Key 时返回 False，链层据此走降级路径。"""
    return bool(settings.llm_api_key and settings.llm_api_key.strip())


def _resolve_model(task: TaskKind) -> str:
    """按任务类型选择模型名。"""
    if task in _ANALYSIS_TASKS:
        return settings.llm_analysis_model
    return settings.llm_default_model


def get_llm(task: TaskKind = "report") -> Any:
    """按任务类型返回 LangChain ChatModel 实例；不可用时返回 None。"""
    if not is_llm_available():
        return None

    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        logger.warning("langchain-openai 未安装，无法创建 LLM 实例")
        return None

    model_name = _resolve_model(task)
    kwargs: dict[str, Any] = {
        "model": model_name,
        "api_key": settings.llm_api_key,
        "timeout": settings.llm_timeout_seconds,
        "temperature": settings.llm_temperature,
    }
    base_url = settings.llm_base_url.strip() if settings.llm_base_url else ""
    if base_url:
        kwargs["base_url"] = base_url

    return ChatOpenAI(**kwargs)


def invoke_structured(
    task: TaskKind,
    prompt: str,
    output_schema: type,
) -> dict[str, Any]:
    """结构化 LLM 调用入口；不可用时返回降级 dict，异常不向外抛出。"""
    if not is_llm_available():
        return {"ok": False, "available": False, "reason": "llm_unavailable"}

    llm = get_llm(task)
    if llm is None:
        return {"ok": False, "available": False, "reason": "llm_unavailable"}

    try:
        response = llm.invoke(prompt)
        raw_text = response.content if hasattr(response, "content") else str(response)
        if not isinstance(raw_text, str):
            raw_text = str(raw_text)
        return parse_with_retry(raw_text, output_schema)
    except Exception as exc:
        logger.exception("invoke_structured 调用失败 task=%s", task)
        return {"ok": False, "error": str(exc)}
