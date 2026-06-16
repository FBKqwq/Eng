# M1-08：测试 index_service

## Agent 角色

测试专项 Agent — **仅为 index_service / init_indices 编写测试**。

## 唯一负责文件

```
tests/test_m1_index_service.py   （新建）
```

## 禁止修改

- `index_service.py`、`init_indices.py` 及任何生产代码

## 前置依赖

- **M1-02 完成**
- M1-03 可选（本测试可只测 service 层函数）

## 开发要求

### 1. 测试分层

| 类型 | 说明 |
| --- | --- |
| 无 ES 单测 | mock `get_es_client`，验证 `init_all_indices` 在 ES 抛错时返回 `ok=False` |
| 集成测（可选） | `@pytest.mark.integration`，仅 ES 在线时执行 `verify_templates` |

### 2. 建议用例

- `test_init_all_indices_es_unavailable`：mock client.search/indices 抛 `ConnectionError` → `ok=False`
- `test_verify_templates_missing`：mock 返回空 → `missing` 非空
- `test_init_all_indices_success`（integration）：ES 在线 → `ok=True`
- `test_no_placeholder_in_response`：检查返回值无 `placeholder` 键

### 3. 约束

- integration 测试失败不得阻塞 CI 时，使用 `pytest.importorskip` 或自定义 marker skip
- 不得修改生产代码来「迎合测试」

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 离线可跑 | 无 ES 时 `pytest tests/test_m1_index_service.py -v` 至少 mock 用例全绿 |
| AC-02 | 隔离 | 仅新增一个测试文件 |
| AC-03 | 覆盖 | ≥4 个 test 函数 |

## 完成定义（DoD）

- [ ] 仅新增 `tests/test_m1_index_service.py`
- [ ] AC-01~AC-03 通过
