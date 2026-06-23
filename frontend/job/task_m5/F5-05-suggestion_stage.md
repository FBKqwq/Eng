# F5-05：建议清单与阶段环 suggestion_stage

## Agent 角色

诊断交互 Agent — **可勾选建议清单 + node_trace 阶段环包装**。

## 唯一负责文件

```
src/components/analysis-diagnosis/SuggestionChecklist.vue
src/components/analysis-diagnosis/DiagnosisStageRing.vue
```

## 禁止修改

- `components/common/StageRing.vue`（只 import 组合）
- api、views

## 前置依赖

- F1-06 `StageRing`
- F5-01 `node_trace` 字段形态

## 开发要求

### 1. SuggestionChecklist

- `suggestions` 列表 → 可勾选核对清单
- 勾选仅前端状态（演示处置流程）
- 版式化列表，非对话

### 2. DiagnosisStageRing

- **数据来源**（API 契约）：`POST /diagnosis` 响应**不含** `node_trace`；阶段环数据来自：
  - `POST /analysis/run` 返回的 `data.node_trace`（完整轨迹），或
  - `GET /reports/{id}` 的 `data.report.node_trace`（报告详情）
- 薄包装：将上述 `node_trace` 映射为 StageRing stages
- 业务语义阶段名：取上下文 → 关联分析 → 根因推断 → 定级 → 成文
- **禁止**展示节点函数名、工具名、模型名
- LLM 跳过阶段标记为「已跳过」/灰色
- 每阶段显示耗时与状态（成功/降级/跳过）

### 3. Props

- 两组件均 props 驱动：`suggestions`、`nodeTrace`、`degraded`

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 清单 | 建议可勾选 |
| AC-02 | 阶段环 | node_trace 翻译为业务阶段 |
| AC-03 | 降级 | LLM 阶段显示跳过 |
| AC-04 | 不越界 | 未改 StageRing.vue |

## 完成定义（DoD）

- [ ] 仅修改上述两个 vue 文件
- [ ] 更新 STATUS F5-05 行

## 下游消费说明

- F5-06 右侧窄栏
