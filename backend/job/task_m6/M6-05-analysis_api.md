# M6-05：分析轨迹 API analysis_api

## Agent 角色

API 层 Agent — 新建分析轨迹 API 并注册路由，向前端暴露图执行轨迹与手动触发。

## 唯一负责文件

```
app/api/v1/analysis.py     # 新建
app/api/router.py          # 注册 analysis 路由（仅本任务编辑）
```

## 禁止修改

- `graph_main.py`、`report_service.py`（只 import）
- 其他 api/v1/*.py、schemas

## 前置依赖

- M6-02 为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.analysis.graph_main import run_main_graph; from app.services.report.report_service import list_recent_reports; print('deps ok')"
```

## 开发要求

### 1. `GET /api/v1/analysis/runs/recent`
- 调 `report_service.list_recent_reports`，提取每份报告的 `node_trace` 摘要（节点名/状态/耗时）返回
- 用于前端展示「图执行了哪些节点、各节点耗时与产出」

### 2. `POST /api/v1/analysis/run`
- body：`trigger_type`（scheduled|rule）+ 可选 `trigger_event` / `time_window`
- 调 `run_main_graph(...)`，返回 `node_trace` + report_id/alert_id（用于演示手动触发）
- 入参校验，非法 trigger_type 返回 4xx 或结构化 ok=False

### 3. 注册路由
- 在 `router.py` 新增 `analysis_router`，`prefix="/v1/analysis"`，`tags=["analysis"]`

### 约定
- 薄路由：不写 ES DSL；可定义本文件内轻量响应模型或返回 dict
- 不要 commit

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `/runs/recent` 返回近期 node_trace 轨迹（TestClient 验证） |
| AC-02 | `/run` 手动触发返回 node_trace + ids |
| AC-03 | router 正确注册 analysis 路由 |
| AC-04 | 更新 `task_m6/STATUS.md` 本行 |
