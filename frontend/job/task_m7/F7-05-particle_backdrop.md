# F7-05：粒子背板 particle_backdrop（可选）

## Agent 角色

氛围视觉 Agent — **震撼级 ParticleBackdrop + 白名单页挂载**。

## 唯一负责文件

```
src/components/common/ParticleBackdrop.vue
src/components/common/particleEngine.js（可选）
src/views/dashboard/index.vue（仅增加背板挂载）
src/views/system/pipeline.vue（仅增加背板挂载）
src/views/analysis/diagnosis.vue（仅增加背板挂载）
```

## 禁止修改

- 白名单页**以外**的所有文件
- 每页仅 **1 处** 背板区域

## 前置依赖

- skill §9.7、reference §9.11
- F4-07、F3-05、F5-06 白名单页已存在

## 开发要求

### 1. ParticleBackdrop.vue

- Props：`variant`（dashboard/pipeline/diagnosis）、`intensity`（0~1）、`accentColor`
- `pointer-events: none`；`z-index: 0`；父级 `position: relative`
- ≥2 层景深、有机流动、令牌配色
- `document.hidden` 暂停 rAF；`onUnmounted` 释放
- `prefers-reduced-motion` → 静态高品质渐变网格

### 2. 白名单挂载（任选其实装，可只做 1~2 页）

| 页面 | 区域 |
| --- | --- |
| `/dashboard` | HealthOverview 英雄区背板 280–360px |
| `/system/pipeline` | PipelineGraph 背板；验证时 intensity 0.4→0.7 |
| `/analysis/diagnosis` | ConclusionPanel 后方背板；critical 仅 accent 微调 ≤15% |

### 3. 一票否决

- 达不到 P-01~P-07 **禁止合并**；改用静态渐变

### 4. 性能

- 桌面 ≥55fps；粒子数分级；单页实例 ≤1

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| P-01 | 场景 | 仅白名单且每页≤1 |
| P-02 | 图层 | 不挡交互 |
| P-03 | 视觉 | 景深+有机流+令牌色 |
| P-04 | 性能 | ≥55fps；隐藏暂停 |
| P-05 | 降级 | reduce-motion 备选 |
| P-06 | 生命周期 | 无泄漏 |
| P-07 | 非半成品 | §9.11.4 无否决项 |

## 完成定义（DoD）

- [ ] ParticleBackdrop 达标或明确跳过并备注
- [ ] 更新 STATUS F7-05 行

## 下游消费说明

- 产品级氛围增强；可整任务跳过
