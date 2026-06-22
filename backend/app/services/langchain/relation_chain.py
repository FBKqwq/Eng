"""隐藏关系发现 Chain。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.4 analyze_relations 节点
职责：证据包 → 隐藏关系推断；LLM 不可用时降级为空关系列表。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.services.langchain import llm_manager, prompts
from app.services.langchain.chain_schemas import RelationChainOutput

logger = logging.getLogger(__name__)


def discover_relations(evidence_package: dict[str, Any]) -> dict[str, Any]:
    """发现如「高峰后支付失败上升」类隐藏关系；LLM 不可用或解析失败时降级为空列表。"""
    package = _normalize_evidence_package(evidence_package)

    try:
        if llm_manager.is_llm_available():
            llm_result = _invoke_llm_relation(package)
            if llm_result.get("ok") and llm_result.get("data"):
                validated = RelationChainOutput.model_validate(llm_result["data"])
                return _build_response(validated, degraded=False)
            logger.info(
                "relation_chain LLM 路径未成功，降级为空关系列表 reason=%s",
                llm_result.get("error") or llm_result.get("reason"),
            )
    except Exception:
        logger.exception("relation_chain LLM 调用异常，降级为空关系列表")

    return _build_degraded_response()


def _normalize_evidence_package(raw: dict[str, Any]) -> dict[str, Any]:
    """兼容直接传入内层 evidence_package 或 build_evidence_package 完整返回值。"""
    if not raw:
        return {}
    if "summary" in raw:
        return raw
    inner = raw.get("evidence_package")
    if isinstance(inner, dict):
        return inner
    return raw


def _invoke_llm_relation(package: dict[str, Any]) -> dict[str, Any]:
    """通过 llm_manager 发起结构化关系发现调用。"""
    template = prompts.get_prompt("relation")
    if not template:
        return {"ok": False, "reason": "prompt_missing"}

    prompt = template.format(
        evidence_package=json.dumps(package, ensure_ascii=False, default=str)
    )
    return llm_manager.invoke_structured("relation", prompt, RelationChainOutput)


def _build_response(output: RelationChainOutput, *, degraded: bool) -> dict[str, Any]:
    """组装符合契约的返回 dict。"""
    return {
        "ok": True,
        "degraded": degraded,
        "relations": [item.model_dump(mode="json") for item in output.relations],
    }


def _build_degraded_response() -> dict[str, Any]:
    """降级路径：空关系列表，不阻断定时子图。"""
    return {
        "ok": True,
        "degraded": True,
        "relations": [],
    }
