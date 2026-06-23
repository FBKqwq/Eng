import request from './request'

/** 离线演示时临时改为 true；默认走后端 M4 报告 API */
export const USE_MOCK = false

/**
 * 最近报告 → GET /reports/recent?limit=
 *
 * limit 1~100，默认 20。
 *
 * 解包后 res.data：
 * { items[{ report_id, report_type, title, risk_level, summary, created_at, task_id }], total, limit }
 *
 * 失败：catch (e) { e.error?.code }，常见 query_failed
 */
export const getRecentReports = (params) => {
  if (USE_MOCK) {
    const limit = params?.limit ?? 20
    return Promise.resolve({ data: { items: [], total: 0, limit } })
  }
  return request.get('/reports/recent', { params })
}

/**
 * 报告详情 → GET /reports/{report_id}
 *
 * 解包后 res.data：
 * { report_id, report{ ...含 node_trace, sections, metrics_snapshot } }
 *
 * 未命中：ok:true 且 report:null（仍 200，非 404）→ 页面展示空态。
 *
 * 失败：catch (e) { e.error?.code }，常见 query_failed
 */
export const getReportDetail = (reportId) => {
  if (USE_MOCK) {
    return Promise.resolve({ data: { report_id: null, report: null } })
  }
  return request.get(`/reports/${reportId}`)
}
