# M7-05：第二阶段 ES 增强工具（11/12/13）

## Agent 角色

ES 工具 Agent — 在 elasticsearch_tools 中新增 3 个增强工具，薄包装 aggregation_service。

## 唯一负责文件

```
app/services/tools/elasticsearch_tools.py
```

## 禁止修改

- `aggregation_service.py`（只 import 复用，不重写聚合逻辑）
- registry.py（注册由 M7-07 负责）
- 其他 tools 文件

## 前置依赖

- M1 完成（aggregation_service 六模板已可用）

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.elasticsearch.aggregation_service import aggregate_behavior_funnel, aggregate_traffic; print('deps ok')"
```

## 详细任务内容

新增 3 个工具函数 + 各自 Pydantic 入参模型（与现有 `EsSearchLogsInput` / `EsAggregateMetricsInput` 风格一致，复用 `schemas/log.py` 枚举）。所有工具**薄适配**：参数校验 → 调 aggregation_service → 结果裁剪；捕获异常返回 `{"ok": false, "error": ...}`。

### 工具 11：`es_get_business_funnel`
- 入参模型 `EsGetBusinessFunnelInput`：`start_time`、`end_time`（必填）、可选 `log_types`、`top_n`（默认 10，`le=50`）。
- 包装 `aggregation_service.aggregate_behavior_funnel(...)`。
- 用途：行为漏斗洞察（各环节转化/流失）。

### 工具 12：`es_detect_traffic_peak`
- 入参模型 `EsDetectTrafficPeakInput`：`start_time`、`end_time`（必填）、可选 `interval`、`group_by`。
- 包装 `aggregation_service.aggregate_traffic(...)`，在返回结果上**附加峰值识别**：从时间桶中找出最高流量桶（peak_bucket：时间点 + 计数）。
- 用途：请求高峰定位。

### 工具 13：`es_compare_time_windows`
- 入参模型 `EsCompareTimeWindowsInput`：当前窗口 `current_start`/`current_end` + 对比窗口 `baseline_start`/`baseline_end`（均必填）、`template`（默认 `traffic`，限六模板枚举）。
- 内部对两窗口各调一次对应聚合模板，计算环比变化（总量差值/百分比）。
- 用途：环比变化分析。

### 通用约束（§3.3）
1. 时间窗强制必填，最大跨度受限（默认 ≤24h，超限返回结构化错误）。
2. 返回桶/条数硬上限（≤50）。
3. 仅返回裁剪后的结构化结果，绝不抛裸异常。

### 约定
- 简体中文；不要 commit。

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | 三工具函数与入参模型可独立调用（mock ES）返回结构化结果 |
| AC-02 | `es_detect_traffic_peak` 返回含 peak_bucket；`es_compare_time_windows` 返回含环比变化 |
| AC-03 | 超长时间窗/异常返回 `{"ok": false, ...}`，不抛裸异常 |
| AC-04 | 不改 aggregation_service；更新 `task_m7/STATUS.md` 中 M7-05 行 |
