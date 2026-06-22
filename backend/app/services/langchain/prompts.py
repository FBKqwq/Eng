"""集中 Prompt 模板。

职责：周期报告 / 根因诊断 / 关系发现 / 预警解释 / 证据摘要五类 Prompt。
规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §2.6
状态：M3-02 已实现 report/diagnosis/evidence_summary/alert 模板；relation 待 M7。
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 周期报告（对齐 chain_schemas.ReportChainOutput）
# ---------------------------------------------------------------------------
REPORT_PROMPT = """你是一名电商日志智能运维分析专家，负责根据证据包生成周期性系统健康分析报告。

## 输入
以下 JSON 为已压缩的证据包（含 summary、grouped、samples、metrics），统计指标已由系统计算完成，请直接引用，勿凭空估算：
{evidence_package}

## 任务
1. 综合 summary 与 metrics 判断整体风险等级（risk_level）。
2. 从 samples 与 grouped 提炼关键发现（key_findings），每条须可追溯到证据。
3. 给出可执行的运维建议（recommendations）。

## 输出要求
**仅输出一个 JSON 对象，不要 Markdown 代码块，不要任何额外解释。**

字段说明（字段名必须完全一致）：
- report_type: 固定为 "periodic"
- title: 报告标题（简体中文，简明扼要）
- risk_level: 风险等级，取 "low" | "medium" | "high" 之一
- summary: 一段话总结本周期系统状态与主要风险
- key_findings: 字符串数组，每条为一个关键发现
- recommendations: 字符串数组，每条为一条处置或优化建议

示例结构：
{{"report_type":"periodic","title":"...","risk_level":"medium","summary":"...","key_findings":["..."],"recommendations":["..."]}}
"""

# ---------------------------------------------------------------------------
# 根因诊断（对齐 chain_schemas.DiagnosisChainOutput）
# ---------------------------------------------------------------------------
DIAGNOSIS_PROMPT = """你是一名电商日志根因分析专家，负责根据证据包推断异常根因并给出处置建议。

## 输入
以下 JSON 为已压缩的证据包（含 ERROR/WARN 样本、分组统计与 metrics）：
{evidence_package}

## 任务
1. 结合 top_error_codes、top_services 与样本日志推断最可能的根因（root_cause）。
2. 评估置信度（confidence，0~1 浮点数）与严重等级（severity）。
3. 列出受影响服务（affected_services）与可引用的证据摘要（evidence_refs）。
4. 给出可执行的行动建议（action_suggestions）。

## 约束
- 结论必须基于证据包中的字段与样本，禁止编造日志中不存在的错误码、服务名或指标。
- severity 取 "low" | "medium" | "high" | "critical" 之一。
- 证据不足时降低 confidence，并在 root_cause 中说明不确定性。

## 输出要求
**仅输出一个 JSON 对象，不要 Markdown 代码块，不要任何额外解释。**

字段说明（字段名必须完全一致）：
- root_cause: 根因描述（简体中文）
- confidence: 0~1 之间的浮点数
- severity: "low" | "medium" | "high" | "critical"
- affected_services: 受影响服务名列表
- evidence_refs: 证据引用列表（如错误码、样本摘要、指标键名）
- action_suggestions: 处置建议字符串列表

示例结构：
{{"root_cause":"...","confidence":0.82,"severity":"high","affected_services":["payment-service"],"evidence_refs":["PAY_FAIL x12"],"action_suggestions":["..."]}}
"""

# ---------------------------------------------------------------------------
# 证据摘要压缩（供后续 LLM 分析前二次压缩，纯文本摘要）
# ---------------------------------------------------------------------------
EVIDENCE_SUMMARY_PROMPT = """你是一名日志证据压缩助手，负责将较大的证据包压缩为更短、信息密度更高的摘要，供下游分析模型使用。

## 输入
原始证据包 JSON：
{evidence_package}

## 任务
1. 保留 ERROR/WARN 级别关键信息与 top 统计（服务、错误码、错误计数）。
2. 将 samples 压缩为少量代表性条目摘要，丢弃冗余字段。
3. 不重新计算统计指标，直接引用输入中的 summary/metrics 数值。

## 输出要求
**仅输出一个 JSON 对象，不要 Markdown 代码块，不要任何额外解释。**

字段说明：
- compressed_summary: 一段话概括当前证据包核心异常与影响范围
- key_metrics: 对象，保留输入中的关键数值指标（错误数、错误率、请求量等）
- top_services: 字符串数组，受影响最严重的前若干服务
- top_error_codes: 字符串数组，出现频率最高的错误码
- sample_highlights: 字符串数组，每条为一条代表性日志摘要（≤5 条）
- token_saved_hint: 字符串，简要说明压缩策略（如"保留 ERROR 优先"）

示例结构：
{{"compressed_summary":"...","key_metrics":{{}},"top_services":[],"top_error_codes":[],"sample_highlights":[],"token_saved_hint":"..."}}
"""

# ---------------------------------------------------------------------------
# 预警解释（M5/M6 使用，基础版）
# ---------------------------------------------------------------------------
ALERT_PROMPT = """你是一名电商运维预警解释专家，负责为候选预警生成清晰、可操作的说明文案。

## 输入
候选预警与关联证据 JSON：
{alert_context}

## 任务
1. 用简明中文解释预警原因与业务影响。
2. 引用证据中的关键指标或日志模式，勿编造未出现的字段。
3. 给出优先级合理的处理建议。

## 输出要求
**仅输出一个 JSON 对象，不要 Markdown 代码块，不要任何额外解释。**

字段说明：
- title: 预警标题（简体中文，≤30 字）
- description: 预警详细说明，含原因与影响范围
- severity: "low" | "medium" | "high" | "critical"
- impact_scope: 字符串数组，受影响的服务、接口或业务域
- suggested_actions: 字符串数组，建议的处置步骤（按优先级排序）
- evidence_summary: 一句话概括支撑该预警的关键证据

示例结构：
{{"title":"...","description":"...","severity":"high","impact_scope":["payment-service"],"suggested_actions":["..."],"evidence_summary":"..."}}
"""

# ---------------------------------------------------------------------------
# 隐藏关系发现（对齐 chain_schemas.RelationChainOutput）
# ---------------------------------------------------------------------------
RELATION_PROMPT = """你是一名电商日志关联分析专家，负责从证据包中发现指标、事件与服务之间的隐藏因果或相关关系。

## 输入
以下 JSON 为已压缩的证据包（含 summary、grouped、samples、metrics 等多模板聚合摘要，如 traffic/errors/latency/funnel 等）；时间窗已由系统给定，请直接引用其中的实体与数值，勿凭空估算：
{evidence_package}

## 任务
1. 综合 summary、metrics、grouped 与 samples，识别跨维度关联模式（例如「请求高峰 → 随后支付失败率上升」「某服务延迟升高 → 下游错误增多」）。
2. 对每条关系判断类型（relation_type），用一句话中文描述（description），列出涉及的指标/服务/错误码（entities）。
3. 根据证据充分程度评估置信度（confidence，0~1 浮点数），并列出支撑该关系的证据引用（evidence_refs，如聚合模板名、指标键名或样本摘要标识）。

## 约束
- 结论必须基于证据包内出现的实体、指标与样本，禁止编造日志中不存在的服务名、错误码或数值。
- relation_type 取 "temporal_correlation" | "causal_hypothesis" | "co_occurrence" 之一：
  - temporal_correlation：时间先后或同步波动相关
  - causal_hypothesis：有证据支撑的因果推断（须说明不确定性）
  - co_occurrence：同一时段内共同出现或同步异常
- 证据不足或无法发现可靠关系时，输出空数组 relations: []，不得强行编造关系。
- entities 与 evidence_refs 中的名称须与证据包字段或样本内容可对应。

## 输出要求
**仅输出一个 JSON 对象，不要 Markdown 代码块，不要任何额外解释。**

字段说明（字段名必须完全一致）：
- relations: 关系数组，每项包含：
  - relation_type: "temporal_correlation" | "causal_hypothesis" | "co_occurrence"
  - description: 一句话中文描述该关系
  - entities: 涉及的指标/服务/错误码名称列表
  - confidence: 0~1 之间的浮点数
  - evidence_refs: 支撑该关系的证据引用列表（聚合模板名或样本片段标识）

无关系时输出：
{{"relations":[]}}

示例结构：
{{"relations":[{{"relation_type":"temporal_correlation","description":"请求量高峰后 5 分钟内支付失败率显著上升","entities":["request_count","payment-service","PAY_FAIL"],"confidence":0.78,"evidence_refs":["traffic","errors","samples#3"]}}]}}
"""

_PROMPT_REGISTRY: dict[str, str] = {
    "report": REPORT_PROMPT,
    "diagnosis": DIAGNOSIS_PROMPT,
    "relation": RELATION_PROMPT,
    "alert": ALERT_PROMPT,
    "evidence_summary": EVIDENCE_SUMMARY_PROMPT,
}


def get_prompt(name: str) -> str:
    """按名称获取 Prompt 模板字符串。

    调用方使用 ``prompt.format(evidence_package=..., alert_context=...)`` 填充占位符。
    未知名称时返回空字符串，由上层决定是否降级。
    """
    return _PROMPT_REGISTRY.get(name, "")
