# M4-08：定时闭环单测 test_m4_scheduled

## Agent 角色

测试 Agent — 新建 M4 单测，ES/LLM 全 mock。

## 唯一负责文件（新建）

```
tests/test_m4_scheduled.py
```

## 禁止修改

- `app/services/analysis/*`、`report_service.py` 生产逻辑（bug 记备注）

## 前置依赖

- M4-04、M4-06 完成

## 测试范围

| 类别 | 内容 |
| --- | --- |
| report_service | mock ES，断言 write/list/get 结构与 report_id；无 placeholder |
| normalize_trigger | scheduled/rule 合法、非法 trigger_type |
| state | create_initial_state / append_node_trace / record_error |
| graph_scheduled | mock 聚合/搜索/report_chain，`run_scheduled_subgraph` 返回 report+node_trace；某节点异常走降级 |
| scheduler | mock `run_scheduled_subgraph` 与 `write_report`，`run_once` 闭环；write_report 被调用一次 |
| 无 placeholder | 各产出断言 |

≥10 个 test 函数；用 `monkeypatch` mock ES/LLM/子图，不联网。

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `pytest tests/test_m4_scheduled.py -v` 全绿 |
| AC-02 | 不依赖真实 ES/LLM |
| AC-03 | 覆盖闭环与降级路径 |
| AC-04 | 更新 `task_m4/STATUS.md` 本行 |
