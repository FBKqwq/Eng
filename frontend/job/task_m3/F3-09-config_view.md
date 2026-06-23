# F3-09：配置页编排 config_view

## Agent 角色

页面装配 Agent — **配置快照页数据映射与 Kibana 入口**。

## 唯一负责文件

```
src/views/system/config.vue
```

## 禁止修改

- `ConfigSnapshotCard.vue`、api 文件结构

## 前置依赖

- F3-01 `getSystemStatus`
- F3-08 `ConfigSnapshotCard`
- `import.meta.env.VITE_KIBANA_URL`

## 开发要求

### 1. 数据映射

- 从 status 响应提取 kafka/es/llm 等配置 → 转为 `groups` props
- 字段缺失时展示「未配置」而非空白

### 2. 布局

- 单页组合 `ConfigSnapshotCard`
- 传入 `kibanaUrl` from env

### 3. 错误态

- status 失败：EmptyState + 重试

### 4. 约束

- 路由 `/system/config`

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 快照 | kafka/es/llm 等字段可见 |
| AC-02 | Kibana | env 有 URL 时外链可开 |
| AC-03 | 脱敏 | 敏感信息已打码 |
| AC-04 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `config.vue`
- [ ] 更新 STATUS F3-09 行

## 下游消费说明

- F7-03 可扩展 Kibana 深链；F3-10 DEV 文档
