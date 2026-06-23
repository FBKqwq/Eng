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
| F1-18 | F1-03 = `已完成`/`已合并`（可与 F1-17 并行，但改 api 文件） |

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
| F1-01 | `assets/styles/index.css` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04 通过：令牌齐全、语义色四色、栅格工具类、build OK | F1-01 设计令牌复审 |
| F1-02 | `composables/useTimeRange.js`+`usePolling.js` | 已完成 | elk-frontend-agent（追溯） | 2026-06-22 | 工作区 | provideTimeRange/useTimeRange + usePolling 就位 | 追溯补录 |
| F1-03 | `api/*.js`（7 个） | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04 通过：信封解包、logs/diagnosis/system 真实路径、metrics/reports/alerts USE_MOCK 契约形态、build 通过 | 已由 F1-18 契约复审 |
| F1-04 | `utils/format.js`+`logTypeMeta.js` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04：formatTime/Bytes/Percent/Duration 边界安全；7 类 logTypeMeta + getLogTypeMeta + §3.2 默认列对齐 | F1-13 可依赖 |
| F1-05 | `components/common/charts/*` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-05 通过：BaseChart resize/dispose/动效；5 图表 data→option 组装；仅 BaseChart import echarts；build OK | F1-05 charts 实现 |
| F1-06 | `components/common/*`（非 charts） | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04 通过：EmptyState 四 props、SeverityBadge 语义色令牌、LogTable 占位、7 组件 build OK | LogTable 占位，真实表格 F2 |
| F1-07 | `layout/menu.js` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-03 通过：1 一级叶子 + 3 分组（7+5+3 叶子），16 path 与 README §2.1 / router 一致，纯声明数据 | F1-08 可依赖 |
| F1-08 | `SidebarTree.vue`+`SidebarTreeNode.vue` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04 通过：menuTree 两级递归渲染、叶子高亮、父分组路由自动展开、分组可折叠；build OK | F1-11 可依赖 |
| F1-09 | `TopBar.vue` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04 通过：meta.title 标题、useTimeRange 预设联动、getActiveAlerts 30s usePolling 角标跳转 /analysis/alerts、失败归 0 不抛错 | F1-11 可依赖 |
| F1-10 | `PipelineHealthDot.vue` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04 通过：getSystemStatus 60s usePolling、嵌套字段四态映射、点击跳 /system/pipeline、失败灰态不抛错；build OK | F1-11 可依赖 |
| F1-11 | `layout/index.vue` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04 通过：aside+content 双栏、品牌/树/健康点/TopBar/router-view 组合挂载、provideTimeRange、导航区可滚动、build OK | F1-16 可依赖 |
| F1-12 | `views/dashboard/`+`components/dashboard/` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-03 通过：5 区块 §3.1 编排；EmptyState+pending-api；图表空 TrendChart 占位；build OK | 真实数据 F4/F6 |
| F1-13 | `views/monitor/`(7)+`components/monitor/` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-03 通过：LogMonitorShell 三段式骨架、7 子页 getLogTypeMeta 配置驱动、筛选/图表 EmptyState+pending 标注、build OK | 真实查询 F2、图表 F4 |
| F1-14 | `views/analysis/`(5)+`components/analysis-*/` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-03 通过：5 页 §3.3~§3.7 分区编排；Gauge/StageRing/EmptyState 占位；无对话框形态；build OK | 真实可视化 F5/F6/F7 |
| F1-15 | `views/system/`(新3)+`components/system/` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-03 通过：§3.8 编排 pipeline/components/config 占位；四节点链路图/验证面板/6 状态卡/配置快照；旧 index.vue 保留；build OK | 能力迁移 F3 |
| F1-16 | `router/index.js` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-05 通过：16 子路由+meta.title 与 menu.js 一致、5 条旧路由重定向、/temp/developer 可达、build OK（735 modules） | F1-17 可依赖 |
| F1-17 | `frontend/DEV.md` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-04 通过：新 16 路由表、目录职责、F1 状态表、约束与开发日志已收敛 | F1 文档收尾完成 |
| F1-18 | `api/*`+`analysis.js` | 已完成 | elk-frontend-agent | 2026-06-23 | 工作区 | AC-01~AC-06 通过：信封解包验收、logs aggregate/searchByTraceId、metrics 六模板→aggregateLogs、mock items+total/buckets、analysis.js 两函数、build OK（735 modules） | F1 契约收口完成 |

---

## 4. 当前可派发任务（编排 Agent / 人工维护）

| 可派发任务 | 原因 |
| --- | --- |
| F2-01 / F2-02 / F3-01 等 | F1-18 已完成；可并行进入 F2/F3 真实对接 |

> **F1 里程碑收尾（2026-06-23）**：F1-01~F1-18 已全部落地——骨架、布局、16 路由、通用件、图表封装、API wrapper（含 analysis.js）与页面占位均已验收；`npm run build` 通过。
> 下一步进入 F2/F3 并行真实对接，详见总体规划 §7。

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
| 2026-06-23 | API 契约审计 | 新增 API_CONTRACT/API_AUDIT、F1-18；修订 F1~F7 api 相关任务文档 |
| 2026-06-23 | F1-17 DEV 文档收敛 | `frontend/DEV.md` 路由/目录/状态表与 F1 落地对齐；F1 里程碑文档收尾 |
