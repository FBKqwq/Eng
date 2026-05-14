from __future__ import annotations

import argparse
import sys
import time

from app.core.config import settings
from app.services.kafka.producer import get_producer, send_log_message
from app.services.kafka.topic_setup import ensure_configured_topic
from app.services.simulation.log_generator import build_mock_log


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="持续生成模拟电商日志并写入 Kafka")
    p.add_argument(
        "--interval",
        type=float,
        default=None,
        help="发送间隔秒数，默认使用配置 log_producer_interval_seconds",
    )
    p.add_argument(
        "--count",
        type=int,
        default=None,
        help="发送条数上限，默认无限循环",
    )
    p.add_argument(
        "--topic",
        type=str,
        default=None,
        help="覆盖默认 Kafka topic（仍建议与 Logstash 消费配置一致）",
    )
    p.add_argument(
        "--skip-ensure-topic",
        action="store_true",
        help="跳过启动时的 topic 预建（依赖 broker 自动建 topic）",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    interval = (
        float(settings.log_producer_interval_seconds)
        if args.interval is None
        else args.interval
    )
    if interval <= 0:
        print("[错误] --interval 必须大于 0", file=sys.stderr)
        sys.exit(1)
    if args.count is not None and args.count <= 0:
        print("[提示] --count<=0 不发送任何消息，直接退出")
        return
    topic_override = args.topic

    if not args.skip_ensure_topic:
        try:
            info = ensure_configured_topic()
            print(f"[topic] {info}")
        except Exception as exc:  # noqa: BLE001 — 任务入口需打印可读诊断
            print(
                f"[错误] 无法确认或创建 Kafka topic: {exc}\n"
                f"  请检查 KAFKA_BOOTSTRAP_SERVERS={settings.kafka_bootstrap_servers!r} 与 broker 是否可达。\n"
                "  若需跳过预建，可加参数 --skip-ensure-topic。",
                file=sys.stderr,
            )
            sys.exit(2)

    try:
        producer = get_producer()
    except Exception as exc:  # noqa: BLE001
        print(
            f"[错误] 无法连接 Kafka Producer: {exc}\n"
            f"  bootstrap={settings.kafka_bootstrap_servers!r}",
            file=sys.stderr,
        )
        sys.exit(3)

    sent = 0
    try:
        while True:
            log = build_mock_log()
            try:
                send_log_message(log, producer=producer, topic=topic_override)
                sent += 1
                print(f"sent[{sent}]: log_id={log.get('log_id')} log_type={log.get('log_type')}")
            except RuntimeError as exc:
                print(f"[错误] {exc}", file=sys.stderr)
                sys.exit(4)
            if args.count is not None and sent >= args.count:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        print("producer stopped")
    finally:
        producer.close()


if __name__ == "__main__":
    main()
