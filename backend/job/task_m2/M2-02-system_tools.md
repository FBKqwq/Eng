# M2-02：系统健康工具 system_tools

## Agent 角色

系统健康组合工具 Agent — **仅实现工具 9** `system_health_check`。

## 唯一负责文件

```
app/services/tools/system_tools.py
```

## 禁止修改

- `elasticsearch/cluster_status.py`、`kafka/`、`docker_status` 实现体
- 其他 tools 文件

## 前置依赖

- M1 完成
- 必读：`get_elasticsearch_health_snapshot`、Kafka 集群状态 API、`docker_status`（或等价函数）

## 开发要求

### 1. `system_health_check() -> dict`

组合探测并返回结构化快照：

```python
{
  "ok": bool,           # 三者均可用时为 true，或按总体规划定义降级语义
  "tool": "system_health_check",
  "elasticsearch": {...},
  "kafka": {...},
  "docker": {...},
}
```

### 2. 异常处理

单个子系统失败时记录 `available: false` 与 `error`，不导致整函数抛异常；`ok` 可反映「是否全部健康」。

### 3. 去除 `placeholder: true`

## 验收标准

| # | 标准 |
| --- | --- |
| AC-01 | 无 `placeholder` 键 |
| AC-02 | 返回含 es/kafka/docker 三节 |
| AC-03 | 离线/mock 环境下可调用并返回结构化 dict |
| AC-04 | 更新 STATUS 本行 |
