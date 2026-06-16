# M2-04：报告写入工具 report_tools

## Agent 角色

报告写工具 Agent — **仅实现工具 6** `analysis_write_report`（第一阶段）。

## 唯一负责文件

```
app/services/tools/report_tools.py
```

## 禁止修改

- `report/report_service.py`（M4 实装）
- `alert_tools.py`

## 前置依赖

- M1 完成

## 开发要求

### 1. `analysis_write_report`

- 保留 `WriteReportInput`（`report: dict`）
- 调用 `report_service.write_report`
- 写类工具：docstring 标明「仅 persist 节点 / include_write_tools=True 时暴露」

### 2. `report_list_recent`

- **保持占位或返回 `ok: false` + 说明「第二阶段 M7」**，勿在本任务实装（属工具 15）

### 3. 去除工具 6 的 `placeholder: true`

## 验收标准

| # | 标准 |
| --- | --- |
| AC-01 | `analysis_write_report` 无 `placeholder` |
| AC-02 | 调用 `write_report` 并返回结构化结果 |
| AC-03 | 更新 STATUS 本行 |
