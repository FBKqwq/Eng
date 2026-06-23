# 前端 Agent 任务编排总览

> 强制基线：`location/frontend/前端开发总体规划.md` §7（F1~F7）
> 执行 skill：`/elk-frontend-agent`
> 边界：仅 `location/frontend/`，不修改 backend / docker / ES / Logstash / Kibana / setup

---

## 1. 里程碑与目录映射

| 阶段 | 目录 | 主题 | 依赖后端里程碑 | 前置前端阶段 |
| --- | --- | --- | --- | --- |
| F1 | [task_m1](./task_m1/README.md) | 骨架重构：树状目录 + 布局 + 路由 + 通用件 + 占位 | 无 | — |
| F2 | [task_m2](./task_m2/README.md) | 监控线：日志明细查询 + 动态筛选 + 7 子页 | logs/search（已有）；fields 可兜底 | F1 |
| F3 | [task_m3](./task_m3/README.md) | 系统线：链路验证 + 状态卡矩阵 + 配置快照 | system 接口（已有） | F1 |
| F4 | [task_m4](./task_m4/README.md) | 图表线：驾驶舱 + 监控图表带 + 漏斗 | 后端 M1（`POST /logs/aggregate`） | F1；与 F2/F3 并行 |
| F5 | [task_m5](./task_m5/README.md) | 智能线：诊断中心 + 链路追踪 | 后端 M5（规则子图，可先 mock） | F1、F2（trace 跳转） |
| F6 | [task_m6](./task_m6/README.md) | 结果线：体检报告 + 预警中心 + 角标 | 后端 M4/M5（reports/alerts 已就绪） | F1、F4（驾驶舱区块） |
| F7 | [task_m7](./task_m7/README.md) | 增强：关系洞察 + 双窗口对比 + Kibana 链接 | 后端 M7 | F4、F6 |

---

## 2. 推荐全局执行顺序

```text
F1（收尾 F1-17 DEV + F1-18 API 契约回补）
  ↓
F2 ∥ F3（可并行，改不同目录）
  ↓
F4（依赖后端 M1 聚合接口就绪；可与 F2/F3 尾期重叠准备）
  ↓
F5 ∥ F6（可并行）
  ↓
F7
```

**关键路径**：F1 → F2 → F4 → F6 → F7（日历最短路径若全力并行 F2/F3 与 F5/F6 可缩短）。

---

## 3. 各里程碑文档结构（统一规范）

每个 `task_mN/` 目录包含：

| 文件 | 用途 |
| --- | --- |
| `README.md` | 阶段定位、任务清单、文件归属、执行顺序、总体验收 |
| `STATUS.md` | 动态进度真相源（Agent 只改自己那一行） |
| `PROMPT_DISPATCH.md` | 编排 Prompt + 各任务可复制派发 Prompt |
| `FN-xx-*.md` | 单任务细则（AC/DoD/文件边界） |

---

## 4. 跨里程碑硬约束（所有 Agent）

1. 一个 Agent **只改一组互不重叠**的文件/目录。
2. **API 契约优先**：动手前必读 [`API_CONTRACT.md`](./API_CONTRACT.md) 与 `backend/app/api/DEV.md` §4.2；`request.js` 已解包信封，页面读 `res.data` 即业务负载，错误用 `catch (e.error?.code)`。
3. 页面与组件不得直接 `axios`/`fetch`，统一 `src/api/*.js`。
3. 不得浏览器直连 ES / Kafka / Kibana API。
4. ECharts 实例只允许在 `components/common/charts/`。
5. 智能体产出遵守总体规划 §5：禁止独立调度页、禁止对话框、数值先于文字、`StageRing` 唯一进度载体。
6. 待后端接口用 `USE_MOCK` + 页内「演示数据」角标，禁止冒充真实数据。
7. 简体中文；除非负责人明确要求，**不要 commit**。

---

## 5. 各阶段任务规模

| 阶段 | 目录 | 任务数 | 编号范围 |
| --- | --- | ---: | --- |
| F1 骨架重构 | task_m1 | 18 | F1-01 ~ F1-18 |
| F2 监控线 | task_m2 | 8 | F2-01 ~ F2-08 |
| F3 系统线 | task_m3 | 10 | F3-01 ~ F3-10 |
| F4 图表线 | task_m4 | 9 | F4-01 ~ F4-09 |
| F5 智能线 | task_m5 | 9 | F5-01 ~ F5-09 |
| F6 结果线 | task_m6 | 8 | F6-01 ~ F6-08 |
| F7 增强 | task_m7 | 6 | F7-01 ~ F7-06 |
| **合计** | | **68** | |

---

## 6. 当前整体进度（人工维护摘要）

| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| F1 | 收尾中 | F1-01~16 已落地；**F1-17 DEV** + **F1-18 API 契约回补（代码未落地，阻塞 F2~F6）** |
| F2~F7 | 未开始 | 任务文档已与 `API_CONTRACT` 对齐；见各 `STATUS.md` |

详细任务行级状态以各里程碑 `STATUS.md` 为准。

**API 专项文档**：[API_CONTRACT.md](./API_CONTRACT.md) | [API_AUDIT.md](./API_AUDIT.md)
