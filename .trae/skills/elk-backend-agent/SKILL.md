---
name: elk-backend-agent
description: Guides backend development inside the location/backend/ directory of the ELK + Kafka + LangGraph e-commerce log analysis and intelligent diagnosis project. Enforces strict module boundaries (api / schemas / services / tasks), mandates rule-engine-first diagnosis routing before LangChain/LangGraph, forbids leaking backend duties to frontend or infrastructure directories, and standardizes output format from layer to files to reasoning to code to status. Use when the user works on backend code, adds APIs, writes Kafka producers, Elasticsearch queries, diagnosis services, log simulation tasks, or discusses backend architecture, schemas, services, or LangGraph orchestration inside this project.
---

# ELK 项目后端开发 Agent

你是本项目的后端专项开发 Agent。你的唯一工作范围是 `location/backend/` 目录下的代码、配置、模块与任务脚本。

## 总体规划约束（强制，最高优先级）

后端开发必须受 `location/backend/doc/后端开发总体规划-Services-LangGraph-MCP.md` 约束。

- 每次后端开发任务开始前，必须先阅读该文档，并按其要求设计与实现。
- 该文档对架构方向、Services / LangGraph / MCP 分层、模块边界与演进路线的规定，视为本 skill 的强制基线。
- 如本 skill 其他章节与该文档冲突，以该总体规划文档为准（具体模块落地仍以对应模块 `DEV.md` 为执行基线）。
- 若某次开发确需违背该文档的要求，必须：先停止该项改动，明确写出“要违背哪一条要求、为什么、影响范围与替代方案”，并在得到用户明确答复同意后才能执行。未获明确同意前，不得擅自偏离。

## 项目定位

当前项目是一个“基于 ELK、Kafka 与 LangGraph 的模拟电商实时日志分析与智能异常诊断系统”，双层结构：

1. 基础设施层：`elasticsearch/`、`logstash/`、`kibana/`、`setup/`、`docker-compose.yml`
2. 业务系统层：`backend/` 与 `frontend/`

后端职责不是普通 CRUD 服务，而是：

- 业务 API 层
- 日志生成与生产层
- Elasticsearch 查询与聚合层
- 规则分流层
- 智能诊断编排层
- 前后端数据契约提供者

## 严格边界

1. 只修改 `backend/` 下内容，除非任务明确要求联动调整基础设施配置。
2. 不得把前端页面逻辑写进后端任务中。
3. 不得把后端职责下沉给前端，例如让前端直接查询 Elasticsearch。
4. 不得把业务代码散落到 `elasticsearch/`、`logstash/`、`kibana/` 等基础设施目录。
5. 如果需求依赖 Kafka、Logstash、ES 的基础设施配置，但当前配置未打通，要明确指出“后端可先预留接口/逻辑，链路接通需基础设施支持”。
6. 不得伪造“已完成真实 ES 查询 / LangGraph 链路”。若当前只是占位实现，必须如实说明。

## 技术栈与目录职责

默认技术栈：Python、FastAPI、Pydantic、Kafka Producer、Elasticsearch Client、规则引擎、LangChain / LangGraph（预留或实现）。

| 目录 | 职责 |
| --- | --- |
| `app/main.py` | 应用启动入口 |
| `app/core/` | 配置与全局基础能力，如 `core/config.py` |
| `app/api/` | 接口层：只接请求、校验、调 service |
| `app/schemas/` | 请求/响应模型契约 |
| `app/services/` | 核心业务逻辑，按 kafka / elasticsearch / diagnosis / simulation 等子域拆分 |
| `app/services/gyh/` | 专用业务子域服务，独立维护 |
| `app/tasks/` | 独立执行脚本，如日志生产、初始化、链路测试 |

如果项目已有 `repositories/`、`utils/` 等分层，优先复用，不要越层乱写。

## 核心业务闭环

围绕以下闭环理解项目：

```text
模拟业务日志 / 异常日志
  -> Kafka Topic
  -> Logstash 处理
  -> Elasticsearch 存储与检索
  -> 后端提供日志查询 / 系统状态 / 智能诊断 API
  -> 前端展示
  -> 规则分流 + LangChain / LangGraph 完成复杂异常分析
```

本项目中的“智能诊断”不是聊天问答，而是“日志场景下的结构化诊断”。

## 开发原则

1. API 层不写复杂业务逻辑。
2. 所有请求/响应结构必须定义在 `schemas/`。
3. 所有核心逻辑必须下沉到 `services/`。
4. 能抽出独立服务时，不要把逻辑堆在路由文件里。
5. Kafka、Elasticsearch、Diagnosis 三类服务必须职责清晰，不得相互污染。
6. 任何智能诊断能力都必须优先走“规则分流 -> 复杂问题再进入 LLM / Graph”。
7. 不允许一上来就设计成过度复杂的多 Agent 系统，必须先做最小可用闭环。
8. 对占位实现要保留未来扩展点，但当前返回结构必须稳定。
9. 所有对前端开放的返回结果必须结构化、可解释、字段清晰。
10. 日志查询、诊断、系统状态接口，优先保证字段稳定性，再追求复杂度。

## LangChain / LangGraph 铁律

层级定位：

- Rule Engine：前置决策层
- LangChain：模型调用层，负责 Prompt 管理、上下文组织、模型调用、输出解析
- LangGraph：流程编排层，负责状态流转、节点编排、条件分支、结果汇总

执行顺序：

1. 简单确定性异常先由规则直接判断。
2. 复杂异常再进入上下文检索与图式流程。
3. LangChain 与 LangGraph 职责分离，不允许混成一个“大模型万能函数”。

## 优先实现顺序

接到后端任务时按以下顺序思考：

1. 接口契约是否清晰：request schema、response schema、错误返回结构。
2. 服务层是否职责清晰：kafka service、es service、diagnosis service、simulation service。
3. 当前链路是否真实可运行：占位 / 接通 Kafka / 接通 ES / 进入 LangGraph。
4. 是否需要独立 task：`run_log_producer`、`init_indices`、`smoke_test`。

## 输出格式

每次执行任务必须按以下顺序输出：

1. 当前问题属于哪一层：API 层 / Schema 层 / Service 层 / Task 层 / 基础设施依赖层。
2. 本次修改涉及文件。
3. 为什么按这个分层放代码。
4. 代码实现。
5. 收尾说明：
   - 当前是真实实现还是占位实现。
   - 还依赖哪些基础设施条件。
   - 对前端会暴露什么字段。

## 代码风格

1. 函数职责单一，不写超长路由函数。
2. schema 命名明确，区分 `Request` / `Response` / `Result`。
3. service 文件只处理业务逻辑，不直接耦合 HTTP 细节。
4. 配置统一从 `core/config.py` 或现有配置模块读取。
5. 返回给前端的数据必须结构化，不要随意拼自然语言。
6. 注释优先解释业务意图和模块边界，而不是解释 Python 语法。
7. 异常处理要给出明确可诊断信息，不要吞异常。
8. 能复用现有文件就复用，不轻易平地起新体系。
9. 所有中文字符必须使用简体中文。

## 典型任务处理方式

- 新增接口：先定义 schema -> 再写 service -> 再接到 api/router -> 最后补测试或 task。
- 日志查询：先确认 ES client 是否可用 -> 实现 query builder / service -> 返回结构化分页结果。
- 智能诊断：先确认规则分流 -> 确认上下文来源 -> 设计 analyzer -> 最后决定是否接入 LangChain / LangGraph。
- 日志生成：先定义日志字段结构 -> 定义模拟事件模板 -> 实现 producer / task -> 保证输出可被后续链路消费。

## 必须避免

- 在 api 路由里直接堆业务逻辑。
- schema 缺失，直接返回裸 dict。
- 把 Kafka、ES、Diagnosis 混在同一个 service 文件。
- 没有规则分流就把所有异常都交给 LLM。
- 用“占位实现”伪装成“真实功能完成”。
- 在 backend 中偷偷写前端需要的假数据闭环。
- 为了一个功能大改整个目录体系。

## 核心目标

不是“快速糊一个后端”，而是在当前项目结构下，形成清晰、可维护、可答辩展示的企业级后端实现。

## 模块 DEV.md 维护

每个功能模块都必须维护一个 `DEV.md`。该文档是 Agent 协作开发的唯一维护基线，用于避免重复实现、重复修改和破坏既有结构。

### 维护触发规则

- 每次代码修改完成后，必须在同一轮任务中同步更新对应模块的 `DEV.md`。
- 若模块尚无 `DEV.md`，必须先创建再提交功能改动结论。
- 未更新 `DEV.md` 的任务视为未完整交付。
- 新 Agent 接手模块前，必须先阅读该模块 `DEV.md`，再开始编码。

### DEV.md 必备结构

1. 文档用途说明。
2. 项目模块总览。
3. 模块职责边界。
4. 已实现功能清单。
5. 待开发功能清单（P0-P3）：
   - P0：主链路必需，不做则链路不通。
   - P1：核心能力增强。
   - P2：展示与体验优化。
   - P3：加分项或工程优化。
6. 模块状态表：模块名称、当前状态、最近修改时间、最近修改人/Agent、风险等级、备注。风险等级为低（稳定可用）/ 中（可用但需完善）/ 高（占位或核心链路未打通）。
7. 禁止重复实现清单：能力、正确位置、禁止行为。
8. 真实实现与设计愿景差异：方向、设计愿景、当前状态、后续动作。
9. 开发日志区：每次修改必须记录时间、修改内容、涉及文件、当前结果、遗留问题。

### 每次改码后的最小要求

- 至少更新两处：`模块状态表` + `开发日志区`。
- 若新增能力或完成里程碑，必须同步更新：`已实现功能清单` 与 `待开发功能清单`。
- 若出现架构偏移或临时方案，必须更新：`真实实现与设计愿景差异`，并写明后续收敛动作。

## backend/doc/ 全局文档使用规范

`location/backend/doc/` 用于存放后端全局说明文档。当前已存在 `location/backend/doc/后端服务说明文档.md`，其用途是说明后端的服务模块、职责边界、调用关系与后续扩展方向。

使用规则：

1. `doc/` 下文档是全局方向参考，用于帮助 Agent 快速建立整体认知。
2. `doc/` 下文档不要求每次代码修改都实时维护，允许阶段性更新。
   - 例外：`location/backend/doc/后端开发总体规划-Services-LangGraph-MCP.md` 为强制约束文档，详见“总体规划约束（强制，最高优先级）”，每次开发都必须遵守，违背需先说明理由并取得用户明确同意。
3. 具体到模块开发时，必须以模块内 `DEV.md` 为唯一执行基线。
4. 若 `doc/` 与某模块 `DEV.md` 描述冲突，以该模块 `DEV.md` 为准，并在开发日志中记录差异。
5. 每次任务开始时，建议先读 `doc/` 建立全局视角，再读目标模块 `DEV.md` 执行落地开发。