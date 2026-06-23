# F3-01：system API 扩展 system_api

## Agent 角色

API 封装专项 Agent — **完善 system.js 状态与链路验证契约**，不修改页面。

## 唯一负责文件

```
src/api/system.js
```

## 禁止修改

- `views/`、`components/`、`composables/`、其他 `api/*.js`

## 前置依赖

- F1-03 已完成（request.js + system.js 骨架）
- 必读：总体规划 §6、`backend` 中 system 相关路由契约

## 开发要求

### 1. `getSystemStatus()`

- `GET /system/status`
- 解包后 `res.data` 含：`kafka{available,...}`、`elasticsearch{available,cluster_status,...}`、`docker{available}`、`containers{...}`、`services{...}` 及配置快照字段
- **禁止**依赖顶层 `available` / `placeholder`（已废弃）
- 失败：`catch (e) { e.error?.code }`

### 2. `verifyPipeline(payload)`

- `POST /system/pipeline/verify`
- payload 支持 `workers`（默认与旧页一致）
- 返回验证步骤输出（结构化数组或终端文本，对齐后端实际响应）

### 3. `getHealth()`

- `GET /health`（若 F1 已有则保留签名）
- 轻量探活，供组件页可选展示

### 4. 约束

- 不写渲染逻辑；system 接口为真实接口，**不引入 USE_MOCK**
- 简体中文注释；导出函数命名与 F1 保持一致

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | status | `getSystemStatus` 返回可解析结构 |
| AC-02 | verify | `verifyPipeline` 支持 workers 参数 |
| AC-03 | 兼容 | 不破坏 F1 `PipelineHealthDot` 已有调用 |
| AC-04 | 构建 | `npm run build` 通过 |

## 完成定义（DoD）

- [ ] 仅修改 `src/api/system.js`
- [ ] 更新 `task_m3/STATUS.md` F3-01 行

## 下游消费说明

- F3-02 `systemStatus.js` 归一化 status 响应
- F3-04 `VerifyOutputPanel` 调用 `verifyPipeline`
- F3-07/F3-08 读取 status 配置字段
