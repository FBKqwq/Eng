import request from './request'
export const getSystemStatus = () => request.get('/system/status')
