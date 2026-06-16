# M2-05：预警工具 alert_tools

## Agent 角色

预警工具 Agent — **实现工具 7、8**（`alert_write_event`、`alert_check_duplicate`）。

## 唯一负责文件

```
app/services/tools/alert_tools.py
```

## 禁止修改

- `alert/alert_service.py`、`alert/dedup.py` 实现体（M5）
- 其他 tools 文件

## 前置依赖

- M1 完成

## 开发要求

### 1. `alert_write_event`（写类，工具 7）

- Pydantic 入参模型包装预警 payload
- 调用 `alert_service.write_alert`
- docstring 标明写类限制

### 2. `alert_check_duplicate`（读类，工具 8）

- 调用 `alert.dedup.check_duplicate`
- 返回是否重复及元数据

### 3. `alert_list_active`

- 第二阶段，保持未实装或明确 `ok: false`

### 4. 去除 7、8 的 `placeholder: true`

## 验收标准

| # | 标准 |
| --- | --- |
| AC-01 | 工具 7、8 无 `placeholder` |
| AC-02 | 两函数返回统一 `{ok: bool, ...}` |
| AC-03 | 更新 STATUS 本行 |
