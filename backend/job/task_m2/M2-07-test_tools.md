# M2-07：工具层单测 test_m2_tools

## Agent 角色

测试 Agent — **新建 M2 工具单测**，ES/Kafka 离线用 mock。

## 唯一负责文件

```
tests/test_m2_tools.py
```

## 可修改

```
pytest.ini 或 pyproject.toml   # 可选：注册 integration mark，消除 M1 遗留 warning
```

## 禁止修改

- `app/services/tools/*.py` 业务逻辑（发现 bug 记备注，由对应任务 Agent 修）

## 前置依赖

- M2-06 完成

## 测试范围

| 类别 | 内容 |
| --- | --- |
| ES 五工具 | mock `search_logs` / `aggregate` / context 三函数，断言 `ok` 与结构 |
| system | mock 子系统探测，断言三节存在 |
| rule / report / alert | mock 底层 service，断言无 `placeholder` |
| registry | 工具数量、读写分离、`list_registered_tool_names` |
| 异常路径 | 至少 1 例 service 抛错 → 工具返回 `ok: false` |

## 验收标准

| # | 标准 |
| --- | --- |
| AC-01 | `pytest tests/test_m2_tools.py` 全绿 |
| AC-02 | 不依赖真实 ES 集群（integration 可 skip） |
| AC-03 | 更新 STATUS 本行 |
