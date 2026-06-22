"""独立运行规则触发扫描器。

用法：
  python -m app.tasks.run_trigger_scanner          # 常驻周期扫描
  python -m app.tasks.run_trigger_scanner --once   # 执行一次后退出
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Any

from app.services.analysis.trigger_scanner import (
    scan_once,
    start_trigger_scanner,
    stop_trigger_scanner,
)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="启动规则触发扫描或单次执行")
    p.add_argument(
        "--once",
        action="store_true",
        help="仅执行一次 scan_once 并打印摘要后退出",
    )
    return p.parse_args()


def _print_scan_once_summary(result: dict[str, Any]) -> None:
    print("[扫描] 单次执行摘要：")
    print(f"  ok={result.get('ok')}")
    print(f"  triggered_count={result.get('triggered_count', 0)}")
    report_ids = result.get("report_ids") or []
    print(f"  report_ids_count={len(report_ids)}")
    if report_ids:
        print(f"  report_ids={report_ids}")
    alert_ids = result.get("alert_ids") or []
    print(f"  alert_ids_count={len(alert_ids)}")
    if alert_ids:
        print(f"  alert_ids={alert_ids}")
    if not result.get("ok"):
        error = result.get("error")
        if error:
            print(f"  error={error}")
        errors = result.get("errors")
        if errors:
            print(f"  errors={errors}")
    if result.get("ok"):
        print("[完成] 单次扫描执行成功")
    else:
        print("[失败] 单次扫描执行失败", file=sys.stderr)


def _print_start_summary(result: dict[str, Any]) -> None:
    print("[扫描] 启动摘要：")
    print(f"  ok={result.get('ok')}")
    print(f"  running={result.get('running')}")
    interval = result.get("interval_seconds")
    if interval is not None:
        print(f"  interval_seconds={interval}")
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
        result = scan_once()
        _print_scan_once_summary(result)
        if not result.get("ok"):
            sys.exit(1)
        return

    result = start_trigger_scanner()
    _print_start_summary(result)
    if not result.get("ok"):
        sys.exit(1)

    print("[扫描] 常驻运行中，Ctrl+C 停止…")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_result = stop_trigger_scanner()
        print(f"[扫描] 已停止 running={stop_result.get('running')}")


if __name__ == "__main__":
    main()
