"""独立运行定时分析调度器。

用法：
  python -m app.tasks.run_scheduler          # 常驻周期调度
  python -m app.tasks.run_scheduler --once   # 执行一次后退出
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Any

from app.services.analysis.scheduler import run_once, start_scheduler, stop_scheduler


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="启动定时分析调度或单次执行")
    p.add_argument(
        "--once",
        action="store_true",
        help="仅执行一次 run_once 并打印摘要后退出",
    )
    return p.parse_args()


def _print_run_once_summary(result: dict[str, Any]) -> None:
    print("[调度] 单次执行摘要：")
    print(f"  ok={result.get('ok')}")
    report_id = result.get("report_id")
    if report_id:
        print(f"  report_id={report_id}")
    node_trace = result.get("node_trace") or []
    print(f"  node_trace_count={len(node_trace)}")
    if not result.get("ok"):
        error = result.get("error")
        if error:
            print(f"  error={error}")
        errors = result.get("errors")
        if errors:
            print(f"  errors={errors}")
    if result.get("ok"):
        print("[完成] 单次调度执行成功")
    else:
        print("[失败] 单次调度执行失败", file=sys.stderr)


def _print_start_summary(result: dict[str, Any]) -> None:
    print("[调度] 启动摘要：")
    print(f"  ok={result.get('ok')}")
    print(f"  running={result.get('running')}")
    interval = result.get("interval_minutes")
    if interval is not None:
        print(f"  interval_minutes={interval}")
    message = result.get("message")
    if message:
        print(f"  message={message}")
    if not result.get("ok"):
        error = result.get("error")
        if error:
            print(f"  error={error}", file=sys.stderr)


def main() -> None:
    args = _parse_args()

    if args.once:
        result = run_once()
        _print_run_once_summary(result)
        if not result.get("ok"):
            sys.exit(1)
        return

    result = start_scheduler()
    _print_start_summary(result)
    if not result.get("ok"):
        sys.exit(1)

    print("[调度] 常驻运行中，Ctrl+C 停止…")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_result = stop_scheduler()
        print(f"[调度] 已停止 running={stop_result.get('running')}")


if __name__ == "__main__":
    main()
