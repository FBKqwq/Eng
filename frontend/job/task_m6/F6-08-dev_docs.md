# F6-08：F6 开发文档 dev_docs

## Agent 角色

文档 Agent — **收敛 F6 结果线至 DEV.md**。

## 唯一负责文件

```
frontend/DEV.md
```

## 禁止修改

- 业务代码

## 前置依赖

- F6-01 ~ F6-07 完成

## 开发要求

- reports/alerts API 与 USE_MOCK 切换记录
- 报告页、预警页、全局角标状态
- F6 开发日志

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | API | reports/alerts 文档化 |
| AC-02 | 页面 | 两页状态准确 |
| AC-03 | 全局 | TopBar/摘要接线说明 |
| AC-04 | 日志 | F6 条目已追加 |

## 完成定义（DoD）

- [ ] 仅修改 `frontend/DEV.md`
- [ ] 更新 STATUS F6-08 行

## 下游消费说明

- F7 增强开发基线
