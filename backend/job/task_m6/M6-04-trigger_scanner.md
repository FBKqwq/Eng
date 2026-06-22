# M6-04：扫描器收敛 trigger_scanner

## Agent 角色

扫描器收敛 Agent — 将 `scan_once` 的子图+持久化改为委托主图。

## 唯一负责文件

```
app/services/analysis/trigger_scanner.py
```

## 禁止修改

- `graph_main.py`、`graph_rule.py`、`alert_service.py`、`dedup.py`、`report_service.py`、`rule_engine.py`（只 import）
- `core/config.py`（只读）

## 前置依赖

- M6-02 为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.analysis.graph_main import run_main_graph; from app.services.diagnosis.rule_engine import match_log; print('deps ok')"
```

## 开发要求

### `scan_once() -> dict`
- 保留 ES 扫描 + `match_log` 复核 `trigger_subgraph=True` 的逻辑
- 对每条触发日志改为调用 `run_main_graph("rule", trigger_event=...)`
- **移除**对 `run_rule_subgraph` + `write_report` + `check_duplicate` + `write_alert` 的直接调用（已收口到主图）
- **保持对外返回契约稳定**：`{"ok": bool, "triggered_count": n, "alert_ids": [...], "report_ids": [...]}`
- 去重与预警决策由主图负责

### `start_trigger_scanner` / `stop_trigger_scanner`
- 保持周期与防重叠不变

### 约定
- 不抛裸异常；不要 commit；若契约变化，知会 M6-06 调整 test_m5

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `scan_once` 对触发日志委托 run_main_graph |
| AC-02 | 不再直接持久化/去重（收口主图） |
| AC-03 | 返回契约稳定（triggered_count/alert_ids/report_ids） |
| AC-04 | 更新 `task_m6/STATUS.md` 本行 |
