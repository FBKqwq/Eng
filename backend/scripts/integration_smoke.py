"""前后端全量联调冒烟脚本：验证前端 API wrapper 对应的后端端点。"""
from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

BASE = "http://localhost:8000/api/v1"
TIMEOUT = 30.0
ANALYSIS_TIMEOUT = 120.0

results: list[dict] = []


def record(name: str, ok: bool, detail: str = "", extra: dict | None = None) -> None:
    results.append({"name": name, "ok": ok, "detail": detail, **(extra or {})})
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}: {detail}")


def unwrap(resp: httpx.Response) -> tuple[bool, dict]:
    try:
        body = resp.json()
    except Exception:
        return False, {"raw": resp.text[:500]}
    if isinstance(body, dict) and "ok" in body:
        return bool(body.get("ok")), body
    return resp.is_success, body


def now_range(hours: int = 24) -> tuple[str, str]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    return start.isoformat().replace("+00:00", "Z"), end.isoformat().replace("+00:00", "Z")


def test_health(client: httpx.Client) -> None:
    r = client.get(f"{BASE}/health")
    ok, body = unwrap(r)
    data = body.get("data", {}) if ok else {}
    record("GET /health", ok and data.get("status") == "ok", f"status={data.get('status')}")


def test_system_status(client: httpx.Client) -> None:
    r = client.get(f"{BASE}/system/status", timeout=TIMEOUT)
    ok, body = unwrap(r)
    data = body.get("data", {}) if ok else {}
    kafka_ok = data.get("kafka", {}).get("available")
    es_ok = data.get("elasticsearch", {}).get("available")
    record(
        "GET /system/status",
        ok and kafka_ok and es_ok,
        f"kafka={kafka_ok}, es={es_ok}, docs={data.get('elasticsearch', {}).get('docs_count')}",
    )


def test_log_fields(client: httpx.Client) -> None:
    r = client.get(f"{BASE}/logs/fields")
    ok, body = unwrap(r)
    types = body.get("data", {}).get("registered_log_types", []) if ok else []
    record("GET /logs/fields", ok and len(types) > 0, f"types={len(types)}")

    r2 = client.get(f"{BASE}/logs/fields", params={"log_type": "application"})
    ok2, body2 = unwrap(r2)
    catalog = body2.get("data", {}).get("catalog", {}) if ok2 else {}
    filters = catalog.get("filter_fields", [])
    record("GET /logs/fields?log_type=application", ok2 and len(filters) > 0, f"filter_fields={len(filters)}")


def test_log_search(client: httpx.Client) -> None:
    start, end = now_range(72)
    payload = {
        "start_time": start,
        "end_time": end,
        "page": 1,
        "page_size": 10,
        "log_types": ["application"],
    }
    r = client.post(f"{BASE}/logs/search", json=payload, timeout=TIMEOUT)
    ok, body = unwrap(r)
    data = body.get("data", {}) if ok else {}
    total = data.get("total", 0)
    items = data.get("items", [])
    record("POST /logs/search", ok, f"total={total}, items={len(items)}")


def test_log_aggregate(client: httpx.Client) -> None:
    start, end = now_range(24)
    payload = {
        "start_time": start,
        "end_time": end,
        "template": "traffic",
        "interval": "1h",
    }
    r = client.post(f"{BASE}/logs/aggregate", json=payload, timeout=TIMEOUT)
    ok, body = unwrap(r)
    data = body.get("data", {}) if ok else {}
    buckets = data.get("buckets", [])
    total = (data.get("extra") or {}).get("total_count")
    record(
        "POST /logs/aggregate (template=traffic)",
        ok,
        f"buckets={len(buckets)}, total={total}, took_ms={data.get('took_ms')}",
    )

    start2, end2 = now_range(23)
    payload2 = {
        "start_time": start2,
        "end_time": end2,
        "template": "errors",
        "top_n": 10,
    }
    r2 = client.post(f"{BASE}/logs/aggregate", json=payload2, timeout=TIMEOUT)
    ok2, body2 = unwrap(r2)
    data2 = body2.get("data", {}) if ok2 else {}
    by_service = (data2.get("extra") or {}).get("by_service", [])
    record(
        "POST /logs/aggregate (template=errors)",
        ok2,
        f"error_buckets={len(data2.get('buckets', []))}, by_service={len(by_service)}",
    )


def test_alerts(client: httpx.Client) -> None:
    r = client.get(f"{BASE}/alerts/active", params={"limit": 10})
    ok, body = unwrap(r)
    data = body.get("data", {}) if ok else {}
    record("GET /alerts/active", ok, f"total={data.get('total', 0)}")


def test_reports(client: httpx.Client) -> None:
    r = client.get(f"{BASE}/reports/recent", params={"limit": 5})
    ok, body = unwrap(r)
    data = body.get("data", {}) if ok else {}
    items = data.get("items", [])
    record("GET /reports/recent", ok, f"total={data.get('total', 0)}, items={len(items)}")
    if items:
        rid = items[0]["report_id"]
        r2 = client.get(f"{BASE}/reports/{rid}")
        ok2, body2 = unwrap(r2)
        report = body2.get("data", {}).get("report") if ok2 else None
        record("GET /reports/{id}", ok2, f"report_id={rid}, has_report={report is not None}")


def test_analysis_runs(client: httpx.Client) -> None:
    r = client.get(f"{BASE}/analysis/runs/recent", params={"limit": 5})
    ok, body = unwrap(r)
    data = body.get("data", {}) if ok else {}
    record("GET /analysis/runs/recent", ok, f"items={len(data.get('items', []))}")


def test_diagnosis(client: httpx.Client) -> None:
    start, end = now_range(24)
    payload = {
        "request_id": str(uuid.uuid4()),
        "keyword": "timeout",
        "service_name": "order-service",
        "time_range_start": start,
        "time_range_end": end,
    }
    r = client.post(f"{BASE}/diagnosis", json=payload, timeout=60.0)
    ok, body = unwrap(r)
    diag = body.get("data", {}).get("diagnosis", {}) if ok else {}
    route = diag.get("route", "?")
    record("POST /diagnosis", ok, f"route={route}, severity={diag.get('severity')}")


def test_analysis_run(client: httpx.Client) -> None:
    start, end = now_range(6)
    payload = {
        "trigger_type": "scheduled",
        "time_window": {"start": start, "end": end},
    }
    try:
        r = client.post(f"{BASE}/analysis/run", json=payload, timeout=ANALYSIS_TIMEOUT)
        ok, body = unwrap(r)
        data = body.get("data", {}) if ok else body.get("data") or {}
        trace = data.get("node_trace", [])
        record(
            "POST /analysis/run",
            ok,
            f"report_id={data.get('report_id')}, nodes={len(trace)}, errors={data.get('errors', [])}",
        )
    except httpx.ReadTimeout:
        record("POST /analysis/run", False, "timeout > 120s")


def main() -> int:
    print("=== ELK 前后端全量联调冒烟 ===\n")
    with httpx.Client() as client:
        test_health(client)
        test_system_status(client)
        test_log_fields(client)
        test_log_search(client)
        test_log_aggregate(client)
        test_alerts(client)
        test_reports(client)
        test_analysis_runs(client)
        test_diagnosis(client)
        test_analysis_run(client)

    passed = sum(1 for r in results if r["ok"])
    failed = [r for r in results if not r["ok"]]
    print(f"\n=== 汇总: {passed}/{len(results)} 通过 ===")
    if failed:
        print("失败项:")
        for f in failed:
            print(f"  - {f['name']}: {f['detail']}")
    out = Path(__file__).resolve().parent / "integration_smoke_result.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n结果已写入 {out}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
