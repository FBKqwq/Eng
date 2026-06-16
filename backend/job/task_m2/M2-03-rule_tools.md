# M2-03：规则匹配工具 rule_tools

## Agent 角色

规则工具 Agent — **仅实现工具 10** `rule_match_log`。

## 唯一负责文件

```
app/services/tools/rule_tools.py
```

## 禁止修改

- `diagnosis/rule_engine.py` 核心规则表（除非任务单明确要求最小 match_log；默认只包装）
- 其他 tools 文件

## 前置依赖

- M1 完成

## 开发要求

### 1. 入参模型

定义 `RuleMatchLogInput`（或等价）：至少含单条日志 dict / 结构化字段，与 `rule_engine.match_log` 签名对齐。

### 2. `rule_match_log`

- 调用 `diagnosis.rule_engine.match_log`
- 透传 service 返回；若 service 仍为占位，返回 `ok: false` + 明确 `error`/`message`，**不得**再带 `placeholder: true`

### 3. 异常捕获

统一 `{"ok": false, "error": ...}` 结构。

## 验收标准

| # | 标准 |
| --- | --- |
| AC-01 | 无 `placeholder` 键 |
| AC-02 | 可传入样例日志 dict 并得到结构化响应 |
| AC-03 | 更新 STATUS 本行 |

## 备注

`match_log` 业务实装在 M5 前收敛；M2 只保证工具契约稳定。
