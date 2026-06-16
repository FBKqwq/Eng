# M2-08：tools 模块文档收敛

## Agent 角色

文档 Agent — **更新 `tools/DEV.md`**，标记 M2 完成状态。

## 唯一负责文件

```
app/services/tools/DEV.md
```

## 前置依赖

- M2-06 完成（可与 M2-07 并行）

## 开发要求

1. 状态表：10 个工具由「占位」改为「已实现」
2. 记录 `get_langchain_tools` 读写分离约定
3. 开发日志追加 M2 完成条目
4. `create_mcp_server` 仍标注 M7

## 验收标准

| # | 标准 |
| --- | --- |
| AC-01 | DEV.md 与代码一致 |
| AC-02 | 无「待 M2」与已完成事实矛盾 |
| AC-03 | 更新 STATUS 本行；若 M2-07 亦完成，可在备注写「M2 里程碑可收口」 |
