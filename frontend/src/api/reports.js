import request from './request'

export const USE_MOCK = true

/** 最近报告 → GET /reports/recent?limit=；解包后 res.data：{ items, total, limit } */
export const getRecentReports = (params) => {
  if (USE_MOCK) {
    const limit = params?.limit ?? 20
    return Promise.resolve({ data: { items: [], total: 0, limit } })
  }
  return request.get('/reports/recent', { params })
}

/** 报告详情 → GET /reports/{report_id}；未命中时 report 为 null（仍 200） */
export const getReportDetail = (reportId) => {
  if (USE_MOCK) {
    return Promise.resolve({ data: { report_id: reportId ?? null, report: null } })
  }
  return request.get(`/reports/${reportId}`)
}
