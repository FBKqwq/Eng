# F2-04：动态筛选栏 DynamicFilterBar

## Agent 角色

监控组件 Agent — **字段目录驱动的动态筛选器**。

## 唯一负责文件

```
src/components/monitor/DynamicFilterBar.vue
```

## 禁止修改

- LogMonitorShell、LogTable、api/logs.js（只 import）、logTypeMeta（只 import）

## 前置依赖

- F2-01 `getLogFields`
- F2-05 `getLogTypeMeta` 兜底筛选项（可并行开发，完成后联调）

## 开发要求

### 1. Props / Events

- `logType`（必填）
- `modelValue` / `update:modelValue` — 筛选对象
- `keyword` / `update:keyword`

### 2. 数据加载

- mount 时 `getLogFields(logType)` 渲染 filterable 字段
- 失败：读 `getLogTypeMeta(logType).fallbackFilters`，顶部标注「字段目录兜底」
- loading 骨架

### 3. 控件映射

- `keyword` / `terms` / `range` 等按字段 type 渲染 input/select/范围
- 提供「重置筛选」按钮

### 4. 约束

- 不发起 search 请求（由 Shell 监听筛选变更）
- 简体中文标签

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 动态 | fields 成功时按接口渲染 |
| AC-02 | 兜底 | 失败时 meta 兜底 + 标注 |
| AC-03 | 双向绑定 | v-model 筛选与关键字可用 |
| AC-04 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `DynamicFilterBar.vue`
- [ ] 更新 STATUS F2-04 行
