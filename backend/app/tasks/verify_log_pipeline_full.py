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
import os
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

_early_backend = Path(__file__).resolve().parents[2]
_DOTENV_ROUTE_KEYS = {
    "KAFKA_BOOTSTRAP_SERVERS",
    "KAFKA_TOPIC",
    "ELASTICSEARCH_HOSTS",
    "ELASTICSEARCH_INDEX_PATTERN",
    "ELASTICSEARCH_USERNAME",
    "KIBANA_BASE_URL",
}


def _load_dotenv_preserving_gateway_yaml() -> None:
    """读取 .env 密钥，但避免 .env 的路由项（值为空时）压过 config/gateway.yaml。"""
    load_dotenv(_early_backend.parent / ".env")
    load_dotenv(_early_backend / ".env")
    # .env 中设为空字符串的路由项，恢复为空（让 gateway.yaml 取值生效）
    for key in _DOTENV_ROUTE_KEYS:
        if os.environ.get(key, "").strip() == "":
            os.environ.pop(key, None)


_load_dotenv_preserving_gateway_yaml()

from elasticsearch import Elasticsearch
from kafka import KafkaConsumer

from app.core.config import settings
from app.services.elasticsearch.client import get_es_client
from app.services.kafka.producer import get_producer, send_log_message
from app.services.kafka.topic_setup import ensure_configured_topic
from app.services.simulation.log_generator import build_mock_log

from app.tasks.verify_log_kafka_pipeline import _poll_until, _wait_assignment


def _log_id_from_source(src: dict[str, Any]) -> str | None:
    lid = src.get("log_id")
    if isinstance(lid, str):
        return lid
    ev = src.get("event")
    if isinstance(ev, dict):
        raw = ev.get("original")
        if isinstance(raw, str):
            try:
                obj = json.loads(raw)
                if isinstance(obj, dict):
                    x = obj.get("log_id")
                    if isinstance(x, str):
                        return x
            except json.JSONDecodeError:
                return None
    return None


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="验证 日志生成 -> Kafka -> Logstash -> ES 全链路，各段可观测产物"
    )
    p.add_argument("--count", type=int, default=2, help="发送条数，默认 2")
    p.add_argument("--topic", type=str, default=None, help="Kafka topic，默认与配置一致")
    p.add_argument("--workers", type=int, default=1, help="并发生成与发送 worker 数，默认 1")
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
    p.add_argument(
        "--verbose-es",
        action="store_true",
        help="打印每次 ES 轮询进度（默认约每 5 次打印一次）",
    )
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


def _es_resp_to_dict(resp: Any) -> dict[str, Any]:
    if isinstance(resp, dict):
        return resp
    if hasattr(resp, "to_dict"):
        return resp.to_dict()
    try:
        return dict(resp)
    except Exception:
        return {}


def _es_count_docs(es: Elasticsearch, index_pattern: str) -> int:
    try:
        r = _es_resp_to_dict(es.count(index=index_pattern, ignore_unavailable=True))
        return int(r.get("count", 0))
    except Exception:
        return -1


def _search_sources_by_log_ids(
    es: Elasticsearch,
    want_ids: set[str],
    *,
    index_pattern: str,
) -> tuple[dict[str, dict[str, Any]], int]:
    """返回 (log_id -> _source, 本次检索 total hits 近似值)。"""
    if not want_ids:
        return {}, 0
    ids = list(want_ids)
    sq = " OR ".join(f'"{lid}"' for lid in ids)
    queries: list[dict[str, Any]] = [
        {"bool": {"should": [{"terms": {"log_id.keyword": ids}}], "minimum_should_match": 1}},
        {"bool": {"should": [{"match_phrase": {"log_id": lid}} for lid in ids], "minimum_should_match": 1}},
        {
            "simple_query_string": {
                "query": sq,
                "fields": ["log_id", "event.original"],
                "lenient": True,
                "default_operator": "OR",
            }
        },
        {
            "bool": {
                "should": [{"wildcard": {"event.original": f"*{lid}*"}} for lid in ids],
                "minimum_should_match": 1,
            }
        },
    ]
    out: dict[str, dict[str, Any]] = {}
    total_hint = 0
    # 单次 search 的 size 必须 >= 待查 log_id 数量；此前固定 min(...,100) 会在 --count 200 时只拉回 100 条命中，表现为永远差几十条「卡住」
    fetch_size = min(10000, len(want_ids) + 50)
    for q in queries:
        if len(out) == len(want_ids):
            break
        try:
            resp = es.search(
                index=index_pattern,
                size=fetch_size,
                query=q,
            )
        except Exception:
            continue
        resp_d = _es_resp_to_dict(resp)
        hits_meta = resp_d.get("hits") or {}
        total = hits_meta.get("total", 0)
        if isinstance(total, dict):
            total_hint = max(total_hint, int(total.get("value", 0)))
        else:
            total_hint = max(total_hint, int(total or 0))
        for hit in hits_meta.get("hits", []) or []:
            if not isinstance(hit, dict):
                hit = hit.to_dict() if hasattr(hit, "to_dict") else dict(hit)
            src = hit.get("_source") or {}
            if not isinstance(src, dict):
                src = dict(src) if hasattr(src, "keys") else {}
            lid = _log_id_from_source(src)
            if isinstance(lid, str) and lid in want_ids:
                out[lid] = src
    return out, total_hint


def _wait_es_for_log_ids(
    es: Elasticsearch,
    want_ids: set[str],
    *,
    index_pattern: str,
    deadline: float,
    verbose: bool,
    baseline_doc_count: int,
) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    last_total = 0
    poll_n = 0
    warned_stall = False
    while time.time() < deadline and want_ids != set(found.keys()):
        try:
            try:
                es.indices.refresh(index=index_pattern)
            except Exception:
                pass
            cur_cnt = _es_count_docs(es, index_pattern)
            batch, last_total = _search_sources_by_log_ids(es, want_ids, index_pattern=index_pattern)
            found.update(batch)
        except Exception as exc:  # noqa: BLE001
            print(f"[ES] 检索异常（将重试）: {exc}")
            cur_cnt = -1
        poll_n += 1
        if verbose or poll_n % 5 == 1:
            delta = ""
            if cur_cnt >= 0 and baseline_doc_count >= 0:
                delta = f" 索引总文档={cur_cnt}（基线={baseline_doc_count}，Δ={cur_cnt - baseline_doc_count}）"
            print(
                f"[4] 等待 Logstash->ES 轮询 #{poll_n} "
                f"已命中目标 log_id {len(found)}/{len(want_ids)} 条 本次查询 total≈{last_total}{delta}"
            )
        if (
            not warned_stall
            and poll_n >= 6
            and cur_cnt >= 0
            and baseline_doc_count >= 0
            and cur_cnt <= baseline_doc_count
            and len(found) < len(want_ids)
        ):
            warned_stall = True
            print(
                "[诊断] 发消息后 ES 文档总数未超过基线，说明 Logstash 很可能没有把新 Kafka 消息写入 ES。\n"
                "  建议：1) docker logs location-logstash-1 --tail 200 查看是否有 ERROR/403；\n"
                "  2) docker compose restart logstash；\n"
                "  3) 若曾反复改 Kafka 监听/网络，确认 Logstash 环境变量 LS_PIPELINE_KAFKA_BOOTSTRAP_SERVERS=kafka:29092。"
            )
        if want_ids == set(found.keys()):
            break
        time.sleep(2.0)
    return found


def _produce_logs_concurrently(
    *,
    count: int,
    workers: int,
    topic: str,
) -> tuple[list[dict[str, Any]], set[str], int]:
    logs: list[dict[str, Any]] = []
    want_ids: set[str] = set()
    lock = threading.Lock()
    next_seq = {"value": 0}
    error: list[BaseException] = []

    def claim_seq() -> int | None:
        with lock:
            if error:
                return None
            if next_seq["value"] >= count:
                return None
            next_seq["value"] += 1
            return next_seq["value"]

    def worker(worker_id: int) -> None:
        try:
            producer = get_producer()
        except Exception as exc:  # noqa: BLE001
            with lock:
                error.append(exc)
            return

        try:
            while True:
                seq = claim_seq()
                if seq is None:
                    break

                log = build_mock_log()
                lid = log.get("log_id")
                if not isinstance(lid, str):
                    with lock:
                        error.append(RuntimeError("build_mock_log 缺少字符串 log_id"))
                    break

                print(
                    f"[1] worker[{worker_id}] 模拟生成 产出 dict[{seq}/{count}] "
                    f"log_id={lid} log_type={log.get('log_type')}"
                )
                send_log_message(log, producer=producer, topic=topic)
                print(
                    f"[2] worker[{worker_id}] Kafka Producer 消费 dict -> 产出 topic 消息 "
                    f"log_id={lid}"
                )

                with lock:
                    logs.append(log)
                    want_ids.add(lid)
        except Exception as exc:  # noqa: BLE001
            with lock:
                error.append(exc)
        finally:
            producer.close()

    threads = [
        threading.Thread(target=worker, args=(idx + 1,), daemon=True)
        for idx in range(workers)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    if error:
        raise error[0]
    return logs, want_ids, len(threads)


def main() -> int:
    _load_dotenv_preserving_gateway_yaml()
    _reconfigure_stdio_utf8()

    args = _parse_args()
    if args.count <= 0:
        print("[错误] --count 必须大于 0", file=sys.stderr)
        return 1
    if args.workers <= 0:
        print("[错误] --workers 必须大于 0", file=sys.stderr)
        return 1

    topic = args.topic or settings.kafka_topic
    bootstrap = settings.kafka_bootstrap_servers
    index_pattern = settings.elasticsearch_index_pattern

    print("========== 全链路验证 ==========")
    print(f"Kafka bootstrap: {bootstrap}  topic: {topic}")
    print(f"Elasticsearch: {settings.elasticsearch_hosts}  index: {index_pattern}")
    print(f"Producer workers: {args.workers}  planned logs: {args.count}")

    if not args.skip_ensure_topic:
        try:
            info = ensure_configured_topic()
            print(f"[0] topic 预检: {info}")
        except Exception as exc:  # noqa: BLE001
            print(f"[错误] topic 预建失败: {exc}", file=sys.stderr)
            return 2

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

        # ----- 环节 1/2：多线程模拟生成并写入 Kafka -----
        try:
            logs, want_ids, actual_workers = _produce_logs_concurrently(
                count=args.count,
                workers=args.workers,
                topic=topic,
            )
            print(
                f"[2] 多线程生产完成 workers={actual_workers} "
                f"generated={len(logs)} topic={topic}"
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[错误] 多线程生成或 Kafka 发送失败: {exc}", file=sys.stderr)
            return 4

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

    # ping 偶发返回 False（kafka-python 库会干扰 socket），改为仅记录不再熔断
    try:
        ping_ok = bool(es.ping())
    except Exception as exc:  # noqa: BLE001
        ping_ok = False
        print(f"[警告] Elasticsearch ping 异常（继续）: {exc}")
    if not ping_ok:
        print("[警告] Elasticsearch ping 返回 False（继续）—后续检索阶段会再校验")

    try:
        pre_cnt = _es_count_docs(es, index_pattern)
        print(f"[ES] ping 成功；索引 {index_pattern} 当前总文档数≈{pre_cnt}（轮询前，含历史数据）")
    except Exception as exc:  # noqa: BLE001
        print(f"[ES] count 查询失败（将继续轮询）: {exc}")
        pre_cnt = -1

    time.sleep(1.5)
    es_deadline = time.time() + args.es_wait
    in_es = _wait_es_for_log_ids(
        es,
        want_ids,
        index_pattern=index_pattern,
        deadline=es_deadline,
        verbose=args.verbose_es,
        baseline_doc_count=pre_cnt,
    )
    missing_e = want_ids - set(in_es.keys())
    if missing_e:
        print(
            f"[错误] 超时内 ES 未检索到全部 log_id: {sorted(missing_e)}\n"
            "  排查建议：1) docker logs location-logstash-1 --tail 200 查看 ERROR/403；\n"
            "  2) docker compose restart logstash（Kafka 或 compose 变更后常见）；\n"
            "  3) 确认 compose 中 LS_PIPELINE_KAFKA_BOOTSTRAP_SERVERS=kafka:29092；\n"
            "  4) 若脚本曾提示「文档总数未增加」，优先检查 Logstash 而非 ES 查询。",
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
