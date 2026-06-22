# M6-06：主图单测 test_m6_main

## Agent 角色

测试 Agent — 新建 M6 单测并完成回归校正，ES/LLM 全 mock。

## 唯一负责文件

```
tests/test_m6_main.py        # 新建
tests/test_m4_scheduled.py   # 仅在 M6-03 改变契约时校正
tests/test_m5_rule.py        # 仅在 M6-04 改变契约时校正
```

## 禁止修改

- 任何 `app/services/**`、`app/api/**` 生产逻辑（bug 记备注）

## 前置依赖

- M6-02 ~ M6-05 完成

## 测试范围

| 类别 | 内容 |
| --- | --- |
| alert_chain | LLM 可用/降级两路径 |
| graph_main | scheduled / rule 两路由跑通；merge_result 归一化；alert_decision（severity≥high 出预警、去重）；persist_result 仅此处写库 |
| 路由分发 | route 按 trigger_type 正确分发 |
| 降级 | 某节点异常 → errors 非空、整图不崩 |
| analysis API | `/runs/recent`、`/run`（TestClient + mock run_main_graph / list_recent_reports）|
| 回归 | 运行 M1~M5 全量；若 M6-03/04 改变 run_once/scan_once 契约，校正 test_m4/test_m5 |
| 无 placeholder | 各产出断言 |

≥12 个 test 函数；`monkeypatch` mock ES/LLM/子图，不联网。

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `pytest tests/test_m6_main.py -v` 全绿 |
| AC-02 | M1~M5 全量回归通过（必要时已校正 test_m4/test_m5） |
| AC-03 | 覆盖路由、预警决策、去重、降级路径 |
| AC-04 | 更新 `task_m6/STATUS.md` 本行 |
