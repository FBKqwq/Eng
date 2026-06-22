# M5-08：扫描任务入口 run_trigger_scanner

## Agent 角色

Task 层 Agent — 新建独立扫描入口，**仅调用** trigger_scanner。

## 唯一负责文件（新建）

```
app/tasks/run_trigger_scanner.py
```

## 禁止修改

- `trigger_scanner.py` 及任何其他文件

## 前置依赖

- M5-07 为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.analysis.trigger_scanner import start_trigger_scanner, scan_once; print('deps ok')"
```

## 开发要求

- 风格对齐 `tasks/run_scheduler.py` / `tasks/run_mcp_server.py`
- `python -m app.tasks.run_trigger_scanner` 常驻扫描；`--once` 执行一次 `scan_once` 并打印摘要后退出
- 成功 stdout 摘要；失败 `sys.exit(1)`

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `python -m app.tasks.run_trigger_scanner --once` 可执行 |
| AC-02 | 仅 import trigger_scanner，不重复业务逻辑 |
| AC-03 | 更新 `task_m5/STATUS.md` 本行 |
