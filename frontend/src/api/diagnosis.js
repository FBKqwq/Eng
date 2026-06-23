import request from './request'

/**
 * 提交诊断 → POST /diagnosis
 * 解包后 res.data：{ message, input, diagnosis{ anomaly_type, severity, route, root_cause, suggestion[], evidence_logs[], context_summary } }
 *
 * 注意：规则诊断响应不含 node_trace；阶段环数据来自 getReportDetail 的 report.node_trace
 * 或 triggerAnalysisRun 返回的 node_trace（见 analysis.js）。
 */
export const submitDiagnosis = (data) => request.post('/diagnosis', data)

/** 兼容旧页面引用，与 submitDiagnosis 等价 */
export const runDiagnosis = submitDiagnosis
