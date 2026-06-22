# M4-07：调度任务入口 run_scheduler

## Agent 角色

Task 层 Agent — 新建独立调度入口，**仅调用** scheduler。

## 唯一负责文件（新建）

```
app/tasks/run_scheduler.py
```

## 禁止修改

- `scheduler.py` 及任何其他文件

## 前置依赖

- M4-06 为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.analysis.scheduler import start_scheduler, run_once; print('deps ok')"
```

## 开发要求

- 风格对齐 `tasks/run_mcp_server.py` / `tasks/run_log_producer.py`
- `python -m app.tasks.run_scheduler` 启动常驻调度
- 建议支持 `--once`：仅执行一次 `run_once` 并打印报告摘要后退出（便于验收）
- 成功 stdout 摘要；失败 `sys.exit(1)`

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `python -m app.tasks.run_scheduler --once` 可执行（mock/真实 ES 下） |
| AC-02 | 仅 import scheduler，不重复业务逻辑 |
| AC-03 | 更新 `task_m4/STATUS.md` 本行 |
