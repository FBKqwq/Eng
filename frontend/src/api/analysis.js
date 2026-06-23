import request from './request'

export const USE_MOCK = true

/** 最近分析运行 → GET /analysis/runs/recent?limit=；解包后 res.data：{ items, total, limit } */
export const getRecentAnalysisRuns = (params) => {
  if (USE_MOCK) {
    const limit = params?.limit ?? 20
    return Promise.resolve({ data: { items: [], total: 0, limit } })
  }
  return request.get('/analysis/runs/recent', { params })
}

/**
 * 触发分析运行 → POST /analysis/run（同步长耗时，默认超时 ≥120s）
 * 解包后 res.data：{ report_id, alert_id, node_trace[], alert_decision{}, errors[] }
 * graph_failed 时 catch 但 error.response 中 data 可能仍含 node_trace
 */
export const triggerAnalysisRun = (payload) => {
  if (USE_MOCK) {
    return Promise.resolve({
      data: {
        report_id: null,
        alert_id: null,
        node_trace: [],
        alert_decision: {},
        errors: []
      }
    })
  }
  return request.post('/analysis/run', payload, { timeout: 120000 })
}
