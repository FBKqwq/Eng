import request from './request'

export const USE_MOCK = false

/** 规则诊断降级演示样例（route: rule） */
const MOCK_DIAGNOSIS_DATA = {
  message: '规则诊断完成（演示数据）',
  input: {
    request_id: 'demo-request-001',
    keyword: 'timeout',
    service_name: 'order-service',
    error_code: 'E503',
    time_range_start: '2026-06-23T00:00:00Z',
    time_range_end: '2026-06-23T23:59:59Z'
  },
  diagnosis: {
    anomaly_type: 'service_timeout',
    severity: 'high',
    route: 'rule',
    root_cause: 'order-service 在采样窗口内出现多次超时，疑似下游 payment-service 响应延迟',
    suggestion: [
      '检查 payment-service 近期部署与资源使用率',
      '核对 order-service 调用 payment 的超时配置',
      '查看 Trace 瀑布图确认慢调用链'
    ],
    evidence_logs: [],
    context_summary: {
      matched_rules: ['timeout_spike'],
      log_count: 0,
      sample_window: '24h'
    }
  }
}

/**
 * 提交规则诊断 → POST /diagnosis
 *
 * 请求体（DiagnosisRequest）：
 * - request_id（必填）
 * - keyword / service_name / error_code / time_range_start / time_range_end（常用可选）
 *
 * 解包后 res.data：
 * { message, input{}, diagnosis{ anomaly_type, severity, route, root_cause, suggestion[], evidence_logs[], context_summary{} } }
 *
 * 注意：规则诊断响应不含 node_trace（规则诊断门面）。
 * 阶段环数据来自 getReportDetail 的 report.node_trace 或 triggerAnalysisRun 返回的 node_trace（见 analysis.js）。
 *
 * 失败：catch (e) { e.error?.code }，常见 diagnosis_failed
 */
export const submitDiagnosis = (payload) => {
  if (USE_MOCK) {
    return Promise.resolve({
      data: {
        ...MOCK_DIAGNOSIS_DATA,
        input: { ...MOCK_DIAGNOSIS_DATA.input, ...payload }
      }
    })
  }
  return request.post('/diagnosis', payload)
}

/** 兼容旧页面引用，与 submitDiagnosis 等价 */
export const runDiagnosis = submitDiagnosis
