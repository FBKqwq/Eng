# M6-03：调度器收敛 scheduler

## Agent 角色

调度器收敛 Agent — 将 `run_once` 改为委托主图，持久化交由主图 persist_result。

## 唯一负责文件

```
app/services/analysis/scheduler.py
```

## 禁止修改

- `graph_main.py`、`graph_scheduled.py`、`report_service.py`（只 import）
- `core/config.py`（只读）

## 前置依赖

- M6-02 为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.analysis.graph_main import run_main_graph; print('deps ok')"
```

## 开发要求

### `run_once(time_window=None) -> dict`
- 改为调用 `run_main_graph("scheduled", time_window=time_window)`
- **移除**对 `run_scheduled_subgraph` + `write_report` 的直接调用（持久化已收口到主图）
- **保持对外返回契约稳定**：`{"ok": bool, "report_id": ..., "node_trace": [...]}`（可附加 `alert_id`）
- 异常结构化返回，不抛裸异常

### `start_scheduler` / `stop_scheduler`
- 保持 APScheduler 周期与防重叠（max_instances=1）不变；回调内调用新 `run_once`

### 约定
- 不要 commit；若契约变化，知会 M6-06 调整 test_m4

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `run_once` 委托 run_main_graph，不再直接 write_report |
| AC-02 | 返回契约稳定（ok/report_id/node_trace） |
| AC-03 | start/stop 行为不变 |
| AC-04 | 更新 `task_m6/STATUS.md` 本行 |
