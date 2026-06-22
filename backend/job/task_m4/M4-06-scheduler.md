# M4-06：定时调度器 scheduler

## Agent 角色

调度器 Agent — 周期触发定时子图并将报告持久化，形成闭环。

## 唯一负责文件

```
app/services/analysis/scheduler.py
```

## 可附加修改

```
requirements.txt   # 追加 apscheduler（或采用 asyncio task 方案，无新依赖则不改）
```

## 禁止修改

- `graph_scheduled.py`、`report_service.py`（只 import）
- `core/config.py`（`analysis_schedule_minutes` 已就绪，只读）

## 前置依赖

- M4-01、M4-04 均为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.analysis.graph_scheduled import run_scheduled_subgraph; from app.services.report.report_service import write_report; print('deps ok')"
```

## 开发要求

### 1. `run_once() -> dict`（核心闭环单元）
- 调 `run_scheduled_subgraph()` → 取 `report`
- 调 `report_service.write_report(report)` 持久化
- 返回 `{"ok": True, "report_id": ..., "node_trace": [...]}`；异常结构化返回

### 2. `start_scheduler() / stop_scheduler()`
- 基于 APScheduler（或 asyncio）按 `settings.analysis_schedule_minutes` 周期调用 `run_once`
- 防重叠运行（max_instances=1 / 互斥标志）
- 返回启动/停止状态结构

### 3. 约定
- 不抛裸异常；去除 placeholder
- 调度异常不影响下一周期

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `run_once` 跑通子图→持久化（mock 验证 write_report 被调用） |
| AC-02 | start/stop 返回结构化状态，无 placeholder |
| AC-03 | 防重叠机制存在 |
| AC-04 | 若新增 apscheduler 已写入 requirements |
| AC-05 | 更新 `task_m4/STATUS.md` 本行 |
