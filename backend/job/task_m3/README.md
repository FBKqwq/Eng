# M3 LangChain 能力层 — 任务编排说明

> 对应总体规划：`doc/后端开发总体规划-Services-LangGraph-MCP.md` §2.6 / §2.7 / §2.8（里程碑 **M3**）  
> 前置里程碑：**M1 数据底座**（`task_m1/STATUS.md` 全绿）+ **M2 工具层**（`task_m2/STATUS.md` 全绿）  
> 原则：**一个 Agent 只负责一个主脚本**，避免并行改同一文件

---

## 1. M3 目标

将 `app/services/langchain/` 从占位升级为可用的 **LangChain 能力层**：4 个 P0 基础组件 + 2 个核心 Chain。

| 项 | 说明 |
| --- | --- |
| **里程碑验收** | 给定 **mock 证据包**，`report_chain` 与 `diagnosis_chain` 能产出**符合 Pydantic schema 的结构化报告**；LLM 不可用时自动降级为纯统计/模板报告且不报错 |
| **不在 M3** | LangGraph 图（`graph_*`、scheduler、trigger_scanner）→ **M4/M5/M6**；`relation_chain` 隐藏关系发现 → **M7**；report/alert 持久化落地 → **M4/M5** |
| **降级铁律** | 任一 LLM 调用失败不得抛裸异常；`report_chain` 退化为模板拼接，`diagnosis_chain` 退化为规则结论 |

---

## 2. M3 范围与组件

| 组件 | 落点文件 | 优先级 | 是否用 LLM |
| --- | --- | --- | --- |
| LLM Manager | `langchain/llm_manager.py` | P0 | — |
| Prompt 管理 | `langchain/prompts.py` | P0 | — |
| Output Parser | `langchain/output_parsers.py` | P0 | 可选（JSON 修复） |
| Evidence Builder | `langchain/evidence_builder.py` | P0 | 否（纯代码压缩） |
| Chain I/O 模型 | `langchain/chain_schemas.py`（新建） | P0 | — |
| 周期报告 Chain | `langchain/report_chain.py` | P0 | 是（可降级） |
| 根因诊断 Chain | `langchain/diagnosis_chain.py` | P0 | 是（可降级） |

**不动**：`relation_chain.py`（M7）、`alert_chain.py`（M5/M6）保持占位。

---

## 3. 任务清单与文件归属

| 任务编号 | 文档 | 唯一负责脚本 | 前置依赖 |
| --- | --- | --- | --- |
| M3-01 | M3-01-llm_manager.md | `app/services/langchain/llm_manager.py` + `requirements.txt` | M2 完成 |
| M3-02 | M3-02-prompts.md | `app/services/langchain/prompts.py` | M2 完成 |
| M3-03 | M3-03-output_parsers.md | `app/services/langchain/output_parsers.py` | M2 完成 |
| M3-04 | M3-04-evidence_builder.md | `app/services/langchain/evidence_builder.py` | M2 完成 |
| M3-05 | M3-05-chain_schemas.md | `app/services/langchain/chain_schemas.py`（新建） | M2 完成 |
| M3-06 | M3-06-report_chain.md | `app/services/langchain/report_chain.py` | M3-01~05 |
| M3-07 | M3-07-diagnosis_chain.md | `app/services/langchain/diagnosis_chain.py` | M3-01~05 |
| M3-08 | M3-08-test_langchain.md | `tests/test_m3_langchain.py`（新建） | M3-06、M3-07 |
| M3-09 | M3-09-langchain_dev.md | `app/services/langchain/DEV.md` | M3-06、M3-07 |

**依赖说明**：

- M3-01 需新增依赖：`langchain-openai`（或兼容供应商客户端），由 **M3-01 Agent** 写入 `requirements.txt`。
- `core/config.py` 的 LLM 配置项已在框架阶段就绪（`llm_provider`/`llm_api_key`/`llm_default_model` 等），M3 **不改 config**，直接读取。
- 链层（M3-06/07）通过 `llm_manager.invoke_structured` + `output_parsers` 产出 `chain_schemas` 模型，不直接 import 具体 LLM SDK。

---

## 4. 推荐执行顺序

```text
阶段 A（可并行，最多 5 Agent）
├── M3-01  llm_manager.py（+ requirements）
├── M3-02  prompts.py
├── M3-03  output_parsers.py
├── M3-04  evidence_builder.py
└── M3-05  chain_schemas.py

阶段 B（可并行，2 Agent；依赖 A 全部）
├── M3-06  report_chain.py
└── M3-07  diagnosis_chain.py

阶段 C（可并行，2 Agent；依赖 B）
├── M3-08  tests/test_m3_langchain.py
└── M3-09  langchain/DEV.md
```

---

## 5. M3 总体验收（Definition of Done）

- [ ] 7 个 langchain 文件去除相关 `placeholder: true`，返回结构化结果
- [ ] `is_llm_available()` 在无 API Key 时返回 `False`，链层据此降级
- [ ] mock 证据包 → `report_chain.generate_periodic_report` 返回符合 `chain_schemas` 的 dict
- [ ] mock 证据包 → `diagnosis_chain.infer_root_cause` / `generate_event_report` 返回符合 schema 的 dict
- [ ] `evidence_builder.build_evidence_package` 控制日志条数 ≤ `max_logs`，输出含分组/采样
- [ ] `pytest tests/test_m3_langchain.py` 全绿（不依赖真实 LLM/ES，全 mock）
- [ ] `langchain/DEV.md` 状态表与开发日志更新
- [ ] `task_m3/STATUS.md` 全部任务 `已完成`

---

## 6. 跨任务约定

1. 只改自己负责的脚本（M3-01 可改 `requirements.txt`）。
2. 不改 `core/config.py`、不改 `analysis/*`、不改 `tools/*`、不改其他 langchain 文件。
3. LLM 调用统一走 `llm_manager`，链层禁止直接 import `langchain_openai`。
4. 任一 LLM 失败必须捕获并降级，不抛裸异常。
5. 进入 LLM 的内容必须经 `evidence_builder` 压缩，控制 token。
6. 中文注释与文档使用简体中文；不要 commit。
7. 进度维护见 `task_m3/STATUS.md`；派发 Prompt 见 `PROMPT_DISPATCH.md`。

---

## 7. 与后续里程碑关系

```text
M1 数据底座 → M2 工具层 → M3 LangChain 能力层（本目录）
                              ↘
                               M4 定时子图（report_chain + evidence_builder）
                               M5 规则子图（diagnosis_chain + evidence_builder）
                               M6 主图收敛 / M7 relation_chain + MCP Server
```

M3 完成后，M4 的 `generate_report` 节点与 M5 的 `infer_root_cause` 节点可直接调用本层 Chain，无需自行管理 LLM。

---

## 8. 已知遗留（不阻塞 M3）

| 项 | 现状 | 何时收敛 |
| --- | --- | --- |
| `relation_chain.py` | 占位（隐藏关系发现） | M7 |
| `alert_chain.py` | 占位（预警文案解释） | M5/M6 |
| `report_service` / `alert_service` 落地 | 占位 | M4 / M5 |
| `analysis/*` 图与调度 | 占位 | M4/M5/M6 |
| 真实 LLM 联调 | 需配置 `LLM_API_KEY` | 集成环境 |
