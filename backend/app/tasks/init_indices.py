"""Elasticsearch 索引模板初始化 CLI。

调用 index_service.init_all_indices / verify_templates，供部署或本地联调使用。
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from app.services.elasticsearch.index_service import init_all_indices, verify_templates


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="初始化或校验 Elasticsearch 索引模板")
    p.add_argument(
        "--verify-only",
        action="store_true",
        help="仅调用 verify_templates() 校验模板是否存在，不创建",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="额外在 stdout 输出完整 JSON 结果",
    )
    return p.parse_args()


def _configure_stdio_encoding() -> None:
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass


def _format_step_line(step: dict[str, Any]) -> str:
    action = step.get("action", "unknown")
    if step.get("ok"):
        count = step.get("count")
        if count is not None:
            return f"  [ok] {action}：{count} 个模板"
        return f"  [ok] {action}"
    return f"  [失败] {action}：{step.get('error', '未知错误')}"


def _print_init_summary(result: dict[str, Any]) -> None:
    print("[索引初始化] 执行摘要：")
    for step in result.get("steps", []):
        print(_format_step_line(step))
    if result.get("ok"):
        print("[完成] 全部步骤成功")
        return
    print(
        f"[失败] {result.get('error', '索引模板初始化失败')}",
        file=sys.stderr,
    )


def _print_verify_summary(result: dict[str, Any]) -> None:
    print("[模板校验] 执行摘要：")
    if result.get("ok"):
        print("  [ok] 全部关键模板已存在")
        return
    missing = result.get("missing") or []
    if missing:
        print(f"  [失败] 缺失 {len(missing)} 个模板：", file=sys.stderr)
        for name in missing:
            print(f"    - {name}", file=sys.stderr)
    if result.get("error"):
        print(f"  [错误] {result['error']}", file=sys.stderr)


def main() -> None:
    _configure_stdio_encoding()
    args = _parse_args()

    try:
        if args.verify_only:
            result = verify_templates()
            _print_verify_summary(result)
        else:
            result = init_all_indices()
            _print_init_summary(result)
    except Exception as exc:  # noqa: BLE001 — 任务入口需打印可读诊断
        print(f"[错误] 索引任务执行异常：{exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
