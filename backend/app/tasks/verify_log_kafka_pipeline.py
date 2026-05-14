"""
验证「模拟日志生成 -> Kafka topic」链路：先启动消费者（latest + 已分配分区），
再经与线上一致的 producer 发送，最后在超时内消费并校验 log_id 一一对应。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from typing import Any

from kafka import KafkaConsumer

from app.core.config import settings
from app.services.kafka.producer import get_producer, send_log_message
from app.services.kafka.topic_setup import ensure_configured_topic
from app.services.simulation.log_generator import build_mock_log


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="验证日志生成经 producer 写入 Kafka 后可被消费者读取")
    p.add_argument("--count", type=int, default=3, help="发送并期望回收的日志条数，默认 3")
    p.add_argument("--topic", type=str, default=None, help="覆盖默认 Kafka topic")
    p.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="消费阶段最长等待秒数，默认 30",
    )
    p.add_argument(
        "--skip-ensure-topic",
        action="store_true",
        help="跳过启动时的 topic 预建",
    )
    return p.parse_args()


def _wait_assignment(consumer: KafkaConsumer, *, deadline: float) -> bool:
    consumer.poll(timeout_ms=200)
    while time.time() < deadline:
        if consumer.assignment():
            return True
        consumer.poll(timeout_ms=500)
    return bool(consumer.assignment())


def _poll_until(
    consumer: KafkaConsumer,
    want_ids: set[str],
    *,
    deadline: float,
) -> dict[str, dict[str, Any]]:
    got: dict[str, dict[str, Any]] = {}
    while time.time() < deadline and want_ids != set(got.keys()):
        polled = consumer.poll(timeout_ms=1000)
        for _tp, records in polled.items():
            for rec in records:
                val = rec.value
                if not isinstance(val, dict):
                    continue
                lid = val.get("log_id")
                if isinstance(lid, str) and lid in want_ids and lid not in got:
                    got[lid] = val
    return got


def main() -> int:
    args = _parse_args()
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass
    if args.count <= 0:
        print("[错误] --count 必须大于 0", file=sys.stderr)
        return 1

    topic = args.topic or settings.kafka_topic
    bootstrap = settings.kafka_bootstrap_servers

    if not args.skip_ensure_topic:
        try:
            info = ensure_configured_topic()
            print(f"[topic] {info}")
        except Exception as exc:  # noqa: BLE001
            print(f"[错误] topic 预建失败: {exc}", file=sys.stderr)
            return 2

    group_id = f"elk-pipeline-verify-{uuid.uuid4().hex}"
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap,
        group_id=group_id,
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=False,
    )

    assign_deadline = time.time() + min(15.0, args.timeout)
    try:
        if not _wait_assignment(consumer, deadline=assign_deadline):
            print("[错误] 消费者在超时内未完成分区分配", file=sys.stderr)
            return 3

        logs: list[dict[str, Any]] = []
        want_ids: set[str] = set()
        for _ in range(args.count):
            log = build_mock_log()
            lid = log.get("log_id")
            if not isinstance(lid, str):
                print("[错误] build_mock_log 缺少字符串 log_id", file=sys.stderr)
                return 4
            want_ids.add(lid)
            logs.append(log)

        producer = get_producer()
        try:
            for log in logs:
                send_log_message(log, producer=producer, topic=topic)
                print(f"[send] log_id={log.get('log_id')} log_type={log.get('log_type')}")
        finally:
            producer.close()

        consume_deadline = time.time() + args.timeout
        received = _poll_until(consumer, want_ids, deadline=consume_deadline)
    finally:
        consumer.close()

    missing = want_ids - set(received.keys())
    extra_ok = len(received) == len(want_ids)

    print("---------- 验证结果 ----------")
    print(f"topic: {topic}")
    print(f"bootstrap: {bootstrap}")
    print(f"期望 log_id 数: {len(want_ids)}")
    print(f"实际匹配数: {len(received)}")
    if missing:
        print(f"未消费到的 log_id: {sorted(missing)}")
    for lid, body in received.items():
        lt = body.get("log_type")
        print(f"[recv] log_id={lid} log_type={lt}")

    if not missing and extra_ok:
        print("[PASS] producer 发送的日志均被同一链路中的消费者成功读取，链路正常。")
        return 0

    print("[FAIL] 未在超时内完整消费到与发送一一对应的日志。", file=sys.stderr)
    return 5


if __name__ == "__main__":
    raise SystemExit(main())
