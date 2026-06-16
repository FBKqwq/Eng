# M1-07：测试 field_catalog

## Agent 角色

测试专项 Agent — **仅为 field_catalog 编写单元测试**。

## 唯一负责文件

```
tests/test_m1_field_catalog.py   （新建）
```

## 禁止修改

- `field_catalog.py` 及任何生产代码
- 其他测试文件

## 前置依赖

- **M1-01 完成**

## 开发要求

### 1. 测试范围（纯单元，不依赖 ES）

| 测试类/函数 | 覆盖点 |
| --- | --- |
| `test_list_registered_log_types` | 返回 7 类 |
| `test_behavior_funnel_steps` | 5 步顺序 |
| `test_validate_aggregate_field_rejects_text` | message / terms → False |
| `test_validate_aggregate_field_accepts_keyword` | error_code / terms → True |
| `test_resolve_index_pattern_multi` | 多类型 pattern 含逗号 |
| `test_validate_aggregate_request_invalid_group_by` | ok=False |
| `test_unknown_log_type_catalog` | 无 placeholder 键（或 ok=False 结构） |

### 2. 约束

- 使用 `pytest`
- 不 mock ES
- 测试文件可独立运行：`pytest tests/test_m1_field_catalog.py -v`

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 执行 | `pytest tests/test_m1_field_catalog.py -v` 全绿 |
| AC-02 | 隔离 | git diff 仅含 `tests/test_m1_field_catalog.py` |
| AC-03 | 覆盖 | 至少 7 个 test 函数 |

## 完成定义（DoD）

- [ ] 仅新增一个测试文件
- [ ] AC-01~AC-03 通过
