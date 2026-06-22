# F1-11：布局骨架 layout_shell

## Agent 角色

布局骨架专项 Agent — **仅实现 aside + main 双栏骨架，组合侧边栏/顶部条/健康点**。

## 唯一负责文件

```
src/layout/index.vue
```

## 禁止修改

- `SidebarTree.vue`、`TopBar.vue`、`PipelineHealthDot.vue`（只 import）
- `menu.js`、`router/index.js`、composables（只 import）

## 前置依赖

- F1-08 SidebarTree、F1-09 TopBar、F1-10 PipelineHealthDot
- F1-02 `provideTimeRange`

## 开发要求

### 1. 双栏结构

```text
aside（侧边栏）：品牌区 + SidebarTree + PipelineHealthDot（底部）
content：TopBar + main(<router-view/>)
```

### 2. 时间窗注入

- 顶层调用 `provideTimeRange()`，向所有子页下发全局时间窗。

### 3. 约束

- **仅组合，不写业务**；新增页面不改本模板（只改 menu.js + router）。
- 配色/间距复用 F1-01 令牌。
- 简体中文文案。

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 双栏 | aside + main 正确布局，main 内 `router-view` |
| AC-02 | 组合 | SidebarTree/TopBar/PipelineHealthDot 均挂载 |
| AC-03 | 时间窗 | 调用 `provideTimeRange()` |
| AC-04 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `layout/index.vue`
- [ ] 不修改 DEV.md

## 下游消费说明（供其他 Agent 只读）

- F1-16 router 以本组件为根布局，子页通过 children 挂载
