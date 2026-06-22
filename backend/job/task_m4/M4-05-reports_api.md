# M4-05：报告 API reports_api

## Agent 角色

API 层 Agent — 将 `reports.py` 从占位响应改为真实调用 `report_service`。

## 唯一负责文件

```
app/api/v1/reports.py
```

## 禁止修改

- `report_service.py`（只 import）
- `schemas/report.py`、`router.py`

## 前置依赖

- M4-01 为 `已完成`/`已合并`

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.report.report_service import list_recent_reports, get_report; r=list_recent_reports(limit=1); assert 'placeholder' not in r"
```

## 开发要求

### `GET /recent`
- 调 `list_recent_reports(limit=...)`，按 `ReportListResponse` 返回真实 items/total
- 去除强制 `placeholder=True`

### `GET /{report_id}`
- 调 `get_report(report_id)`，按 `ReportDetailResponse` 返回真实 report
- 未命中返回 ok=True + report=None（或合理 404 语义，二选一并注释）

### 约定
- 薄路由：不写 ES DSL、不定义新 schema
- 保持响应模型契约

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `/recent` 返回 service 真实结果（TestClient 验证） |
| AC-02 | `/{id}` 命中/未命中均结构化返回 |
| AC-03 | 无强制 placeholder 响应 |
| AC-04 | 更新 `task_m4/STATUS.md` 本行 |
