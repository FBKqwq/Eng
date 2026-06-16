# M1-09：测试 aggregation_service

## Agent 角色

测试专项 Agent — **仅为 aggregation_service 编写测试**。

## 唯一负责文件

```
tests/test_m1_aggregation_service.py   （新建）
```

## 禁止修改

- `aggregation_service.py` 及任何生产代码

## 前置依赖

- **M1-01 + M1-04 完成**

## 开发要求

### 1. 测试分层

| 类型 | 用例 |
| --- | --- |
| 单元 | `validate_aggregate_request` 失败时不调用 ES（mock `get_es_client`） |
| 单元 | `top_n` 截断为 50 |
| 单元 | 非法 `group_by` 返回 `available=False` 或校验错误 |
| 集成 | ES 在线 + 有数据时 `aggregate_traffic` buckets 非空 |

### 2. Mock 规范

```python
@patch("app.services.elasticsearch.aggregation_service.get_es_client")
def test_aggregate_es_offline(mock_client):
    mock_client.side_effect = Exception("connection refused")
    ...
```

### 3. 集成测试数据

- 文档注明需先执行：`python -m app.tasks.run_log_producer --count 100`
- 使用 `@pytest.mark.integration` 标记

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 离线 | mock 用例全绿 |
| AC-02 | 在线 | integration 用例在 ELK 环境通过（可 skip） |
| AC-03 | 白名单 | 非法 group_by 不触发 client.search（可用 mock 断言 call_count=0） |
| AC-04 | 隔离 | 仅一个测试文件 |

## 完成定义（DoD）

- [ ] 仅新增 `tests/test_m1_aggregation_service.py`
- [ ] ≥5 个 test 函数
- [ ] AC-01~AC-04 通过
