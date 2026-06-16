import request from './request'

export const USE_MOCK = true

const mockReports = []

export const getRecentReports = (params) => {
  if (USE_MOCK) return Promise.resolve({ data: mockReports })
  return request.get('/reports/recent', { params })
}

export const getReportDetail = (id) => {
  if (USE_MOCK) return Promise.resolve({ data: null })
  return request.get(`/reports/${id}`)
}
