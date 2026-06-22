# M5-09：规则闭环单测 test_m5_rule

## Agent 角色

测试 Agent — 新建 M5 单测，ES/LLM 全 mock。

## 唯一负责文件（新建）

```
tests/test_m5_rule.py
```

## 禁止修改

- `app/services/analysis/*`、`alert/*`、`diagnosis/*` 生产逻辑（bug 记备注）

## 前置依赖

- M5-06、M5-07 完成

## 测试范围

| 类别 | 内容 |
| --- | --- |
| rule_definitions | 含三类规则、PAY_FAIL trigger_subgraph=True |
| rule_engine | match_log 命中 PAY_FAIL / 未命中；classify_by_rules 兼容 |
| alert_service | mock ES，write/list/ack 结构与状态机；无 placeholder |
| dedup | 幂等键稳定；check_duplicate 命中/未命中 |
| graph_rule | mock context/diagnosis_chain，`run_rule_subgraph` 返回 report+alert_candidate+node_trace；降级路径 |
| trigger_scanner | mock 子图/write_report/write_alert/check_duplicate，`scan_once` 闭环；重复触发不重复写预警 |
| 无 placeholder | 各产出断言 |

≥12 个 test 函数；用 `monkeypatch` mock ES/LLM/子图，不联网。

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `pytest tests/test_m5_rule.py -v` 全绿 |
| AC-02 | 不依赖真实 ES/LLM |
| AC-03 | 覆盖闭环、去重与降级路径 |
| AC-04 | 更新 `task_m5/STATUS.md` 本行 |
