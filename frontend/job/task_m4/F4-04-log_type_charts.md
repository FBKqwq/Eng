# F4-04：日志类型图表配置 log_type_charts

## Agent 角色

配置专项 Agent — **为 7 类日志补齐 chartTemplates 与总体规划 §3.2 对齐**。

## 唯一负责文件

```
src/utils/logTypeMeta.js
```

## 禁止修改

- **仅允许修改**各类配置中的 `chartTemplates` 字段及相关注释
- 禁止改动 `defaultColumns`、`fallbackFilters`、`title` 等 F2 已验收字段（除非修复明显错误需备注）

## 前置依赖

- F2-05 已完成
- 总体规划 §3.2 图表带表

## 开发要求

### 1. 每类 2~3 个 chartTemplates

| logType | 模板示例 |
| --- | --- |
| application | errors 趋势、latency Top、error_code 分布 |
| behavior | terms 行为分布、funnel 简化、Top 商品/关键词 |
| web-server | errors 状态码、latency request_time、traffic Top URI |
| performance | infra_health 指标切换、p95 对比 |
| security | security risk 分布、Top IP、拦截趋势 |
| infrastructure | infra_health 组件比率、Kafka lag、资源趋势 |
| audit | terms 操作人/操作类型 |

### 2. 结构

```javascript
chartTemplates: [
  { id, template: 'errors'|'latency'|..., title, chartType: 'trend'|'bar'|'pie', options? }
]
```

### 3. 约束

- template id 必须属于六类聚合之一
- 简体中文 title

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 七类 | 每类 ≥2 个 template |
| AC-02 | 对齐 | 与 §3.2 表一致 |
| AC-03 | 不破坏 | F2 列/筛选未误改 |
| AC-04 | ChartBand | F4-03 可消费 |

## 完成定义（DoD）

- [ ] 仅扩展 chartTemplates 相关代码
- [ ] 更新 STATUS F4-04 行

## 下游消费说明

- F4-03 ChartBand 读取配置
