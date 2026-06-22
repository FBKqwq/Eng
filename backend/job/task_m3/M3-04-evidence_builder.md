# M3-04：证据包构建 evidence_builder

## Agent 角色

证据压缩 Agent — 将原始日志 + 聚合指标压缩为受控证据包（纯代码，不用 LLM）。

## 唯一负责文件

```
app/services/langchain/evidence_builder.py
```

## 禁止修改

- 其他 langchain 文件

## 前置依赖

- M2 完成

## 开发要求

### 1. `build_evidence_package(raw_logs, metrics=None, *, max_logs=50) -> dict`
压缩流程：**过滤 → 分组 → 采样 → 摘要**
- 过滤：优先保留 ERROR/WARN 级别日志
- 分组：按 `service_name` / `error_code` / `log_level` 聚类计数
- 采样：每组取代表样本，总条数 ≤ `max_logs`
- 摘要：附带 `top_services`、`top_error_codes`、`total_logs`、`error_count` 等统计
- 合并传入的 `metrics`（聚合结果）到证据包

### 2. 返回结构
```python
{
  "ok": True,
  "evidence_package": {
    "summary": {...},          # 计数与 top 列表
    "grouped": {...},          # 分组摘要
    "samples": [...],          # 采样日志（≤ max_logs）
    "metrics": {...},          # 透传聚合指标
  },
  "input_log_count": int,
  "sampled_count": int,
}
```
- 空输入返回 `ok: True` + 空证据包，不报错
- **无 placeholder 键**

### 3. 约定
- 纯代码实现，不调用 LLM/ES
- 控制 token：samples 字段裁剪长 message

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `sampled_count <= max_logs` |
| AC-02 | ERROR 日志优先保留 |
| AC-03 | 含 summary/grouped/samples/metrics 结构；无 placeholder |
| AC-04 | 空输入不报错 |
| AC-05 | 更新 `task_m3/STATUS.md` 本行 |
