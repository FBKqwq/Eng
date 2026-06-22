# Alert 持久化域 DEV 文档

## 1. 文档用途说明
维护 `app/services/alert/` 预警写入、查询与去重，目标索引 `alerts-*`。

## 2. 模块总览
| 文件 | 职责 | 状态 |
|---|---|---|
| `alert_service.py` | `write_alert` / `list_active_alerts` / `acknowledge_alert` | 已实现（M5） |
| `dedup.py` | `build_idempotency_key` / `check_duplicate` | 已实现（M5） |

## 3. API 对接
- `GET /api/v1/alerts/active` → `list_active_alerts`（M5-05 已去占位，真实调用 service）
- `POST /api/v1/alerts/{id}/ack` → `acknowledge_alert`

## 4. 已实现功能清单

### 4.1 alert_service 三函数

| 函数 | 职责 | 返回要点 |
|---|---|---|
| `write_alert(alert)` | 写入 `alerts-{YYYY-MM-DD}` 索引；支持 `existing_alert_id` 累加 `evidence_count` | `{ ok, alert_id }` 或 `{ ok: False, error }` |
| `list_active_alerts(limit)` | 查询 `status=active`，按 `updated_at` 倒序 | `{ ok, items, total, limit }` |
| `acknowledge_alert(alert_id, operator?)` | `active` → `acknowledged` 状态流转 | `{ ok, alert_id, status }` |

- 复用 `get_es_client()`；请求超时 2s；`ignore_unavailable=True` 容忍索引未建。
- 新预警文档字段：`alert_id`、`alert_type`、`severity`、`status`、`title`、`affected_service`、`evidence_count`、`created_at`、`updated_at`、`payload`。
- `write_alert` 传入 `existing_alert_id` 时走 `_increment_evidence`，将已有预警 `evidence_count + 1` 并更新 `updated_at`（供去重命中后复用）。

### 4.2 dedup 去重

| 函数 | 职责 |
|---|---|
| `build_idempotency_key(alert_candidate, bucket_minutes=10)` | 构建幂等键字符串 |
| `check_duplicate(alert_candidate, bucket_minutes=10)` | ES 查重，返回是否重复及 `existing_alert_id` |

**幂等键约定**：`{alert_type}:{affected_service}:{bucket_start_iso}`

- `alert_type`：来自 `alert_candidate.alert_type`，缺省 `unknown`。
- `affected_service`：缺省 `unknown`；查重时对 `unknown` 匹配「字段不存在或空串」。
- **时间桶**：默认 10 分钟窗口，以 `created_at`（或当前 UTC 时刻）向下取整到桶起点；格式 `YYYY-MM-DDTHH:MM:SSZ`。
- `check_duplicate` 查询条件：`alert_type` + `status=active` + `affected_service` + `created_at` 落在 `[bucket_start, bucket_end)`。
- 命中重复：返回 `{ ok: True, is_duplicate: True, existing_alert_id, idempotency_key }`；调用方应 `write_alert({"existing_alert_id": ...})` 累加证据。
- 未重复：返回 `{ ok: True, is_duplicate: False, existing_alert_id: None, idempotency_key }`；调用方正常 `write_alert(alert_candidate)`。

### 4.3 alerts-* 状态机

```text
                    write_alert（新预警）
                          │
                          ▼
                      ┌────────┐
                      │ active │  ← list_active_alerts 查询此状态
                      └────────┘
                          │
              acknowledge_alert（仅 active 可确认）
                          ▼
                  ┌───────────────┐
                  │ acknowledged  │
                  └───────────────┘
                          │
              resolved（规划，当前未实现 API）
                          ▼
                    ┌──────────┐
                    │ resolved │
                    └──────────┘
```

| 状态 | 含义 | 当前实现 |
|---|---|---|
| `active` | 待处理活跃预警 | 写入默认值；`list_active_alerts` 过滤条件 |
| `acknowledged` | 运维已确认 | `acknowledge_alert` 流转；写入 `payload.acknowledged_at` / `acknowledged_by` |
| `resolved` | 已关闭（规划） | 代码注释提及，尚无 API 与写入路径 |

**索引命名**：写入时按 `updated_at` 日期解析为 `alerts-{YYYY-MM-DD}`；查询使用 pattern `alerts-*`。

### 4.4 与 trigger_scanner 闭环

`trigger_scanner._persist_alert` 调用链：

```text
check_duplicate(alert_candidate)
  ├─ is_duplicate=True  → write_alert({ existing_alert_id })  // evidence_count +1
  └─ is_duplicate=False → write_alert(alert_candidate)        // 新 active 预警
```

## 5. 待开发功能清单（P0-P3）
- P0：确保 `alerts-*` 索引模板已通过 `init_indices` 任务创建（基础设施依赖）。
- P1：`resolved` 状态 API 与自动关闭策略。
- P2：预警列表分页、按 severity / affected_service 过滤。
- P3：主图 `alert_decision` 节点统一预警出口（M6）。

## 6. 模块状态表
| 模块名称 | 当前状态 | 最近修改时间 | 最近修改人/agent | 风险等级 | 备注 |
|---|---|---|---|---|---|
| `alert_service` | 已实现（M5） | 2026-06-22 | M5-01 Agent | 中 | 依赖 ES alerts-* 索引 |
| `dedup` | 已实现（M5） | 2026-06-22 | M5-02 Agent | 低 | 10 分钟时间桶幂等 |
| Alert 域整体 | M5 读写+去重可用 | 2026-06-22 | M5-10 Agent | 中 | resolved 未实现 |

## 7. 禁止重复实现清单
| 能力 | 正确位置 | 禁止行为 |
|---|---|---|
| 预警写入/查询 | `alert_service.py` | 禁止在 `trigger_scanner` 或 API 路由内直接调 ES index |
| 去重与幂等键 | `dedup.py` | 禁止在 `alert_service` 或子图节点内重复实现查重逻辑 |
| 预警 API | `api/v1/alerts.py` | 禁止在路由内拼装 ES 查询 DSL |

## 8. 真实实现与设计愿景差异
| 方向 | 设计愿景 | 当前状态 | 后续动作 |
|---|---|---|---|
| 三态状态机 | active → acknowledged → resolved | active/acknowledged 已实现 | P1 补 resolved API |
| 主图预警决策 | `graph_main.alert_decision` 统一出口 | 当前由规则子图 `assess_severity` 产出 `alert_candidate`，scanner 写库 | M6 主图收敛 |

## 9. 开发日志区
| 时间 | 修改内容 | 涉及文件 | 当前结果 | 遗留问题 |
|---|---|---|---|---|
| 2026-06-16 | 建立 alert 占位 + alerts API | `alert_service.py`、`dedup.py`、`api/v1/alerts.py` | API 骨架就绪 | 已由 M5 实现 |
| 2026-06-22 | M5-01：alert_service 三函数 | `alert_service.py` | alerts-* 读写 + active→acknowledged | 索引模板需 init |
| 2026-06-22 | M5-02：dedup 幂等键与查重 | `dedup.py` | 结构化返回 existing_alert_id | — |
| 2026-06-22 | M5-05：alerts API 去占位 | `api/v1/alerts.py` | /active 与 /ack 真实调 service | — |
| 2026-06-22 | M5-10：DEV 文档收敛 | `alert/DEV.md` | 状态机、幂等键、闭环已记录 | resolved 待 P1 |
