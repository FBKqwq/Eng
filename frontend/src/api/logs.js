import request from './request'
export const searchLogs = (data) => request.post('/logs/search', data)
