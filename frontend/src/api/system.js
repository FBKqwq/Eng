import request from './request'

export const getApiHealth = () => request.get('/health')

export const getSystemStatus = () => request.get('/system/status')

export const verifyPipeline = (payload = {}) =>
  request.post('/system/pipeline/verify', payload, {
    timeout: 210000
  })
