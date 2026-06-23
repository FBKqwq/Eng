# F3-08：配置快照卡 ConfigSnapshotCard

## Agent 角色

系统展示 Agent — **只读配置键值分组展示**。

## 唯一负责文件

```
src/components/system/ConfigSnapshotCard.vue
```

## 禁止修改

- views、api

## 前置依赖

- F3-01 status 响应中配置字段契约
- `VITE_KIBANA_URL` 环境变量约定（Kibana 按钮由 view 或本卡 props 传入）

## 开发要求

### 1. Props

- `groups` — `[{ title, items: [{ key, value, sensitive? }] }]`
- `kibanaUrl` — 可选，有值时展示「打开 Kibana」外链按钮（`target="_blank"`）

### 2. 分组

- Kafka：bootstrap、topic 等
- ES：hosts、索引模式
- LLM：provider、model（**脱敏**，密钥永不展示）

### 3. UI

- 只读键值卡；敏感字段打码 `***`
- 无编辑能力

### 4. 约束

- 不调 API；F7-03 可增强 Kibana 链接生成

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 分组 | 多组键值可读 |
| AC-02 | 脱敏 | LLM 密钥类字段不泄露 |
| AC-03 | Kibana | URL 配置时按钮可用 |
| AC-04 | 只读 | 无输入控件 |

## 完成定义（DoD）

- [ ] 仅修改 `ConfigSnapshotCard.vue`
- [ ] 更新 STATUS F3-08 行

## 下游消费说明

- F3-09 `config.vue` 装配数据
