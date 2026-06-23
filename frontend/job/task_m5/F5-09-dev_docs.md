# F5-09：F5 开发文档 dev_docs

## Agent 角色

文档 Agent — **收敛 F5 智能线至 DEV.md**。

## 唯一负责文件

```
frontend/DEV.md
```

## 禁止修改

- 业务代码

## 前置依赖

- F5-01 ~ F5-08 完成

## 开发要求

- 诊断中心四区与 §5 耦合规范落地说明
- 链路追踪页与 trace API 说明
- node_trace → DiagnosisStageRing 映射约定
- F5 开发日志

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 诊断 | 诊断页状态准确 |
| AC-02 | 链路 | trace 页状态准确 |
| AC-03 | 规范 | §5 禁止项已记录 |
| AC-04 | 日志 | F5 条目已追加 |

## 完成定义（DoD）

- [ ] 仅修改 `frontend/DEV.md`
- [ ] 更新 STATUS F5-09 行

## 下游消费说明

- 全员维护基线
