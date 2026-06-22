# M4-01：报告持久化 report_service

## Agent 角色

报告持久化 Agent — 实现 `analysis-results-*` 索引的写入与查询。

## 唯一负责文件

```
app/services/report/report_service.py
```

## 禁止修改

- `index_service.py`（`analysis-results-*` 模板已就绪，只 import `get_es_client`）
- `tools/report_tools.py`（M2 已薄包装，不改）
- 其他文件

## 前置依赖

- M1 完成（`create_analysis_indices` 已建模板）
- 必读：`elasticsearch/client.py` 的 `get_es_client`、`schemas/report.py`、`index_service._analysis_results_properties`（只读参考字段）

## 开发要求

### 1. `write_report(report: dict) -> dict`
- 生成 `report_id`（如 uuid4）、`created_at`
- 写入索引 `analysis-results-<日期>` 或 `analysis-results-write`（与模板 pattern 对齐）
- 返回 `{"ok": True, "report_id": ...}`；ES 异常 → `{"ok": False, "error": ...}`，**无 placeholder**

### 2. `list_recent_reports(limit=20, report_type=None) -> dict`
- 按 `created_at` 倒序查询，可按 `report_type` 过滤
- 返回 `{"ok": True, "items": [...], "total": n, "limit": limit}`

### 3. `get_report(report_id) -> dict`
- 按 `report_id` 查询单份；未命中 `{"ok": True, "report": None}`；异常结构化错误

### 4. 约定
- ES 错误风格沿用 `log_query_service`
- 不抛裸异常；去除所有 placeholder

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | 三函数无 placeholder 键 |
| AC-02 | `write_report` 返回 report_id；mock ES 验证 index 调用 |
| AC-03 | `list_recent_reports` 结构含 items/total |
| AC-04 | ES 异常路径返回 ok=False 不抛异常 |
| AC-05 | 更新 `task_m4/STATUS.md` 本行 |
