# F1-01：设计令牌与全局样式 design_tokens

## Agent 角色

前端样式基建专项 Agent — **仅建立全局设计变量与基础样式骨架**（色板、间距、卡片阴影、栅格工具类）。

## 唯一负责文件

```
src/assets/styles/index.css
```

## 禁止修改

- 任何 `.vue`、`.js` 文件
- `main.js`（若需引入样式，由本任务在文档中说明引入位置，但不在本任务改 main.js；F1-11 布局或 main 引入由对应 Agent 处理）

## 前置依赖

- 无（F1 第一站，建议最先完成，供所有组件复用）

## 开发要求

### 1. 设计令牌（CSS 变量，挂在 `:root`）

至少包含：

| 类别 | 变量示例 |
| --- | --- |
| 背景 | `--color-bg`、`--color-surface` |
| 边框 | `--color-border` |
| 文本 | `--color-text`、`--color-text-secondary` |
| 主色 | `--color-primary` |
| 语义色 | `--color-success`、`--color-warning`、`--color-danger`、`--color-info` |
| 侧边栏 | `--color-sidebar`、`--color-sidebar-text`、`--color-sidebar-text-muted`、`--color-sidebar-border`、`--color-sidebar-hover` |
| 圆角 | `--radius-sm`、`--radius-md` |
| 阴影 | `--shadow-card` |

### 2. 全局基础样式与工具类

- `* { box-sizing: border-box }`、`body` 字体与默认背景。
- 通用区块：`.page-section`（卡片容器：背景/圆角/内边距/阴影）。
- 栅格工具类：`.page-grid`、`.page-grid-2`、`.page-grid-3`（CSS Grid，间距用令牌）。

### 3. 约束

- 仅 CSS，不引入任何 CSS 框架。
- 配色须满足语义色（绿/黄/红/蓝）可被仪表、徽章、状态点复用。
- 简体中文注释。

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 令牌齐全 | `:root` 含上表全部变量 |
| AC-02 | 语义色 | success/warning/danger/info 四色齐全 |
| AC-03 | 栅格 | `.page-grid-2`/`.page-grid-3` 可用 |
| AC-04 | 构建 | 引入后 `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `src/assets/styles/index.css`
- [ ] 令牌与工具类齐全，语义色可复用
- [ ] 不修改 DEV.md（交给 F1-17）

## 下游消费说明（供其他 Agent 只读）

- F1-05/F1-06 通用组件、F1-08/09/10/11 布局组件均复用本令牌
- 语义色为 `SeverityBadge`、`GaugeChart`、`PipelineHealthDot` 的配色唯一来源
