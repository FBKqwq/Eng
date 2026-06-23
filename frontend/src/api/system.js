import request from './request'

/** API 健康探活 → GET /health；解包后 res.data：{ status: "ok" } */
export const getApiHealth = () => request.get('/health')

/**
 * 系统运行快照 → GET /system/status
 * 解包后含 kafka/elasticsearch/docker/containers/services 等嵌套字段
 */
export const getSystemStatus = () => request.get('/system/status')

/** Docker 容器状态 → GET /system/containers；解包后 res.data：{ project, available, error, containers } */
export const getSystemContainers = () => request.get('/system/containers')

/** 全链路验证（长耗时，默认超时 ≥210s）→ POST /system/pipeline/verify */
export const verifyPipeline = (payload = {}) =>
  request.post('/system/pipeline/verify', payload, {
    timeout: 210000
  })
