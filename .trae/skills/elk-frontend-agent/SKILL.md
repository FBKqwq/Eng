---
name: elk-frontend-agent
description: Frontend development agent for the ELK + Kafka + LangGraph e-commerce log analysis and intelligent diagnosis project. Use when working on location/frontend Vue 3 + Vite code; routes, components, layout, styling, API wrappers, log monitoring, diagnosis, analysis results, system status, or tech-forward dashboard UI with dynamic charts and polished interactions. Must stay inside location/frontend.
---

# ELK Frontend Agent

Use this skill for frontend work in the ELK + Kafka + LangGraph e-commerce log analysis and intelligent diagnosis project.

## 总体规划约束（强制，最高优先级）

前端开发必须受 `location/frontend/前端开发总体规划.md` 约束。

- 每次前端开发任务开始前，必须先阅读该文档，并按其要求设计与实现。
- 该文档对页面规划、目录结构、组件与 API 封装、交互与展示约定的规定，视为本 skill 的强制基线。
- 如本 skill 其他章节与该文档冲突，以该总体规划文档为准。
- 若某次开发确需违背该文档的要求，必须：先停止该项改动，明确写出“要违背哪一条要求、为什么、影响范围与替代方案”，并在得到用户明确答复同意后才能执行。未获明确同意前，不得擅自偏离。

## Hard Boundaries

- Modify only `location/frontend/`.
- Do not modify `location/backend/`, `location/docker-compose.yml`, `location/elasticsearch/`, `location/logstash/`, `location/kibana/`, or `location/setup/`.
- Do not add direct Elasticsearch, Kafka, or Kibana access from frontend code.
- Route all data through backend APIs. Do not query Elasticsearch directly from the browser.
- Prefer the smallest necessary change. Do not introduce broad rewrites, major UI frameworks, or large state-management changes for narrow requests.
- If the backend API is missing, reserve the frontend call site, empty state, loading state, error state, or mock placeholder; clearly say the real behavior depends on backend support.

## Project Scope

Frontend scope is the system display layer: monitoring, diagnosis interaction, analysis results, and system status inspection. It is not a generic admin platform.

Default stack: Vue 3 + Vite + JavaScript.

Respect the existing directory contract:

- `src/api/`: request wrappers only; pages must not write raw `axios` or `fetch`.
- `src/views/`: page-level composition.
- `src/views/gongyiheng/`: dedicated directory for new pages and components.
- `src/views/gongyiheng/com/`: components specific to gongyiheng pages, can reuse existing components from `src/components/`.
- `src/components/`: reusable UI and detailed presentation.
- `src/layout/`: layout components.
- `src/router/`: route definitions.
- `src/utils/`: formatting, status, time, and shared helpers.
- `src/assets/`: images, icons, and style assets.

The fixed business pages are `home`, `monitor`, `diagnosis`, `results`, `system`, and `gongyiheng`.

## Required Workflow

1. Read before writing. Read the target view, related components, corresponding API file, and relevant router/layout files before editing.
2. Locate the smallest edit surface:
   - New page: inspect router, then layout reuse, then create view/components, then add API wrapper.
   - Interaction change: update existing components first.
   - API integration: write or update `src/api/*.js`, call it from the view, and handle loading, empty, and error states.
3. State the data contract before implementing: source API, displayed fields, and which fields are placeholders versus real backend data.
4. Keep responsibilities layered: view composes, component renders details, API module requests data, utils format values.
5. Verify with the repo's available frontend checks when practical, such as lint, build, or a browser smoke test.

## Response Format

For every frontend task using this skill, answer in this order:

1. **本次修改目标**：one sentence.
2. **涉及文件**：list files read, added, or modified.
3. **为什么这样改，而不是重构**：explain the minimal-change choice.
4. **代码**：summarize the actual code changes; include key snippets only when helpful.
5. **可能依赖的后端接口前提**：list required methods, paths, and key fields.
6. **当前未完成边界**：identify mocks, reserved integration points, or missing backend support.

## Page Requirements

When adding or materially changing these pages, cover the minimum sections below. If APIs are absent, implement empty/mock placeholders and mark them as pending backend integration.

- `diagnosis`: input conditions, diagnosis result, evidence logs, handling suggestions, status and confidence.
- `monitor`: search conditions, log list, key fields, time range filter, level filter, source filter.
- `system`: Kafka configuration snapshot, Elasticsearch configuration snapshot, API health status, Kibana entry if the project already supports it.

## Extra Reference

Read [reference.md](reference.md) when a task needs:

- More detailed page splitting, API-wrapper style, naming rules, or anti-patterns.
- **科技感 UI、动态图表、高级交互视效的完整规范**（reference §九）。

---

## 九、科技感 UI 与动态视觉（强制审美基线）

在满足总体规划与硬边界的前提下，所有前端页面与图表须符合「**简洁 + 科技感 + 数据动态感**」的产品气质。数值、动效参数、组件级清单见 [reference.md §九](reference.md#九科技感视觉与交互规范详细版)。

### 9.1 总体原则

1. **信息优先**：科技感服务于可读性与态势感知，禁止为炫技牺牲数据清晰度。
2. **动态优先**：凡有时间序列、计数、状态、进度的区块，默认具备**数据变更时的平滑过渡**；能轮询/联动的不得做成静态截图式展示。
3. **交互克制**：动效短、缓动自然、有明确反馈；单屏同时强动效元素不超过 3 处。
4. **审美对齐**：参考 Grafana / Datadog / Vercel Dashboard——深色导航 + 浅色内容、低饱和背景、高对比关键数字、语义色一致。

### 9.2 视觉语言（必须遵守）

| 维度 | 要求 |
| --- | --- |
| 色彩 | 以 `assets/styles/index.css` 设计令牌为准；主色科技蓝系；语义色仅用于状态 |
| 卡片 | 白底/浅灰底 + 细边框 + 轻阴影；可选顶部 accent 线 |
| 数字 | `tabular-nums`；大数字加粗，标签次级色 |
| 密度 | 8px 栅格；留白充足 |
| 装饰 | 允许震撼级粒子背板（见下 §9.7）；禁止霓虹过载、半成品粒子 |

### 9.3 图表动态更新（必须遵守）

1. 统一经 `components/common/charts/`；`animation: true`；刷新用 `setOption` + `animationDurationUpdate`（300–800ms）。
2. 与 `useTimeRange()` 联动；变更时重查并重绘，带 loading。
3. 轮询区块（预警、链路健康等）过渡更新，禁止整页闪烁。
4. mock 仍走动态渲染路径并标注「演示数据」；禁止浏览器端伪造聚合曲线。

### 9.4 交互与动效（必须遵守）

悬停卡片轻抬升 150–200ms；加载优先骨架屏；抽屉/展开 300ms ease-out；关键异常态轻微脉冲（≤2s）；尊重 `prefers-reduced-motion`。

### 9.5 页面级最低动态要求

驾驶舱：仪表/指标/趋势联动时间窗；监控：筛选与图表带同步刷新；智能分析：仪表与阶段环随进度更新（禁止对话框动效）；系统：链路节点状态色过渡。

### 9.6 与总体规划的关系

不替代总体规划 §5（禁止聊天气泡、数值先于文字、StageRing 唯一进度载体）。硬边界与总体规划优先。

### 9.7 粒子特效（震撼级，可选用）

允许适当引入粒子，须达产品级震撼标准；**严禁半成品**。统一 `ParticleBackdrop.vue`；每页≤1处；白名单：驾驶舱英雄区/链路背板/诊断结论背板；桌面≥55fps；`reduce-motion` 静态高品质降级。细则见项目 reference §9.11。

### 9.8 任务交付审美自检

- [ ] 数据更新有平滑过渡
- [ ] 时间窗/筛选变更后相关区块同步刷新
- [ ] 语义色与排版符合规范
- [ ] 无过度动效
- [ ] `prefers-reduced-motion` 已考虑
- [ ] 若使用粒子：符合震撼级标准（reference §9.11 验收表 P-01~P-07）