# F2-05：日志类型元数据 log_type_meta

## Agent 角色

工具专项 Agent — **完善 7 类日志展示元数据与兜底筛选**。

## 唯一负责文件

```
src/utils/logTypeMeta.js
```

## 禁止修改

- views、components、api

## 前置依赖

- F1-04 骨架已存在

## 开发要求

### 1. 每类 logType 配置项

对齐总体规划 §3.2 表：

| 字段 | 说明 |
| --- | --- |
| `title` / `icon` | 展示用 |
| `logType` | API 用 snake_case 值 |
| `defaultColumns` | LogTable 默认列 |
| `fallbackFilters` | fields 接口失败时的筛选项 |
| `chartTemplates` | F4 用模板 id 列表（F2 仅占位引用，不实现图表） |

### 2. 七类 key

`application`、`behavior`、`web-server`、`performance`、`security`、`infrastructure`、`audit`

### 3. `getLogTypeMeta(key)`

- 未知 key 返回安全默认 + console.warn

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 七类 | 7 类配置齐全 |
| AC-02 | 默认列 | 与总体规划表一致 |
| AC-03 | 兜底筛选 | 每类 ≥2 个 fallbackFilters |
| AC-04 | chartTemplates | 预留 F4 模板 id（可为空数组） |

## 完成定义（DoD）

- [ ] 仅修改 `logTypeMeta.js`
- [ ] 更新 STATUS F2-05 行

## 下游消费说明

- F2-04 兜底；F2-07 views 读配置；F4-04 扩展 chartTemplates
