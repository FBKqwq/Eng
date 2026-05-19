from __future__ import annotations

import argparse
import sys
import threading
import time
from dataclasses import dataclass
from typing import Optional

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
        "--workers",
        type=int,
        default=1,
        help="并发生产线程数，默认 1；所有线程统一写入同一 Kafka topic",
    )
    p.add_argument(
        "--skip-ensure-topic",
        action="store_true",
        help="跳过启动时的 topic 预建（依赖 broker 自动建 topic）",
    )
    return p.parse_args()


@dataclass
class ProducerState:
    sent: int = 0
    error: Optional[BaseException] = None


def _should_send_more(args: argparse.Namespace, state: ProducerState, lock: threading.Lock) -> Optional[int]:
    with lock:
        if state.error is not None:
            return None
        if args.count is not None and state.sent >= args.count:
            return None
        state.sent += 1
        return state.sent


def _producer_worker(
    *,
    worker_id: int,
    args: argparse.Namespace,
    interval: float,
    state: ProducerState,
    lock: threading.Lock,
    stop_event: threading.Event,
) -> None:
    try:
        producer = get_producer()
    except Exception as exc:  # noqa: BLE001
        with lock:
            state.error = exc
        stop_event.set()
        return

    try:
        while not stop_event.is_set():
            seq = _should_send_more(args, state, lock)
            if seq is None:
                break

            log = build_mock_log()
            try:
                send_log_message(log, producer=producer, topic=args.topic)
                print(
                    f"worker[{worker_id}] sent[{seq}]: "
                    f"log_id={log.get('log_id')} log_type={log.get('log_type')}"
                )
            except RuntimeError as exc:
                with lock:
                    state.error = exc
                stop_event.set()
                break

            if args.count is None or state.sent < args.count:
                time.sleep(interval)
    finally:
        producer.close()


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
    if args.workers <= 0:
        print("[错误] --workers 必须大于 0", file=sys.stderr)
        sys.exit(1)

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

    state = ProducerState()
    lock = threading.Lock()
    stop_event = threading.Event()
    workers: list[threading.Thread] = []

    try:
        for i in range(args.workers):
            worker = threading.Thread(
                target=_producer_worker,
                kwargs={
                    "worker_id": i + 1,
                    "args": args,
                    "interval": interval,
                    "state": state,
                    "lock": lock,
                    "stop_event": stop_event,
                },
                daemon=True,
            )
            worker.start()
            workers.append(worker)

        for worker in workers:
            worker.join()
    except KeyboardInterrupt:
        stop_event.set()
        print("producer stopped")

    if state.error is not None:
        print(
            f"[错误] Kafka 多线程生产失败: {state.error}\n"
            f"  bootstrap={settings.kafka_bootstrap_servers!r}, topic={(args.topic or settings.kafka_topic)!r}",
            file=sys.stderr,
        )
        sys.exit(4)

    print(f"[完成] workers={args.workers} total_sent={state.sent} topic={args.topic or settings.kafka_topic}")


if __name__ == "__main__":
    main()
