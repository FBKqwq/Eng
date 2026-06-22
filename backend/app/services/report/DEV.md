# Report 持久化域 DEV 文档

## 1. 文档用途说明
维护 `app/services/report/` 分析报告写入与查询，目标索引 `analysis-results-*`。

## 2. 模块总览
| 文件 | 职责 | 状态 |
|---|---|---|
| `report_service.py` | `write_report` / `list_recent_reports` / `get_report` | 已实现 |

## 3. API 对接
- `GET /api/v1/reports/recent` → `list_recent_reports`（M4-05 已去占位，真实调 service）
- `GET /api/v1/reports/{id}` → `get_report`

## 4. 已实现功能清单
- **`write_report(report)`**：生成 `report_id`（uuid4）与 `created_at`（UTC ISO8601），合并写入 ES，返回 `{ ok, report_id }` 或 `{ ok: false, error }`。
- **`list_recent_reports(limit, report_type)`**：按 `created_at` 倒序分页列表，返回 `{ ok, items, total, limit }`。
- **`get_report(report_id)`**：按 `report_id` term 查询单份报告，返回 `{ ok, report_id, report }`（未找到时 `report: null`）。

### 4.1 `analysis-results-*` 索引约定（M4）

**索引模板**（M1 `index_service.create_analysis_indices` 已创建）：
- 模板名：`analysis-results`
- 匹配模式：`analysis-results-*`

**写入规则**（`write_report`）：
- 目标索引名：`analysis-results-{YYYY-MM-DD}`（由 `created_at` 日期部分解析，与模板 pattern 对齐）。
- 文档 `_id` = `report_id`。
- 写入字段：调用方传入的 `report` 字典 + 服务端追加的 `report_id`、`created_at`。
- 超时：`request_timeout=2s`，`max_retries=0`；失败返回结构化 `{ ok: false, error }`，不抛裸异常。

**查询规则**：
- 列表/单查均使用 `REPORT_INDEX_PATTERN = "analysis-results-*"` 跨日索引检索。
- `list_recent_reports`：`ignore_unavailable=True`、`allow_no_indices=True`；可选 `report_type` term 过滤；`limit` 钳制在 1~100。
- `get_report`：`term` 查询 `report_id` 字段；索引不存在时返回 `report: null`（`ok: true`）。

**列表项精简字段**（`_hit_to_report_item`）：`report_id`、`report_type`、`title`、`risk_level`、`summary`、`created_at`、`task_id`。

**调用方**：
- 定时闭环：`scheduler.run_once` 在子图成功后调用 `write_report`。
- HTTP：`api/v1/reports.py` 只调 service，不直连 ES。

## 5. 待开发功能清单
- P1：报告删除/归档（当前无删除接口）。
- P2：按 `task_id` / 时间范围复合查询。
- P3：写入前 schema 校验（与 `schemas/report.py` 对齐）。

## 6. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| `report_service` | 已实现 | 2026-06-22 | elk-backend-agent (M4-01) | 中 | 三函数真实 ES 读写；依赖索引模板已 init |
| Report 域整体 | 读写闭环可用 | 2026-06-22 | elk-backend-agent (M4-09) | 中 | API 已对接真实 service |

## 7. 禁止重复实现清单
| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| ES 客户端 | `elasticsearch/client.get_es_client` | 禁止在 API 层直连 ES |
| 索引模板创建 | `elasticsearch/index_service.create_analysis_indices` | 禁止在 report_service 内建模板 |
| 报告内容生成 | `langchain/report_chain` | 禁止在 report 域生成报告正文 |

## 8. 真实实现与设计愿景差异
| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 预警持久化 | `alerts-*` 索引读写 | M5 已实现（`alert_service` + `dedup`） | M6 主图收敛、预警 resolved 状态 API |
| 写入校验 | Pydantic 校验报告结构 | 直接合并 dict 写入 | 可选 P3 schema 校验 |
| 索引生命周期 | ILM 归档策略 | 仅按日分索引写入 | 运维层配置 |

## 9. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-06-16 | 建立 report_service 占位 + reports API | `report_service.py`、`api/v1/reports.py`、`schemas/report.py` | API 可访问，返回 placeholder | 待 M4 真实 ES 读写 |
| 2026-06-22 | M4-01：三函数真实 ES 读写 | `report_service.py` | `write_report` / `list_recent_reports` / `get_report` 无 placeholder | 需 `init_indices` 创建 analysis-results 模板 |
| 2026-06-22 | M4-05：reports API 去占位 | `api/v1/reports.py` | `/recent` 与 `/{id}` 真实调 service | — |
| 2026-06-22 | M4-09：DEV 文档收敛 | `report/DEV.md` | `analysis-results-*` 写入/查询约定已记录 | — |
| 2026-06-22 | 修正「预警持久化」差异表 | `report/DEV.md` | alerts-* 已由 M5 `alert/` 域实现 | 见 `alert/DEV.md` |
