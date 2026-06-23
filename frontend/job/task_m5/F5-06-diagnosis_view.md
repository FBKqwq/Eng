# F5-06：诊断页装配 diagnosis_view

## Agent 角色

页面装配 Agent — **四区作战面板编排与提交流**。

## 唯一负责文件

```
src/views/analysis/diagnosis.vue
```

## 禁止修改

- `analysis-diagnosis/` 下各子组件（只组合）
- api 文件

## 前置依赖

- F5-01~05 全部组件就绪

## 开发要求

### 1. 布局（§3.3）

```text
[DiagnosisEntryPanel]  左窄
[ConclusionPanel]      中上
[EvidenceTimeline + ServiceTopology]  中下
[SuggestionChecklist + DiagnosisStageRing]  右窄
```

### 2. 数据流

- `@submit` → `submitDiagnosis` → 结果分发各 panel
- loading/error 全局条
- 处理 route query：`alert_id`、预填日志

### 3. 约束

- 不出现智能体调度 UI
- mock 时页级「演示数据」角标

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 四区 | 布局与 §3.3 一致 |
| AC-02 | 提交流 | 提交后各面板更新 |
| AC-03 | 降级 | 规则结果角标正确 |
| AC-04 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `diagnosis.vue`
- [ ] 更新 STATUS F5-06 行

## 下游消费说明

- 预警详情「深度诊断」跳转本页（F6）
