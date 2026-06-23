# F3-04：验证输出面板 VerifyOutputPanel

## Agent 角色

系统交互 Agent — **一键验证触发与终端输出展示**。

## 唯一负责文件

```
src/components/system/VerifyOutputPanel.vue
```

## 禁止修改

- views、api 文件（通过 emit 或 inject 由父级调 API 亦可；推荐 props + events）

## 前置依赖

- F3-01 `verifyPipeline` 契约明确

## 开发要求

### 1. Props / Events

- `output` — 验证结果（步骤列表或文本行）
- `running` — 验证进行中
- `error` — 错误信息
- `@verify` — 用户点击「一键验证」，payload 含 `workers`

### 2. UI

- workers 数字输入（合理默认，与旧 `system/index.vue` 对齐）
- 「一键验证」主按钮；进行中禁用 + loading
- 输出区：等宽字体、可折叠、成功/失败步骤分色
- 失败时展示结构化错误，不白屏

### 3. 约束

- 组件内**不直接 import api**（由 `pipeline.vue` 调 `verifyPipeline` 后传 props，保持单一 API 通道在 view 层）
- 沿用旧页已验证交互，重排为面板形态

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 触发 | 点击验证 emit `verify` |
| AC-02 | workers | workers 参数可配置 |
| AC-03 | 输出 | 成功/失败输出可读 |
| AC-04 | 进行中 | running 态 UI 明确 |

## 完成定义（DoD）

- [ ] 仅修改 `VerifyOutputPanel.vue`
- [ ] 更新 STATUS F3-04 行

## 下游消费说明

- F3-05 `pipeline.vue` 串联 status 刷新 + verify 调用
