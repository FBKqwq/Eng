# F5-02：诊断输入区 DiagnosisEntryPanel

## Agent 角色

诊断交互 Agent — **三种诊断入口表单**。

## 唯一负责文件

```
src/components/analysis-diagnosis/DiagnosisEntryPanel.vue
```

## 禁止修改

- api、其他 diagnosis 组件、views

## 前置依赖

- F5-01 API 契约（payload 形状）
- 路由 query 预填：来自预警中心 `alert_id`（F6 跳转，本任务预留 props）

## 开发要求

### 1. 入口模式（Tab 或分段）

- 粘贴异常日志（textarea）
- 选择活跃预警（下拉，数据由父级传入或 emit 请求）
- 服务名 + 时间窗（读全局 useTimeRange 或局部覆盖）

### 2. Events

- `@submit` — 携带规范化 payload
- `loading` prop 禁用重复提交

### 3. UI 约束

- 不出现「智能体」「LLM」字样
- 左侧窄栏布局友好

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 三入口 | 三种模式可切换 |
| AC-02 | 提交 | emit submit payload |
| AC-03 | 预填 | 支持 route query 初始值 |
| AC-04 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `DiagnosisEntryPanel.vue`
- [ ] 更新 STATUS F5-02 行

## 下游消费说明

- F5-06 `diagnosis.vue` 调 submitDiagnosis
