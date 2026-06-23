# ELK Frontend Agent Reference

Load this file only when the task needs more detailed frontend conventions.

## Backend Contract First

- Use existing project API paths and schemas as the source of truth.
- Default to `VITE_API_BASE_URL` when the existing codebase uses it.
- If an endpoint is absent, do not invent a real business loop in the frontend. Use loading, empty, error, or clearly marked mock states.
- Adapt field names in the frontend according to actual API responses.

## Page Splitting

- Keep page files in `src/views/` focused on data loading, state orchestration, and component assembly.
- Move repeated visual blocks into `src/components/`.
- Keep request functions in `src/api/`.
- Put reusable formatters, status maps, and time handling in `src/utils/`.
- Avoid one large page file that mixes API calls, formatting, and detailed markup.

## API Wrapper Style

- Prefer adding or updating the most relevant existing `src/api/*.js` file.
- Do not call `axios` or `fetch` directly from a view or component.
- Preserve existing request helper names, error handling patterns, and base URL conventions.
- Expose semantic functions such as `fetchMonitorLogs`, `runDiagnosis`, or `fetchSystemStatus` rather than raw endpoint names when that matches the codebase style.

## Expected Frontend Behavior

- Show loading, empty, and error states for backend data.
- Keep filters and request parameters explicit and easy to trace.
- Do not hide missing backend functionality behind a polished fake result.
- Prefer restrained, operational UI suitable for monitoring and repeated inspection.

## Goulingming 页面目录约定

新增业务页面统一维护在 `src/views/goulingming/` 下。

**目录结构**：

```
src/views/goulingming/
├── com/                    # 所有 goulingming 页面共享的通用组件
│   ├── FooCard.vue         # 可复用组件
│   └── BarChart.vue
├── my-page/                # 一个页面一个子目录，子目录名 = 路由路径
│   ├── index.vue          # 页面入口，组合组件
│   └── components/         # 仅本页面使用的局部组件（可选）
└── another-page/
    └── index.vue
```

**命名规范**：

- 页面子目录：`kebab-case`，与路由 path 保持一致
- 共享组件（`com/`）：`PascalCase.vue`
- 页面局部组件：放在页面子目录的 `components/` 下

**组件复用原则**：

- 优先从 `src/components/` 已有组件中复用（`common/`、`monitor/`、`analysis-*`/`system/` 等）
- `com/` 只放 `src/components/` 中没有、且被多个 goulingming 页面共享的组件
- 页面局部组件放在 `my-page/components/` 下，不提升到 `com/`

**路由与菜单注册**（新增 goulingming 页面后必须操作）：

1. 在 `src/router/index.js` 中 `import` 页面入口并注册路由
2. 在 `src/layout/menu.js` 的 `menuTree` 中添加菜单项；如需新分组，在 `menuTree` 顶层插入新分组

**API 封装**：Goulingming 页面同样必须通过 `src/api/` 下的封装函数发起请求，禁止在页面或组件中直接写 `axios`/`fetch`。

**样式与动效**：遵守 skill §9 科技感规范，参考 `src/components/common/` 已有组件的实现方式。

---

## 典型错误清单

- 把前端做成与后端脱节的演示壳
- 在浏览器代码中写 Elasticsearch、Kafka 或 Kibana 直连逻辑
- 将请求代码直接写在页面组件中
- 为小页面改动重建全局路由、布局或样式
- 在做前端任务时编辑基础设施或后端文件
- 在写入前不读取已有实现
- Goulingming 页面忘记注册路由或菜单项
- Goulingming 页面在 `com/` 中重复已有 `src/components/` 的组件
- 为单个 goulingming 页面新建组件时直接放在 `com/` 而非 `my-page/components/`

---

## 九、科技感视觉与交互规范（详细版）

> 与项目内 `.cursor/skills/elk-frontend-agent/reference.md` §九 保持同步；以该文件为完整规范源。

本节将「科技感、动态图表、高级交互、简洁 UI、主流美学」落实为**可测量、可验收**的前端规范。与 `SKILL.md` §九摘要配套。

**产品气质**：企业级可观测控制台（Grafana / Datadog / Vercel 结构参考）。禁止赛博霓虹过载、半成品粒子。允许震撼级粒子背板（白名单场景，见项目 reference §9.11）。

**图表（BaseChart 强制）**：`animation: true`；更新 `animationDurationUpdate` 300–800ms；禁止 `clear()` 硬重绘；与 `useTimeRange()` 联动；轮询过渡更新；mock 标注「演示数据」且禁止 `Math.random` 假曲线。

**动效令牌**（`index.css`）：`--motion-fast/normal/slow`、`--ease-out`、`--shadow-card-hover`、`--font-mono` 等；悬停卡片轻抬升；骨架屏 loading；`prefers-reduced-motion` 降级。

**组件清单**：StatCard 数字过渡、GaugeChart 弧段动画、StageRing 当前步高亮、TimeAxis stagger 入场、AlertDetailDrawer 滑入、PipelineGraph 验证中流动虚线、**ParticleBackdrop 震撼级粒子背板**（可选，须过 P-01~P-07 验收）。

**粒子（高门槛）**：仅 `ParticleBackdrop.vue`；2层景深+噪声场流动+令牌色+≥55fps+降级；严禁 CSS 弹球圆点、全屏遮罩、无性能分级。完整规范见项目 reference §9.11。

**智能分析**：遵守总体规划 §5（无聊天气泡、数值先于文字）；根因 fade-in 非打字机。

**验收**：时间窗变更联动刷新、至少一处数字过渡、无 ECharts 泄漏、减少动效系统设置生效。

完整表格、反例与参数见项目 `location/.cursor/skills/elk-frontend-agent/reference.md` 第九节。
