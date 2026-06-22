# M5-07：触发扫描器 trigger_scanner

## Agent 角色

扫描器 Agent — 周期扫描命中规则的日志，去重后触发规则子图并持久化报告与预警。

## 唯一负责文件

```
app/services/analysis/trigger_scanner.py
```

## 禁止修改

- `graph_rule.py`、`alert_service.py`、`dedup.py`、`report_service.py`、`rule_engine.py`（只 import）
- `core/config.py`（`trigger_scan_seconds` 已就绪，只读）

## 前置依赖

- M5-06、M5-01、M5-02 均为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.analysis.graph_rule import run_rule_subgraph; from app.services.alert.alert_service import write_alert; from app.services.alert.dedup import check_duplicate; from app.services.report.report_service import write_report; print('deps ok')"
```

## 开发要求

### 1. `scan_once() -> dict`（核心闭环）
- 查询 ES 最近窗口内可能命中规则的日志（ERROR/特定 error_code），用 `match_log` 复核 `trigger_subgraph=True`
- 对每条触发日志：
  1. `run_rule_subgraph(trigger_event)` → 取 report + alert_candidate
  2. `report_service.write_report(report)`
  3. `dedup.check_duplicate(alert_candidate)`：未重复 → `alert_service.write_alert`；重复 → 累加 evidence_count（或跳过写入）
- 去重避免同一触发反复产预警
- 返回 `{"ok": True, "triggered_count": n, "alert_ids": [...], "report_ids": [...]}`；异常结构化

### 2. `start_trigger_scanner() / stop_trigger_scanner()`
- 按 `settings.trigger_scan_seconds` 周期调用 `scan_once`（APScheduler 或 asyncio，复用 M4 模式）
- 防重叠运行

### 3. 约定
- 不抛裸异常；去除 placeholder；扫描异常不影响下一周期

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `scan_once` 闭环：触发→子图→写报告+去重写预警（mock 验证调用） |
| AC-02 | 重复触发不重复写预警 |
| AC-03 | start/stop 结构化返回，含防重叠 |
| AC-04 | 无 placeholder |
| AC-05 | 更新 `task_m5/STATUS.md` 本行 |
