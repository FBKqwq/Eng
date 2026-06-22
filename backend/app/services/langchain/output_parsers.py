"""Pydantic 结构化输出解析。

职责：LLM 输出解析、格式错误自动重试（轻量模型修 JSON）。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.6
"""

from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

_CODE_BLOCK_RE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL | re.IGNORECASE)
_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")


def _extract_json(text: str) -> str | None:
    """从文本中提取 JSON 字符串，容忍代码块包裹与前后多余文本。"""
    if not text or not text.strip():
        return None

    stripped = text.strip()

    block_match = _CODE_BLOCK_RE.search(stripped)
    if block_match:
        candidate = block_match.group(1).strip()
        if candidate:
            return candidate

    if stripped.startswith("{") or stripped.startswith("["):
        balanced = _extract_balanced_json(stripped, 0)
        if balanced:
            return balanced

    for opener in ("{", "["):
        idx = stripped.find(opener)
        if idx != -1:
            balanced = _extract_balanced_json(stripped, idx)
            if balanced:
                return balanced

    return None


def _extract_balanced_json(text: str, start: int) -> str | None:
    """从 start 位置起提取首个平衡的 JSON 对象或数组。"""
    if start >= len(text):
        return None

    open_char = text[start]
    close_char = "}" if open_char == "{" else "]"
    depth = 0
    in_string = False
    escaped = False

    for i in range(start, len(text)):
        ch = text[i]
        if escaped:
            escaped = False
            continue
        if ch == "\\" and in_string:
            escaped = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    return None


def _sanitize_json_text(text: str) -> str:
    """纯代码清洗：去尾逗号、统一空白。"""
    cleaned = text.strip()
    cleaned = _TRAILING_COMMA_RE.sub(r"\1", cleaned)
    return cleaned


def _try_validate(json_text: str, schema: type[T]) -> tuple[dict[str, Any] | None, str | None]:
    """尝试 JSON 解析与 schema 校验，成功返回 model_dump，失败返回错误信息。"""
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        return None, f"JSON 解析失败: {exc.msg}"

    try:
        model = schema.model_validate(payload)
    except ValidationError as exc:
        return None, f"Schema 校验失败: {exc.error_count()} 个字段错误"

    return model.model_dump(), None


def _try_llm_repair(raw_text: str, schema: type[T]) -> str | None:
    """可选 LLM 修复路径；LLM 不可用时返回 None，不抛异常。"""
    from app.services.langchain import llm_manager

    llm = llm_manager.get_llm("json_repair")
    if llm is None:
        return None

    prompt = (
        "将以下文本修复为合法 JSON，仅输出 JSON，不要解释。\n"
        f"目标结构类型: {schema.__name__}\n\n"
        f"{raw_text}"
    )
    try:
        response = llm.invoke(prompt)
        content = getattr(response, "content", None)
        if content is None:
            content = str(response)
        repaired = _extract_json(str(content)) or str(content).strip()
        return repaired or None
    except Exception:
        return None


def parse_with_retry(raw_text: str, schema: type[T], *, max_retries: int = 2) -> dict[str, Any]:
    """解析 LLM 输出为 Pydantic 模型，失败时尝试代码清洗与可选 LLM 修复。"""
    preview = raw_text[:200] if raw_text else ""

    if not raw_text or not raw_text.strip():
        return {"ok": False, "error": "输入为空", "raw_preview": preview}

    last_error = "无法从文本中提取 JSON"
    working_text = raw_text

    for attempt in range(max_retries + 1):
        candidates: list[str] = []
        extracted = _extract_json(working_text)
        if extracted:
            candidates.append(extracted)
        sanitized_source = _sanitize_json_text(extracted or working_text.strip())
        if sanitized_source not in candidates:
            candidates.append(sanitized_source)

        for candidate in candidates:
            data, err = _try_validate(candidate, schema)
            if data is not None:
                return {"ok": True, "data": data}
            if err:
                last_error = err

        if attempt >= max_retries:
            break

        repaired = _try_llm_repair(working_text, schema)
        if repaired:
            working_text = repaired
            continue

        next_text = _sanitize_json_text(working_text)
        if next_text == working_text.strip():
            break
        working_text = next_text

    return {"ok": False, "error": last_error, "raw_preview": preview}
