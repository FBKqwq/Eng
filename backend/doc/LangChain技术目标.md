# LangChain 技术目标

## 1. 文档定位

本文档用于明确当前项目中 LangChain 层的技术目标、职责边界、核心组件和落地需求。

当前项目最终目标不是构建一个“用户提问后回答”的聊天式诊断助手，而是构建一套主动运行的电商日志智能分析与预警系统。整体链路为：

```text
模拟电商日志
  -> Kafka
  -> Logstash
  -> Elasticsearch
  -> LangGraph 主动编排分析
  -> LangChain 负责模型调用、Prompt、结构化输出和工具封装
  -> 生成分析报告与预警
  -> 前端展示
```

在这套体系中：

```text
LangGraph 负责流程编排、状态流转、任务路由。
LangChain 负责模型调用、Prompt 管理、结构化输出、工具调用封装和模型管理。
MCP/工具层负责访问 Elasticsearch、写入报告、写入预警和检查系统状态。
```

## 2. LangChain 的核心定位

LangChain 不作为主流程引擎使用，主流程由 LangGraph 负责。

LangChain 的核心定位是：

```text
为 LangGraph 节点提供稳定、统一、可控的 LLM 调用能力。
```

它主要解决以下问题：

- 如何统一调用大模型
- 如何集中管理 API Key、模型名称和调用参数
- 如何管理不同分析场景下的 Prompt
- 如何让模型输出固定 JSON 结构
- 如何把 ES 查询、报告写入、预警写入等能力封装为工具
- 如何压缩和整理日志证据，避免把大量原始日志直接塞给模型
- 如何校验模型输出并在格式错误时重试

## 3. 与 LangGraph 的分工边界

LangGraph 和 LangChain 的关系应保持清晰：

| 层级 | 职责 |
|---|---|
| LangGraph | 决定什么时候分析、走哪条分析路径、节点如何流转 |
| LangChain | 决定如何调用模型、如何组织 Prompt、如何解析模型输出 |
| MCP/工具层 | 执行外部系统访问，例如 ES 查询、报告写入、预警去重 |

推荐调用关系：

```text
LangGraph 节点
  -> 调用 LangChain Chain
  -> Chain 从模型管理器获取 LLM
  -> Chain 使用 Prompt + 结构化输出解析器
  -> 必要时调用受控工具
  -> 返回结构化结果给 LangGraph State
```

不建议在 LangGraph 节点中直接创建模型客户端，例如直接写 `ChatOpenAI(...)`。模型初始化、API Key、模型选择和参数配置应全部交给模型管理组件。

## 4. 模型管理组件

LangChain 层必须包含一个模型管理组件，建议命名为：

```text
llm_manager.py
```

或：

```text
model_manager.py
```

### 4.1 职责

模型管理组件负责：

- 统一读取 API Key
- 统一读取模型供应商
- 统一读取模型名称
- 统一初始化 LLM 客户端
- 管理不同任务使用的模型
- 管理 temperature、timeout、max_tokens 等参数
- 封装重试策略
- 屏蔽不同模型供应商之间的差异
- 为 LangGraph 节点和 LangChain Chain 提供统一模型入口

### 4.2 配置项建议

建议在后端配置中扩展以下环境变量：

```env
LLM_PROVIDER=openai
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_DEFAULT_MODEL=gpt-4o-mini
LLM_ANALYSIS_MODEL=gpt-4o
LLM_REPORT_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=30
LLM_TEMPERATURE=0.2
```

如果后续切换到其他模型供应商，也可以保持同一套配置接口：

```env
LLM_PROVIDER=dashscope
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_DEFAULT_MODEL=qwen-plus
```

### 4.3 按任务类型选择模型

模型管理组件应支持按任务类型返回不同模型：

```python
get_llm(task="report")
get_llm(task="diagnosis")
get_llm(task="relation")
get_llm(task="alert")
```

推荐策略：

| 任务 | 模型策略 |
|---|---|
| 周期报告总结 | 使用成本较低、速度较快的模型 |
| 事件根因诊断 | 使用推理能力更强的模型 |
| 隐藏关系发现 | 使用推理能力更强的模型 |
| 预警解释 | 可使用轻量模型 |
| JSON 修复/摘要压缩 | 可使用轻量模型 |

这样可以在效果和成本之间取得平衡。

## 5. Prompt 管理需求

Prompt 不应分散写在各个节点中，应集中管理。

建议建立：

```text
prompts.py
```

或按场景拆分：

```text
prompts/
  periodic_report_prompt.py
  event_diagnosis_prompt.py
  relation_analysis_prompt.py
  alert_explanation_prompt.py
```

### 5.1 需要的 Prompt 类型

至少需要以下 Prompt：

| Prompt | 作用 |
|---|---|
| 周期报告总结 Prompt | 基于窗口统计和样本日志生成周期分析报告 |
| 事件根因分析 Prompt | 基于触发日志和上下文日志分析根因 |
| 日志关系发现 Prompt | 发现普通统计不易看出的日志关系 |
| 业务洞察总结 Prompt | 从埋点日志中总结请求高峰、热门行为、业务瓶颈 |
| 预警解释 Prompt | 生成预警原因、影响范围和处理建议 |
| 证据摘要 Prompt | 将大量日志样本压缩成可供模型分析的证据包 |

### 5.2 Prompt 应遵守的原则

- 明确模型角色：日志分析专家、智能运维分析助手、电商业务分析助手
- 明确输入内容：统计指标、样本日志、触发事件、时间窗口
- 明确输出格式：必须输出 JSON
- 要求结论必须引用证据
- 不允许编造日志中不存在的字段
- 不允许把统计计算交给模型凭空估计
- 对不确定结论输出 confidence

## 6. 结构化输出需求

当前系统需要的不是自由文本，而是前端可展示、后端可存储、后续可检索的结构化结果。

建议使用 Pydantic Schema 或 LangChain 的 structured output 能力约束输出。

### 6.1 周期报告输出结构

周期报告用于定时任务子图，示例结构：

```json
{
  "report_type": "periodic",
  "time_window": {
    "start": "2026-05-11T14:00:00",
    "end": "2026-05-11T14:15:00"
  },
  "summary": "最近 15 分钟平台请求量稳定，但支付接口响应时间升高。",
  "traffic_peak": {
    "peak_time": "14:08-14:10",
    "request_count": 2340
  },
  "top_apis": [],
  "service_health": [],
  "business_insights": [],
  "hidden_relations": [],
  "risk_level": "medium",
  "suggestions": []
}
```

### 6.2 事件诊断输出结构

事件诊断用于规则触发子图，示例结构：

```json
{
  "report_type": "event_diagnosis",
  "trigger_event_id": "log-123",
  "anomaly_type": "支付服务超时",
  "severity": "high",
  "root_cause": "payment-service 调用下游支付接口超时。",
  "affected_service": "payment-service",
  "affected_api": "/api/pay",
  "evidence_logs": [],
  "related_events": [],
  "suggestions": [],
  "confidence": 0.82
}
```

### 6.3 预警输出结构

预警用于写入 `alerts-*` 或供前端展示：

```json
{
  "alert_type": "payment_timeout",
  "severity": "high",
  "title": "支付服务疑似超时异常",
  "description": "最近 5 分钟 payment-service 出现多条 PAY_FAIL 和 timeout 日志。",
  "trigger_rule": "PAY_FAIL_WITH_TIMEOUT",
  "evidence_count": 42,
  "status": "active",
  "created_at": "2026-05-11T14:31:22"
}
```

## 7. 证据压缩与上下文构建

Elasticsearch 返回的日志可能很多，不能直接全部交给 LLM。

LangChain 层需要配合工具层完成“证据包”构造：

```text
原始日志
  -> 过滤无关字段
  -> 聚合统计
  -> 提取代表性样本
  -> 按 trace_id / service_name / error_code 分组
  -> 压缩成 Evidence Package
  -> 交给 LLM 分析
```

证据包建议包含：

- 时间窗口
- 请求总量
- 错误总量
- 错误率
- 慢接口列表
- 错误码分布
- 服务错误排名
- 关键样本日志
- 同 trace 上下文
- 同服务窗口日志摘要
- 同类错误出现频率

LLM 只负责解释和推理，不负责原始统计计算。

## 8. 工具调用封装需求

LangChain 可以把外部能力封装为 tools，但工具内部必须是受控逻辑，不应让模型自由生成 ES DSL。

推荐边界：

```text
LangGraph 节点决定要查什么
  -> 调用受控 MCP 工具
  -> MCP 工具内部生成 ES DSL
  -> 返回结构化结果
  -> LangChain/LLM 分析结果
```

这样可以避免：

- 模型生成错误 DSL
- 查询过大拖垮 ES
- 查询越权字段
- 输出格式不可控
- 分析结果无法追溯

## 9. MCP 工具需求

从 LangChain 和 LangGraph 的角度看，MCP 工具是智能分析图可以调用的外部能力接口。

第一阶段建议构建以下核心工具：

| MCP 工具 | 作用 |
|---|---|
| `es_search_logs` | 按时间、服务、级别、关键词、trace_id 查询日志 |
| `es_aggregate_metrics` | 聚合请求量、错误率、接口耗时、错误码分布 |
| `es_get_trace_context` | 根据 `trace_id` 获取完整上下文 |
| `es_get_service_window` | 查询某服务某时间窗口内的日志 |
| `es_get_similar_errors` | 查询同类 `error_code` 或相似错误 |
| `analysis_write_report` | 写入分析报告 |
| `alert_write_event` | 写入预警事件 |
| `alert_check_duplicate` | 检查是否已有相同预警，避免重复 |
| `system_health_check` | 检查 ES、Kafka、Logstash 链路状态 |
| `rule_match_log` | 判断某条日志是否命中规则触发条件 |

第二阶段可扩展：

| MCP 工具 | 作用 |
|---|---|
| `kibana_generate_link` | 为报告生成 Kibana 查询链接 |
| `es_get_business_funnel` | 统计浏览、搜索、下单、支付等行为漏斗 |
| `es_detect_traffic_peak` | 找出请求高峰时间段 |
| `es_compare_time_windows` | 比较当前窗口和上一窗口指标变化 |
| `report_list_recent` | 给前端读取历史报告 |
| `alert_list_active` | 给前端读取当前活跃预警 |

## 10. LangChain 层推荐目录结构

建议新增如下结构：

```text
backend/app/services/langchain/
  __init__.py
  llm_manager.py
  prompts.py
  output_parsers.py
  report_chain.py
  diagnosis_chain.py
  relation_chain.py
  alert_chain.py
```

各文件职责：

| 文件 | 职责 |
|---|---|
| `llm_manager.py` | 统一管理模型调用、API Key、模型参数 |
| `prompts.py` | 集中管理 Prompt 模板 |
| `output_parsers.py` | 管理结构化输出解析和校验 |
| `report_chain.py` | 周期报告生成 Chain |
| `diagnosis_chain.py` | 事件根因诊断 Chain |
| `relation_chain.py` | 隐藏日志关系分析 Chain |
| `alert_chain.py` | 预警解释和建议生成 Chain |

## 11. 与当前代码现状的关系

当前项目已有：

- `services/diagnosis/analyzer.py`
- `services/diagnosis/rule_engine.py`
- `services/elasticsearch/log_query_service.py`
- `core/config.py`

但目前：

- `analyzer.py` 只调用规则函数，未接入 LangGraph/LangChain
- `rule_engine.py` 只做 keyword 判断
- `log_query_service.py` 返回空 `items`，未真实查询 Elasticsearch
- 尚无模型管理组件
- 尚无 Prompt 管理
- 尚无结构化输出解析器
- 尚无 LangChain Chain

因此，LangChain 层的第一阶段目标是建立基础能力，而不是立刻追求复杂智能效果。

## 12. 最小可落地版本

第一版建议只做以下内容：

```text
1. 扩展 config.py，加入 LLM 配置
2. 新增 llm_manager.py，统一初始化模型
3. 新增 prompts.py，定义周期报告和事件诊断 Prompt
4. 新增 output_parsers.py，约束 JSON 输出
5. 新增 report_chain.py，用于周期分析报告生成
6. 新增 diagnosis_chain.py，用于规则触发事件诊断
7. 配合 MCP/工具层获取 ES 证据数据
```

最小运行闭环：

```text
定时触发
  -> ES 聚合与样本日志
  -> LangChain 周期报告 Chain
  -> 结构化报告
  -> 写入 analysis-results-*

规则触发
  -> ES 查询上下文日志
  -> LangChain 事件诊断 Chain
  -> 结构化诊断
  -> 写入 alerts-*
```

## 13. 最终技术目标

LangChain 在本项目中的最终技术目标是：

```text
构建一个统一、可配置、可扩展的模型调用与智能分析能力层，
为 LangGraph 的定时分析子图和规则触发子图提供 Prompt、模型、工具、结构化输出和结果校验支持。
```

它最终应支持：

- 周期性平台运行分析
- 事件级根因诊断
- 隐藏日志关系发现
- 电商埋点日志业务洞察
- 预警解释和处理建议
- 多模型管理
- API Key 统一配置
- 结构化 JSON 输出
- 工具调用和结果校验

