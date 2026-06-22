# F1 任务进度与依赖状态（Agent 共享真相源）

> **用途**：各 Agent 开工前必读本文；任务完成后仅更新**自己负责的那一行**。
> **静态编排**：见 `README.md`、`PROMPT_DISPATCH.md`
> **任务细则**：见 `F1-xx-*.md`
> **强制基线**：`location/frontend/前端开发总体规划.md`

---

## 1. 状态枚举

| 状态 | 含义 |
| --- | --- |
| `未开始` | 尚未派发或无人认领 |
| `进行中` | Agent 已开工，代码未验收 |
| `已完成` | 本任务 AC/DoD 已通过，变更在负责分支/工作区 |
| `已合并` | 已合入团队约定的集成分支（如 `main` / `dev` / `f1`） |
| `阻塞` | 因依赖或环境问题无法继续，见「备注」 |

**下游依赖以 `已合并` 为准**；若全员单分支开发，`已完成` 可视同 `已合并`。

---

## 2. 派发前依赖检查（快速规则）

| 任务 | 可派发条件（STATUS 中依赖项） |
| --- | --- |
| F1-01 | 无 |
| F1-02 | 无 |
| F1-03 | 无 |
| F1-04 | 无 |
| F1-05 | F1-01 = `已完成`/`已合并` |
| F1-06 | F1-01 = `已完成`/`已合并` |
| F1-07 | 无 |
| F1-08 | F1-07 = `已完成`/`已合并` |
| F1-09 | F1-02、F1-03 = `已完成`/`已合并` |
| F1-10 | F1-03 = `已完成`/`已合并` |
| F1-11 | F1-08、F1-09、F1-10、F1-02 = `已完成`/`已合并` |
| F1-12 | F1-05、F1-06 = `已完成`/`已合并` |
| F1-13 | F1-04、F1-05、F1-06 = `已完成`/`已合并` |
| F1-14 | F1-05、F1-06 = `已完成`/`已合并` |
| F1-15 | F1-06 = `已完成`/`已合并` |
| F1-16 | F1-12 ~ F1-15 均为 `已完成`/`已合并` |
| F1-17 | F1-01 ~ F1-16 均为 `已完成`/`已合并` |

---

## 3. 任务状态表（动态维护）

> 负责 Agent 在「完成后」更新自己行：状态、完成时间、分支/PR、验收摘要、备注。
> **请勿修改其他任务行**，避免并行冲突。
>
> 说明：本规划为**追溯补录**——F1 骨架已在 `src/` 落地且 `npm run build` 通过（709 modules，built OK），
> 故各行初始登记为 `已完成`（占位级，对应 F1 验收「可导航 + 构建通过」）；
> 业务真实数据接入属 F2~F7，不在 F1 验收范围内。

| 任务 | 负责文件/目录 | 状态 | 负责人/Agent | 完成时间 | 分支/PR | 验收摘要 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F1-01 | `assets/styles/index.css` | 已完成 | elk-frontend-agent（追溯） | 2026-06-22 | 工作区 | 设计令牌/语义色/栅格工具类就位，构建通过 | 追溯补录 |
| F1-02 | `composables/useTimeRange.js`+`usePolling.js` | 已完成 | elk-frontend-agent（追溯） | 2026-06-22 | 工作区 | provideTimeRange/useTimeRange + usePolling 就位 | 追溯补录 |
| F1-03 | `api/*.js`（7 个） | 已完成 | elk-frontend-agent（追溯） | 2026-06-22 | 工作区 | logs/diagnosis/system 真实；metrics/reports/alerts 带 USE_MOCK=true | 待后端就绪后关 mock（F4/F6） |
| F1-04 | `utils/format.js`+`logTypeMeta.js` | 已完成 | elk-frontend-agent（追溯） | 2026-06-22 | 工作区 | format 工具 + 7 类 logTypeMeta + getLogTypeMeta | 追溯补录 |
| F1-05 | `components/common/charts/*` | 已完成 | elk-frontend-agent（追溯） | 2026-06-22 | 工作区 | BaseChart + Gauge/Trend/Bar/Pie/Funnel，仅 BaseChart import echarts | 追溯补录 |
| F1-06 | `components/common/*`（非 charts） | 已完成 | elk-frontend-agent（追溯） | 2026-06-22 | 工作区 | EmptyState/StatCard/StatusCard/SeverityBadge/LogTable/TimeAxis/StageRing | LogTable 占位，真实表格 F2 |
| F1-07 | `layout/menu.js` | 已完成 | elk-frontend-agent（追溯） | 2026-06-22 | 工作区 | menuTree 1+3 分组（7+5+3 叶子），path 对齐路由 | 追溯补录 |
| F1-08 | `SidebarTree.vue`+`SidebarTreeNode.vue` | 已完成 | elk-frontend-agent（追溯） | 2026-06-22 | 工作区 | 递归树渲染、高亮、自动展开、可折叠 | 追溯补录 |
| F1-09 | `TopBar.vue` | 已完成 | elk-frontend-agent（追溯） | 2026-06-22 | 工作区 | meta.title + 时间范围选择器 + 预警角标 30s 轮询 | 追溯补录 |
| F1-10 | `PipelineHealthDot.vue` | 已完成 | elk-frontend-agent（追溯） | 2026-06-22 | 工作区 | getSystemStatus 60s 轮询，四态着色，跳转 /system/pipeline | 追溯补录 |
| F1-11 | `layout/index.vue` | 已完成 | elk-frontend-agent（追溯） | 2026-06-22 | 工作区 | aside+main 双栏，组合树/顶栏/健康点，provideTimeRange | 追溯补录 |
| F1-12 | `views/dashboard/`+`components/dashboard/` | 已完成 | elk-frontend-agent（追溯） | 2026-06-22 | 工作区 | 5 区块编排，占位区用 EmptyState+pending-api | 真实数据 F4/F6 |
| F1-13 | `views/monitor/`(7)+`components/monitor/` | 已完成 | elk-frontend-agent（追溯） | 2026-06-22 | 工作区 | LogMonitorShell 三段式，7 子页配置驱动占位 | 真实查询 F2、图表 F4 |
| F1-14 | `views/analysis/`(5)+`components/analysis-*/` | 已完成 | elk-frontend-agent（追溯） | 2026-06-22 | 工作区 | 诊断/报告/预警/链路/漏斗占位，符合智能体耦合规范 | 真实可视化 F5/F6/F7 |
| F1-15 | `views/system/`(新3)+`components/system/` | 已完成 | elk-frontend-agent（追溯） | 2026-06-22 | 工作区 | pipeline/components/config 占位；旧 system/index.vue 保留 | 能力迁移 F3 |
| F1-16 | `router/index.js` | 已完成 | elk-frontend-agent（追溯） | 2026-06-22 | 工作区 | 16 路由 + meta.title + 5 旧路由重定向 + /temp/developer | 追溯补录 |
| F1-17 | `frontend/DEV.md` | 进行中 | — | — | — | DEV.md 仍描述旧 5 路由，需更新为新路由/目录/约束基线 | **唯一未收尾项** |

---

## 4. 当前可派发任务（编排 Agent / 人工维护）

| 可派发任务 | 原因 |
| --- | --- |
| F1-17 | F1-01~F1-16 均为 `已完成`；DEV.md 尚未与新路由/目录对齐，需收敛 |

> F1-01~F1-16 已落地（追溯补录）；F1 仅剩 **F1-17 DEV 文档收敛** 未完成。
> 收尾后即可进入 F2（监控线）/F3（系统线）并行阶段，详见总体规划 §7。

---

## 5. Agent 更新规范

### 开工时
1. 阅读第 2 节，确认依赖已满足。
2. 将本人任务行状态改为 `进行中`，填写 `负责人/Agent`。

### 完成时
1. 状态改为 `已完成`。
2. 填写 `完成时间`、`验收摘要`（如：AC-01~AC-04 通过）。
3. 若分分支开发，填写 `分支/PR`。
4. 更新第 4 节「当前可派发任务」。

### 阻塞时
1. 状态改为 `阻塞`。
2. 在 `备注` 写明：缺哪一任务、错误现象、建议动作。

---

## 6. 变更日志

| 时间 | 操作人/Agent | 说明 |
| --- | --- | --- |
| 2026-06-22 | 初始化 | 创建 F1 任务规划（README/PROMPT_DISPATCH/STATUS + F1-01~17）；据现有 `src/` 落地追溯补录 F1-01~16 为 `已完成`；F1-17 待收尾 |
