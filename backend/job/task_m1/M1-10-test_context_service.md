# M1-10：测试 context_service

## Agent 角色

测试专项 Agent — **仅为 context_service 编写测试**。

## 唯一负责文件

```
tests/test_m1_context_service.py   （新建）
```

## 禁止修改

- `context_service.py`、`log_query_service.py` 及任何生产代码

## 前置依赖

- **M1-05 完成**

## 开发要求

### 1. 建议用例

| 用例 | 类型 |
| --- | --- |
| `test_get_trace_context_empty` | mock ES 返回 hits=[] → total=0 |
| `test_get_trace_context_es_offline` | available=False |
| `test_get_service_window_level_distribution` | mock 聚合含 ERROR/INFO |
| `test_get_similar_errors_total` | mock 命中 5 条 |
| `test_limit_capped_at_50` | 传入 limit=200，断言 ES size≤50 |
| `test_get_user_recent_actions`（integration） | ES 在线可选 |

### 2. 约束

- 不得依赖修改 `log_query_service`
- integration 测试可 skip

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 离线 mock | 全绿 |
| AC-02 | 隔离 | 仅一个测试文件 |
| AC-03 | 覆盖 | ≥5 个 test 函数 |

## 完成定义（DoD）

- [ ] 仅新增 `tests/test_m1_context_service.py`
- [ ] AC-01~AC-03 通过
