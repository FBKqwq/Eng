"""
验证「模拟日志生成 -> Kafka -> Logstash -> Elasticsearch」全链路。

各环节说明（上一环节的产出被下一环节消费，并产生新产物）：
  1) 模拟生成：产出结构化 dict（含 log_id 等）。
  2) Kafka Producer：消费 dict，产出 topic 中的 JSON 消息。
  3) Kafka Consumer（本脚本内）：消费 topic 消息，产出与发送一致的 dict（证明 broker 侧可查）。
  4) Logstash（基础设施）：消费 Kafka 消息，产出写入 ES 的文档（含 @timestamp、tags 等）。
  5) Elasticsearch 查询（本脚本内）：消费 ES 已索引文档，产出检索命中结果（证明可查到 log_id）。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from kafka import KafkaConsumer

from app.core.config import settings
from app.services.elasticsearch.client import get_es_client
from app.services.kafka.producer import get_producer, send_log_message
from app.services.kafka.topic_setup import ensure_configured_topic
from app.services.simulation.log_generator import build_mock_log

from app.tasks.verify_log_kafka_pipeline import _poll_until, _wait_assignment


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="验证 日志生成 -> Kafka -> Logstash -> ES 全链路，各段可观测产物"
    )
    p.add_argument("--count", type=int, default=2, help="发送条数，默认 2")
    p.add_argument("--topic", type=str, default=None, help="Kafka topic，默认与配置一致")
    p.add_argument(
        "--kafka-wait",
        type=float,
        default=45.0,
        help="Kafka 脚本内消费阶段最长等待秒数",
    )
    p.add_argument(
        "--es-wait",
        type=float,
        default=120.0,
        help="等待 Logstash 写入 ES 后检索成功的最长秒数",
    )
    p.add_argument("--skip-ensure-topic", action="store_true", help="跳过 topic 预建")
    return p.parse_args()


def _reconfigure_stdio_utf8() -> None:
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass


def _elasticsearch_client() -> Elasticsearch:
    return get_es_client()


def _search_sources_by_log_ids(
    es: Elasticsearch,
    want_ids: set[str],
    *,
    index_pattern: str,
) -> dict[str, dict[str, Any]]:
    if not want_ids:
        return {}
    should = [{"match_phrase": {"log_id": lid}} for lid in want_ids]
    resp = es.search(
        index=index_pattern,
        size=min(100, len(want_ids) * 5),
        query={"bool": {"should": should, "minimum_should_match": 1}},
    )
    out: dict[str, dict[str, Any]] = {}
    for hit in resp.get("hits", {}).get("hits", []) or []:
        src = hit.get("_source") or {}
        lid = src.get("log_id")
        if isinstance(lid, str) and lid in want_ids:
            out[lid] = src
    return out


def _wait_es_for_log_ids(
    es: Elasticsearch,
    want_ids: set[str],
    *,
    index_pattern: str,
    deadline: float,
) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    while time.time() < deadline and want_ids != set(found.keys()):
        try:
            batch = _search_sources_by_log_ids(es, want_ids, index_pattern=index_pattern)
            found.update(batch)
        except Exception as exc:  # noqa: BLE001
            print(f"[ES] 检索暂不可达（将重试）: {exc}")
        if want_ids == set(found.keys()):
            break
        time.sleep(2.0)
    return found


def main() -> int:
    _reconfigure_stdio_utf8()
    # 与 Settings 一致：先合并 location/.env 再 backend/.env，便于读取 ELASTIC_PASSWORD
    _backend_root = Path(__file__).resolve().parents[2]
    _location_root = _backend_root.parent
    load_dotenv(_location_root / ".env")
    load_dotenv(_backend_root / ".env")

    args = _parse_args()
    if args.count <= 0:
        print("[错误] --count 必须大于 0", file=sys.stderr)
        return 1

    topic = args.topic or settings.kafka_topic
    bootstrap = settings.kafka_bootstrap_servers
    index_pattern = settings.elasticsearch_index_pattern

    print("========== 全链路验证 ==========")
    print(f"Kafka bootstrap: {bootstrap}  topic: {topic}")
    print(f"Elasticsearch: {settings.elasticsearch_hosts}  index: {index_pattern}")

    if not args.skip_ensure_topic:
        try:
            info = ensure_configured_topic()
            print(f"[0] topic 预检: {info}")
        except Exception as exc:  # noqa: BLE001
            print(f"[错误] topic 预建失败: {exc}", file=sys.stderr)
            return 2

    # ----- 环节 1：模拟生成 -----
    logs: list[dict[str, Any]] = []
    want_ids: set[str] = set()
    for i in range(args.count):
        log = build_mock_log()
        lid = log.get("log_id")
        if not isinstance(lid, str):
            print("[错误] build_mock_log 缺少字符串 log_id", file=sys.stderr)
            return 4
        want_ids.add(lid)
        logs.append(log)
        print(
            f"[1] 模拟生成 产出 dict[{i + 1}/{args.count}] "
            f"log_id={lid} log_type={log.get('log_type')}"
        )

    # 先起 Consumer（latest）并完成分区分配，再发送，避免漏读
    group_id = f"elk-full-pipeline-verify-{uuid.uuid4().hex}"
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap,
        group_id=group_id,
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=False,
    )
    assign_deadline = time.time() + min(20.0, args.kafka_wait)
    try:
        if not _wait_assignment(consumer, deadline=assign_deadline):
            print("[错误] Kafka 消费者未完成分区分配", file=sys.stderr)
            return 3

        # ----- 环节 2：写入 Kafka -----
        producer = get_producer()
        try:
            for log in logs:
                send_log_message(log, producer=producer, topic=topic)
                print(
                    f"[2] Kafka Producer 消费 dict -> 产出 topic 消息 "
                    f"log_id={log.get('log_id')}"
                )
        finally:
            producer.close()

        # ----- 环节 3：脚本内 Consumer 消费 Kafka -----
        kafka_deadline = time.time() + args.kafka_wait
        from_kafka = _poll_until(consumer, want_ids, deadline=kafka_deadline)
    finally:
        consumer.close()

    missing_k = want_ids - set(from_kafka.keys())
    if missing_k:
        print(f"[错误] Kafka 侧未收齐 log_id: {sorted(missing_k)}", file=sys.stderr)
        return 5

    for lid, body in from_kafka.items():
        print(
            f"[3] Kafka Consumer 消费 topic -> 产出 dict  log_id={lid} "
            f"log_type={body.get('log_type')} keys~={len(body)}"
        )

    # ----- 环节 4/5：Logstash 消费 Kafka 写 ES；脚本查询 ES -----
    try:
        es = _elasticsearch_client()
    except Exception as exc:  # noqa: BLE001
        print(f"[错误] 无法创建 Elasticsearch 客户端: {exc}", file=sys.stderr)
        return 6

    es_deadline = time.time() + args.es_wait
    in_es = _wait_es_for_log_ids(es, want_ids, index_pattern=index_pattern, deadline=es_deadline)
    missing_e = want_ids - set(in_es.keys())
    if missing_e:
        print(
            f"[错误] 超时内 ES 未检索到全部 log_id（请确认 Logstash 已启动且 pipeline 正常）: "
            f"{sorted(missing_e)}",
            file=sys.stderr,
        )
        return 7

    for lid, src in in_es.items():
        tags = src.get("tags")
        ts = src.get("@timestamp")
        has_ls_tag = isinstance(tags, list) and "pipeline_kafka_app_logs" in tags
        print(
            f"[4->5] ES 命中 log_id={lid} @timestamp={ts!r} "
            f"含 pipeline_kafka_app_logs 标签={has_ls_tag}"
        )

    print("----------")
    print(
        "[PASS] 全链路：生成 dict -> Kafka 消息 -> 脚本消费 Kafka 确认 "
        "-> Logstash 写入 -> ES 可检索（含 @timestamp / tags 等下游产物）。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
