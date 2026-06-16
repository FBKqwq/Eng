import request from './request'

export const searchLogs = (data) => request.post('/logs/search', data)

export const getRecentLogs = (params) => request.get('/logs/recent', { params })

export const getLogTrace = (traceId) => request.get(`/logs/trace/${traceId}`)

export const getLogFields = (logType) =>
  request.get('/logs/fields', { params: { log_type: logType } })
