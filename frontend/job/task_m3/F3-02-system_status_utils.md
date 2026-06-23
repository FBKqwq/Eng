# F3-02：系统状态工具 system_status_utils

## Agent 角色

工具专项 Agent — **归一化 system/status 响应与 DEV.md 兜底规则**。

## 唯一负责文件

```
src/utils/systemStatus.js
```

## 禁止修改

- views、components、api

## 前置依赖

- F1 已完成（`systemStatus.js` 骨架若存在则扩展）
- 必读：`frontend/DEV.md` 中 containers/services 兜底、ES health unknown 规则

## 开发要求

### 1. 状态归一化

- 输入 `getSystemStatus()` 原始响应
- 输出各组件统一结构：`{ key, label, status, detail, port?, container? }`
- 覆盖：Kafka、ES、Logstash、Kibana、Backend、LLM

### 2. 兜底规则（与 DEV.md 一致）

- `containers` 与 `services` 字段互备：一方缺失时用另一方推断
- ES `health === 'unknown'` 时以容器运行态兜底展示，标注「健康未知，按容器态展示」
- 离线/超时返回可识别错误码供 UI 展示

### 3. 链路四节点

- `getPipelineNodes(status)` — 生产→Kafka→Logstash→ES 四节点着色键（`healthy`/`degraded`/`down`/`unknown`）

### 4. 链路健康微状态（供 F1-10 / PipelineHealthDot）

- `derivePipelineHealthTone(status)` → `'success' | 'warning' | 'danger' | 'unknown'`
- 输入为 `getSystemStatus()` 解包后的 `res.data`（非信封顶层）
- 规则：综合 `kafka.available`、`elasticsearch.available`、`docker.available` 与 `containers.*.status`；**禁止**依赖 `overall` / `pipeline_healthy`

### 5. 约束

- 纯函数，无副作用；不调 API
- 简体中文 JSDoc

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 六组件 | 6+ 组件状态可归一化 |
| AC-02 | 兜底 | containers/services 互备逻辑可用 |
| AC-03 | ES unknown | unknown 时容器态兜底 |
| AC-04 | 链路节点 | 四节点着色数据可生成 |
| AC-05 | 微状态 | `derivePipelineHealthTone` 不读伪字段 |

## 完成定义（DoD）

- [ ] 仅修改 `src/utils/systemStatus.js`
- [ ] 更新 STATUS F3-02 行

## 下游消费说明

- F3-03 `PipelineGraph` 消费四节点数据
- F3-06 `StatusCard` 消费单卡归一化结构
- F3-07 `components.vue` 矩阵渲染
