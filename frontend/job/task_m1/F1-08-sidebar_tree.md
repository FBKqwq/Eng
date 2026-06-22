# F1-08：侧边栏树组件 sidebar_tree

## Agent 角色

侧边栏渲染专项 Agent — **仅实现递归树目录组件（折叠/高亮/自动展开）**。

## 唯一负责文件

```
src/layout/components/SidebarTree.vue
src/layout/components/SidebarTreeNode.vue
```

## 禁止修改

- `menu.js`（只 import）、`layout/index.vue`、`TopBar.vue`、`router/index.js`

## 前置依赖

- F1-07 `menu.js` 提供 `menuTree`

## 开发要求

### 1. `SidebarTree.vue`

- 读取 `menuTree`，渲染两级树。
- 仅负责渲染，**目录数据不在此硬编码**。

### 2. `SidebarTreeNode.vue`（递归节点）

- 叶子节点用 `router-link` 路由跳转；分组节点可折叠（不可路由）。
- 当前路由命中的叶子高亮，其父分组**自动展开**。
- 折叠/展开为组件内交互状态。

### 3. 约束

- 不直接 `axios`/`fetch`。
- 配色复用 F1-01 侧边栏令牌。
- 简体中文注释。

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 渲染 | 完整渲染 menuTree 两级结构 |
| AC-02 | 高亮 | 命中叶子高亮 |
| AC-03 | 自动展开 | 命中叶子的父分组自动展开 |
| AC-04 | 折叠 | 分组可手动折叠/展开 |

## 完成定义（DoD）

- [ ] 仅修改 SidebarTree.vue、SidebarTreeNode.vue
- [ ] 数据来自 menu.js，未硬编码目录
- [ ] 不修改 DEV.md

## 下游消费说明（供其他 Agent 只读）

- F1-11 layout 在 aside 中挂载 `SidebarTree`
