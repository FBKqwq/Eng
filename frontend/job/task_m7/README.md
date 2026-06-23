# F7 增强 — 前端 Agent 任务编排说明

> 对应总体规划：`location/frontend/前端开发总体规划.md` §3.4、§3.7、§8、§7（阶段 F7）
> 目标：关系洞察真实数据、双窗口对比、Kibana 深链、动效抛光、可选粒子背板。
> 原则：**一个 Agent 只负责一组互不重叠的文件**。
> Skill 参考：`/elk-frontend-agent` §9.4、§9.7 粒子白名单。

---

## 1. 阶段定位

F7 为收尾增强，依赖 F4/F6 主体已就绪：

- 报告页 `RelationInsightCard` 接 relation_chain 真实数据。
- `StatCard` 环比箭头 + 漏斗时段对比 tab。
- Kibana 链接 config + utils 生成。
- 图表动画、卡片 hover、`prefers-reduced-motion` 审计。
- 可选 `ParticleBackdrop` 白名单页（dashboard / pipeline / diagnosis）。

---

## 2. 任务清单与文件归属

| 任务编号 | 文档 | 唯一负责文件/目录 | 禁止修改 |
| --- | --- | --- | --- |
| F7-01 | [F7-01-relation_insight.md](./F7-01-relation_insight.md) | `RelationInsightCard.vue` | 其他所有文件 |
| F7-02 | [F7-02-dual_window_compare.md](./F7-02-dual_window_compare.md) | `StatCard.vue` + `funnel.vue` 时段对比 tab | 其他所有文件 |
| F7-03 | [F7-03-kibana_links.md](./F7-03-kibana_links.md) | `.env.example` + `src/utils/kibanaLinks.js`（新建） | 其他所有文件 |
| F7-04 | [F7-04-motion_polish.md](./F7-04-motion_polish.md) | `assets/styles/index.css`（动效段）+ `charts/BaseChart.vue` | 其他所有文件 |
| F7-05 | [F7-05-particle_backdrop.md](./F7-05-particle_backdrop.md) | `ParticleBackdrop.vue`（+可选 `particleEngine.js`）+ 白名单页挂载 | 其他所有文件 |
| F7-06 | [F7-06-dev_docs.md](./F7-06-dev_docs.md) | `frontend/DEV.md` | 业务代码文件 |

**说明**：F7-05 仅允许在 `/dashboard`、`/system/pipeline`、`/analysis/diagnosis` 各 **≤1 处** 挂载；达不到震撼级标准则不上线（skill §9.7）。

---

## 3. 推荐执行顺序

```text
阶段 A（可并行）
  F7-03 kibana links
  F7-04 motion polish

阶段 B
  F7-01 RelationInsightCard

阶段 C
  F7-02 双窗口对比（依赖后端 M7 或 mock 对比接口）

阶段 D（可选）
  F7-05 ParticleBackdrop + 白名单挂载

阶段 E
  F7-06 dev_docs
```

---

## 4. 跨任务约定

1. 双窗口、Kibana 深链后端未就绪时 UI **默认隐藏**，不得展示不可用按钮。
2. 粒子宁缺毋滥；`prefers-reduced-motion` 必须降级。
3. F7-04 不改业务逻辑，仅动效与样式令牌层。
4. F7-03 可更新 `ConfigSnapshotCard` 消费方，但**不修改** ConfigSnapshotCard 源码（由 F3-09 读 utils）。
5. 全部简体中文；不要 commit。

---

## 5. F7 总体验收

- [ ] 报告页关系卡有双指标对照迷你图（或接口未就绪时整块隐藏）。
- [ ] 驾驶舱 StatCard 环比箭头在后端就绪时显示；漏斗对比 tab 可用或隐藏。
- [ ] Kibana 深链工具可用；env 文档更新。
- [ ] 动效审计通过；reduce-motion 有效。
- [ ] 若启用粒子：符合 skill §9.7 验收表 P-01~P-07。
- [ ] `npm run build` 通过；DEV.md 更新。

---

## 6. 后端依赖

| 能力 | 状态 | F7 行为 |
| --- | --- | --- |
| relation_chain 报告字段 | M4/M7 | F7-01 消费 |
| es_compare_time_windows | M7 | F7-02 对比数据 |
| kibana_generate_link | M7 | F7-03 封装 |
