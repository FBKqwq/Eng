# F3-07：组件状态页 components_view

## Agent 角色

页面装配 Agent — **六组件状态卡矩阵，迁移旧系统页能力**。

## 唯一负责文件

```
src/views/system/components.vue
```

## 禁止修改

- `StatusCard.vue`、api、旧 `views/system/index.vue`（只读参考）

## 前置依赖

- F3-01 `getSystemStatus`
- F3-02 归一化工具
- F3-06 `StatusCard`
- 旧 `index.vue` / `ServiceStatusCard` 行为对齐

## 开发要求

### 1. 数据

- 轮询或 mount 拉取 `getSystemStatus`（间隔可与 `PipelineHealthDot` 协调，建议 60s）
- `normalizeComponentCards(status)` → 网格数据

### 2. 布局

- 响应式网格：Kafka / ES / Logstash / Kibana / Backend / LLM
- 每格一个 `StatusCard`
- 全局 loading / 错误 / 重试

### 3. 兜底展示

- 应用 F3-02 全部兜底规则
- ES unknown 时 UI 标注说明

### 4. 约束

- 不删除旧路由文件；`/system` 重定向仍指向本页（F1-16）
- `/temp/developer` 复用本视图

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 六卡 | 6+ 组件卡正确渲染 |
| AC-02 | 真实数据 | 反映 `/system/status` |
| AC-03 | 兜底 | containers/services/ES unknown 规则生效 |
| AC-04 | 无回退 | 不低于旧系统页信息量 |

## 完成定义（DoD）

- [ ] 仅修改 `components.vue`
- [ ] 更新 STATUS F3-07 行

## 下游消费说明

- 系统运维默认落地页；F3-10 DEV 记录迁移说明
