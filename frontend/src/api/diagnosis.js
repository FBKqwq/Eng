import request from './request'
export const runDiagnosis = (data) => request.post('/diagnosis', data)
