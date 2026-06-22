# F1-16：路由树汇总 router

## Agent 角色

路由汇总专项 Agent — **仅注册嵌套路由 + 旧路由重定向 + meta.title**。

## 唯一负责文件

```
src/router/index.js
```

## 禁止修改

- `layout/index.vue`（只 import）、所有 views（只 import）、`menu.js`

## 前置依赖

- F1-11 layout 根布局
- F1-12~15 全部 16 个页面 view 已存在（静态 import 需文件存在方能构建）

## 开发要求

### 1. 根布局 + 子路由

- 根 `path:'/'` → `component: Layout`，`redirect:'/dashboard'`。
- children 注册 16 个页面，每个含 `name`、`component`、`meta.title`（供 TopBar）。

### 2. 旧路由重定向

```text
/                → /dashboard
monitor          → /monitor/application
diagnosis        → /analysis/diagnosis
results          → /analysis/reports
system           → /system/components
```

### 3. 开发者入口

- `/temp/developer` → 复用 `SystemComponents` 视图。

### 4. 约束

- 使用 `createWebHistory`。
- `meta.title` 与 menu.js 标题一致。
- 简体中文标题。

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 16 路由 | 全部页面可路由访问 |
| AC-02 | 重定向 | 5 条旧路由正确重定向 |
| AC-03 | meta.title | 每路由含 title，TopBar 正确显示 |
| AC-04 | 开发者入口 | `/temp/developer` 可达 |
| AC-05 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `router/index.js`
- [ ] 不修改 DEV.md

## 下游消费说明（供其他 Agent 只读）

- F1-17 DEV 文档据此更新路由表
