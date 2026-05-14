import request from './request'

export const getApiHealth = () => request.get('/health')

export const getSystemStatus = () => request.get('/system/status')
