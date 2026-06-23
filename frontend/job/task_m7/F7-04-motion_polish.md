# F7-04：动效抛光 motion_polish

## Agent 角色

体验抛光 Agent — **图表过渡、卡片 hover、reduce-motion**。

## 唯一负责文件

```
src/assets/styles/index.css
src/components/common/charts/BaseChart.vue
```

## 禁止修改

- 业务页面、其他 chart 封装

## 前置依赖

- F4 图表已上线
- skill §9.4 图表动效、§9.2 卡片层级

## 开发要求

### 1. index.css

- `@media (prefers-reduced-motion: reduce)` 全局减弱动画
- 卡片 hover：轻阴影 + translateY(-1px)，reduced-motion 时仅阴影
- 统一 `--transition-fast` / `--transition-chart` 令牌（若未有则补充）

### 2. BaseChart.vue

- setOption 使用 `notMerge` 策略与 `animationDuration` 统一（建议 300~500ms）
- loading → data 切换平滑
- reduced-motion 时 `animation: false`

### 3. 约束

- 不改数据逻辑
- 禁止阻碍阅读的闪烁/自动轮播

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 图表 | 数据更新有过渡 |
| AC-02 | 卡片 | hover 一致 |
| AC-03 | a11y | reduce-motion 生效 |
| AC-04 | 构建 | 通过 |

## 完成定义（DoD）

- [ ] 仅修改上述两文件
- [ ] 更新 STATUS F7-04 行

## 下游消费说明

- 全站图表与卡片体验一致
