# M7 增强项：隐藏关系发现 + 第二阶段工具 + MCP Server — 任务编排说明

> 对应总体规划：`doc/后端开发总体规划-Services-LangGraph-MCP.md` §2.4 / §3.2 / §3.4（里程碑 **M7**）  
> 前置里程碑：**M1~M6 全部 STATUS 全绿**  
> 原则：**一个 Agent 只负责一个主脚本**，避免并行改同一文件

---

## 1. M7 目标

完成总体规划的最后一个里程碑，三条增强主线并行推进：

| 主线 | 内容 | 验收 |
| --- | --- | --- |
| **A 隐藏关系发现** | 实装 `relation_chain.discover_relations`（LLM + 降级），并在定时子图插入 `analyze_relations` 节点 | 演示「高峰后支付失败上升」类隐藏关系被发现并写入周期报告 |
| **B 第二阶段工具** | 新增 6 个增强工具（11~16），扩展 `registry` 工具表至 16 个 | 6 个新工具可独立调用并返回结构化结果 |
| **C MCP Server 形态** | 基于 FastMCP 实装 `create_mcp_server()`，新增 `run_mcp_server` 独立任务，仅暴露读类工具 | 演示「同一套工具既支撑内部 LangGraph，又能被外部 Agent 调用」 |

**M7 完成即整体规划收口。**

---

## 2. M7 范围与组件

### 2.1 主线 A：隐藏关系发现（§2.4）

| 组件 | 落点文件 | 说明 |
| --- | --- | --- |
| 关系发现 Prompt | `langchain/prompts.py` | 填充 `RELATION_PROMPT`（当前为 M7 占位文案） |
| 关系发现输出 schema | `langchain/chain_schemas.py` | 新增 `RelationChainOutput` / `RelationItem` |
| 关系发现 Chain | `langchain/relation_chain.py` | 实装 `discover_relations`（去 placeholder + 降级） |
| 定时子图接入 | `analysis/graph_scheduled.py` | `build_evidence → analyze_relations → generate_report`，并把 relations 注入报告 |

### 2.2 主线 B：第二阶段 6 个增强工具（§3.2）

| # | 工具 | 包装的 service 函数 | 落点文件 |
| --- | --- | --- | --- |
| 11 | `es_get_business_funnel` | `aggregation_service.aggregate_behavior_funnel` | `tools/elasticsearch_tools.py` |
| 12 | `es_detect_traffic_peak` | `aggregation_service.aggregate_traffic`（峰值识别封装） | `tools/elasticsearch_tools.py` |
| 13 | `es_compare_time_windows` | `aggregation_service`（双窗口对比封装） | `tools/elasticsearch_tools.py` |
| 14 | `kibana_generate_link` | 新增轻量函数（拼 Kibana Discover URL） | `tools/kibana_tools.py`（新建） |
| 15 | `report_list_recent` | `report_service.list_recent_reports` | `tools/report_tools.py` |
| 16 | `alert_list_active` | `alert_service.list_active_alerts` | `tools/alert_tools.py` |

### 2.3 主线 C：注册与 MCP Server（§3.1 / §3.4）

| 组件 | 落点文件 | 说明 |
| --- | --- | --- |
| 工具注册 + MCP 出口 | `tools/registry.py` | 工具表扩至 16；实装 `create_mcp_server()`（FastMCP，懒加载） |
| MCP 独立任务 | `tasks/run_mcp_server.py`（新建） | CLI 启动 MCP Server；仅 import registry |
| 依赖 | `requirements.txt` | 新增 `fastmcp`（registry 懒加载，缺失时结构化降级） |

**复用（不重写）**：`aggregation_service`、`report_service`、`alert_service`、`evidence_builder`、`llm_manager`、`output_parsers`、第一阶段 10 个工具。

---

## 3. 关键设计约束

1. **工具只包装 service，不重写业务**：新工具是薄适配层（参数校验 + 调用 + 结果裁剪）。
2. **读写分离**：MCP Server 仅暴露读类工具（1-5、8-10、11-16）；写类工具（6 `analysis_write_report`、7 `alert_write_event`）**不对外部 MCP 客户端开放**。
3. **入参受控**：时间窗强制必填、最大跨度受限（默认 ≤24h）；返回条数硬上限（样本 ≤50、聚合桶 ≤50）。
4. **结构化错误**：工具内部捕获 ES 异常返回 `{"ok": false, "error": ...}`，绝不抛裸异常。
5. **降级铁律**：`relation_chain` LLM 不可用时返回空 relations（`degraded=True`），`analyze_relations` 节点跳过不影响报告产出。
6. **FastMCP 懒加载**：`create_mcp_server` 内部延迟 import `fastmcp`，未安装时返回结构化错误，**保证测试无需联网/安装即可全绿**。
7. **向后兼容**：`analyze_relations` 插入定时子图后，M4/M6 既有行为与契约不变（relations 为空时报告等价于 M4）。

---

## 4. 任务清单与文件归属

| 任务编号 | 文档 | 唯一负责脚本 | 前置依赖 |
| --- | --- | --- | --- |
| M7-01 | M7-01-relation_prompt.md | `langchain/prompts.py` | M3 完成 |
| M7-02 | M7-02-relation_schema.md | `langchain/chain_schemas.py` | M3 完成 |
| M7-03 | M7-03-relation_chain.md | `langchain/relation_chain.py` | M7-01、M7-02 |
| M7-04 | M7-04-graph_scheduled.md | `analysis/graph_scheduled.py` | M7-03 |
| M7-05 | M7-05-es_tools.md | `tools/elasticsearch_tools.py` | M1 完成 |
| M7-06 | M7-06-aux_tools.md | `tools/kibana_tools.py`（新建）+ `tools/report_tools.py` + `tools/alert_tools.py` | M1 完成 |
| M7-07 | M7-07-registry_mcp.md | `tools/registry.py` + `requirements.txt` | M7-05、M7-06 |
| M7-08 | M7-08-run_mcp_server.md | `tasks/run_mcp_server.py`（新建） | M7-07 |
| M7-09 | M7-09-tests.md | `tests/test_m7_enhancements.py`（新建） | M7-04、M7-07、M7-08 |
| M7-10 | M7-10-dev_docs.md | `langchain/DEV.md` + `analysis/DEV.md` + `tools/DEV.md` | M7-04、M7-07、M7-08 |

**依赖与冲突说明**：

- `prompts.py`（M3 已建）与 `chain_schemas.py`（M3 已建）在 M7 仅做**增量追加**，由 M7-01/02 独占编辑。
- `elasticsearch_tools.py` 仅由 M7-05 编辑；`report_tools.py` / `alert_tools.py` / 新建 `kibana_tools.py` 仅由 M7-06 编辑。
- `registry.py` 与 `requirements.txt` 仅由 M7-07 编辑（新增 fastmcp 依赖）。
- `graph_scheduled.py` 仅由 M7-04 编辑；改动须向后兼容，**M7-09 须回归 M4/M6 套件**。

---

## 5. 推荐执行顺序

```text
阶段 A（可并行，4 Agent）
├── M7-01  prompts.py（RELATION_PROMPT）
├── M7-02  chain_schemas.py（RelationChainOutput）
├── M7-05  elasticsearch_tools.py（工具 11/12/13）
└── M7-06  kibana_tools.py(新建)+report_tools.py+alert_tools.py（工具 14/15/16）
阶段 B（可并行，2 Agent）
├── M7-03  relation_chain.py            依赖 M7-01、M7-02
└── M7-07  registry.py + requirements.txt  依赖 M7-05、M7-06
阶段 C（可并行，2 Agent）
├── M7-04  graph_scheduled.py（analyze_relations 节点）  依赖 M7-03
└── M7-08  tasks/run_mcp_server.py        依赖 M7-07
阶段 D（可并行，2 Agent，依赖 C）
├── M7-09  tests/test_m7_enhancements.py
└── M7-10  langchain/analysis/tools DEV
```

---

## 6. M7 总体验收（Definition of Done）

- [ ] `relation_chain.discover_relations` 产出结构化 relations，LLM 不可用时降级（空列表 + degraded）
- [ ] 定时子图 `analyze_relations` 节点跑通；relations 写入周期报告；relations 为空时报告与 M4 等价
- [ ] 6 个增强工具（11~16）可独立调用返回结构化结果，时间窗/条数受控
- [ ] `registry` 工具表为 16 个；MCP Server 仅暴露读类工具（不含 6、7）
- [ ] `create_mcp_server()` 在 fastmcp 已安装时返回 server 实例；未安装时结构化降级，不致测试失败
- [ ] `run_mcp_server.py` 可启动（仅 import registry）
- [ ] `pytest tests/test_m7_enhancements.py` 全绿；M1~M6 全量回归通过
- [ ] `langchain/DEV.md`、`analysis/DEV.md`、`tools/DEV.md` 更新
- [ ] `task_m7/STATUS.md` 全部任务 `已完成`

---

## 7. 跨任务约定

1. 只改自己负责的脚本；`registry.py`/`requirements.txt` 仅 M7-07 编辑。
2. 不改 M1~M6 已收口的核心脚本（`aggregation_service`、`report_service`、`alert_service`、`graph_main`、`graph_rule` 等），只 import 复用。
3. 工具读写分离、入参受控、结构化错误，不抛裸异常。
4. LLM/FastMCP 不可用时降级，不中断主流程，不破坏测试。
5. 中文注释与文档使用简体中文；不要 commit。
6. 进度维护见 `task_m7/STATUS.md`；派发 Prompt 见 `PROMPT_DISPATCH.md`。

---

## 8. 里程碑全景（收口）

```text
M1 数据底座 → M2 工具层(10) → M3 能力层 →（M4 定时子图 ∥ M5 规则子图）→ M6 主图收敛与前端展示 → M7 增强项（本目录）✅ 规划收口
```

M7 完成后：隐藏关系发现进入周期报告、工具层达 16 个、MCP Server 可供外部 Agent 复用，全规划闭环可演示。
