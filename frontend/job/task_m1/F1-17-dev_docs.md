# F1-17：DEV 文档收敛 dev_docs

## Agent 角色

文档 Agent — **统一更新前端 DEV 基线（不碰业务代码）**。

## 唯一负责文件

```
frontend/DEV.md
```

## 禁止修改

- 任何 `.vue`、`.js`、`.css` 文件

## 前置依赖

- F1-01 ~ F1-16 全部完成（构建通过、可导航）

## 开发要求

更新 `frontend/DEV.md` 使之与 F1 落地一致：

### 1. 路由表

- 用 README §2.1 的新路由树替换旧 5 路由表（`/`、`/monitor`、`/diagnosis`、`/results`、`/system`）。
- 标注旧路由已重定向；`/temp/developer` 复用组件运行状态页。

### 2. 目录职责

- 增补 `composables/`、`components/common/`（含 charts）、`layout/menu.js`、各页面组件目录。

### 3. 状态表

- 反映 F1 落地：骨架/布局/路由/通用件/图表封装/API wrapper 为「可用」；监控/分析/系统页为「占位（待 F2~F6）」。

### 4. 开发约束

- 增补：图表只进 charts/、新增依赖仅 ECharts、占位须标注 pending-api、mock 须可识别。

### 5. 开发日志

- 追加一行 F1 骨架重构落地记录（日期、内容、涉及文件、结果、遗留）。

### 6. 约束

- 全文简体中文。
- 不引入与代码不符的描述（以实际代码为准）。

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 路由表 | DEV.md 路由表与新路由一致 |
| AC-02 | 目录 | 目录职责覆盖 composables/common/charts/menu |
| AC-03 | 状态表 | 反映 F1 真实状态（可用/占位） |
| AC-04 | 日志 | 追加 F1 落地开发日志 |

## 完成定义（DoD）

- [ ] 仅修改 `frontend/DEV.md`
- [ ] 与实际代码一致，全文简体中文
- [ ] 更新 `task_m1/STATUS.md` 第 4 节标注 F1 里程碑收尾

## 下游说明

- F2~F7 后续里程碑在此基线上继续维护
