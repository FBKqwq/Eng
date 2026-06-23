import request from './request'

export const USE_MOCK = false

/** 分析主图同步执行长超时（毫秒），对齐后端数十秒级耗时 */
const ANALYSIS_RUN_TIMEOUT_MS = 120000

/** node_trace 摘要演示条目（node_name / status / duration_ms / output_summary） */
const MOCK_NODE_TRACE_SUMMARY = [
  { node_name: 'log_fetch', status: 'success', duration_ms: 820, output_summary: '拉取 128 条候选日志' },
  { node_name: 'pattern_detect', status: 'success', duration_ms: 1240, output_summary: '匹配超时异常模式' },
  { node_name: 'rule_diagnose', status: 'success', duration_ms: 95, output_summary: '规则路由：service_timeout' },
  { node_name: 'report_write', status: 'success', duration_ms: 310, output_summary: '写入分析报告' }
]

const MOCK_RECENT_RUNS = {
  items: [
    {
      report_id: 'demo-report-001',
      report_type: 'event',
      title: 'order-service 超时异常分析（演示）',
      created_at: '2026-06-23T08:30:00Z',
      trigger_type: 'rule',
      node_trace: MOCK_NODE_TRACE_SUMMARY,
      node_count: MOCK_NODE_TRACE_SUMMARY.length,
      total_duration_ms: MOCK_NODE_TRACE_SUMMARY.reduce((sum, n) => sum + n.duration_ms, 0)
    }
  ],
  total: 1,
  limit: 20
}

/**
 * 最近分析运行 → GET /analysis/runs/recent?limit=
 *
 * 解包后 res.data：
 * { items[{ report_id, report_type, title, created_at, trigger_type,
 *   node_trace[{ node_name, status, duration_ms, output_summary }], node_count, total_duration_ms }], total, limit }
 */
export const getRecentAnalysisRuns = (params) => {
  if (USE_MOCK) {
    const limit = params?.limit ?? 20
    return Promise.resolve({
      data: {
        items: MOCK_RECENT_RUNS.items.slice(0, limit),
        total: MOCK_RECENT_RUNS.total,
        limit
      }
    })
  }
  return request.get('/analysis/runs/recent', { params })
}

/**
 * 触发分析运行 → POST /analysis/run（同步长耗时）
 *
 * 请求体（AnalysisRunRequest）：trigger_type（scheduled | rule）、trigger_event?、time_window?
 *
 * 解包后 res.data：
 * { report_id, alert_id, node_trace[], alert_decision{}, errors[] }
 *
 * graph_failed 时 Promise reject（e.error.code === 'graph_failed'），
 * 但 e.response.data.data 可能仍含 node_trace，阶段环可降级展示已完成的节点轨迹。
 *
 * 失败：catch (e) { e.error?.code }；graph_failed 时读 e.response?.data?.data?.node_trace
 */
export const triggerAnalysisRun = (payload) => {
  if (USE_MOCK) {
    return Promise.resolve({
      data: {
        report_id: 'demo-report-002',
        alert_id: null,
        node_trace: MOCK_NODE_TRACE_SUMMARY,
        alert_decision: {
          should_alert: false,
          is_duplicate: false,
          existing_alert_id: null,
          idempotency_key: 'demo-idempotency-key',
          explanation: '演示数据：未触发新预警'
        },
        errors: []
      }
    })
  }
  return request.post('/analysis/run', payload, { timeout: ANALYSIS_RUN_TIMEOUT_MS })
}
