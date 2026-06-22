# M7-06：第二阶段辅助工具（14/15/16）

## Agent 角色

辅助工具 Agent — 新增 Kibana 链接工具，并为 report/alert 增加只读列表工具。

## 唯一负责文件

```
app/services/tools/kibana_tools.py     # 新建（工具 14）
app/services/tools/report_tools.py     # 追加工具 15
app/services/tools/alert_tools.py      # 追加工具 16
```

## 禁止修改

- `report_service.py` / `alert_service.py`（只 import 复用）
- registry.py（注册由 M7-07 负责）
- elasticsearch_tools.py（M7-05 负责）

## 前置依赖

- M1 完成；report_service / alert_service 已实装（M4/M5）

## 前置依赖检查

```powershell
cd location\backend
python -c "from app.services.report.report_service import list_recent_reports; from app.services.alert.alert_service import list_active_alerts; print('deps ok')"
```

## 详细任务内容

### 工具 14：`kibana_generate_link`（新建 `kibana_tools.py`）
- 入参模型 `KibanaGenerateLinkInput`：`index_pattern`（如 `logs-*`）、`start_time`、`end_time`（必填）、可选 `query`（KQL/关键词）、可选 `log_type`。
- 纯字符串拼装 Kibana Discover URL（**不访问网络、不依赖 ES**），base URL 从 `settings`（若有 `kibana_base_url`）取，缺省用占位 base（如 `http://localhost:5601`）。
- 返回 `{"ok": True, "url": "..."}`；异常返回结构化错误。
- 用途：报告附跳转链接。

### 工具 15：`report_list_recent`（追加到 `report_tools.py`）
- 入参模型 `ReportListRecentInput`：`limit`（默认 20，`le=50`）、可选 `report_type`。
- 薄包装 `report_service.list_recent_reports(limit, report_type)`。
- 用途：外部 Agent / 前端读取历史报告。

### 工具 16：`alert_list_active`（追加到 `alert_tools.py`）
- 入参模型 `AlertListActiveInput`：`limit`（默认 50，`le=50`）。
- 薄包装 `alert_service.list_active_alerts(limit)`。
- 用途：外部 Agent / 前端读取活跃预警。

### 通用约束
1. 均为**读类**工具（MCP 可对外暴露）。
2. 返回条数受 `le=50` 限制；捕获异常返回 `{"ok": false, "error": ...}`，不抛裸异常。
3. 与既有 `report_tools` / `alert_tools` 中写类工具的风格保持一致（入参模型 + 薄适配）。

### 约定
- 简体中文；不要 commit。

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | 三工具函数与入参模型可独立调用返回结构化结果（kibana 工具离线可跑） |
| AC-02 | `report_list_recent` / `alert_list_active` 正确透传 service 结果（mock ES） |
| AC-03 | 异常返回 `{"ok": false, ...}`，不抛裸异常；不改 service 层 |
| AC-04 | 更新 `task_m7/STATUS.md` 中 M7-06 行 |
