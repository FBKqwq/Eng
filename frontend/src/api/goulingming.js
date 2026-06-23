import request from './request.js'

/**
 * 演示数据开关：true 时返回本地模拟数据，false 走后端接口。
 * 后端接口就绪后改为 false。
 */
export const USE_MOCK = false

const mockStats = {
  total_requests: 12847,
  total_requests_delta: 12.3,
  error_rate: 0.023,
  error_rate_delta: -0.5,
  avg_latency: 87,
  avg_latency_delta: -8.2,
  active_services: 6
}

const mockServices = [
  { name: 'order-service', status: 'healthy', qps: 342, error_rate: 0.015 },
  { name: 'user-service', status: 'healthy', qps: 210, error_rate: 0.008 },
  { name: 'product-service', status: 'healthy', qps: 156, error_rate: 0.003 },
  { name: 'payment-service', status: 'degraded', qps: 98, error_rate: 0.12 },
  { name: 'notification-service', status: 'healthy', qps: 45, error_rate: 0.001 },
  { name: 'search-service', status: 'healthy', qps: 523, error_rate: 0.022 }
]

/**
 * 获取核心统计指标
 * @param {object} payload start_time (ms) / end_time (ms)
 */
export function getGoulingmingStats(payload = {}) {
  if (USE_MOCK) {
    return Promise.resolve({ data: { ...mockStats } })
  }
  return request.post('/v1/goulingming/stats', payload)
}

/**
 * 获取服务节点状态列表
 */
export function getServiceStatus() {
  if (USE_MOCK) {
    return Promise.resolve({ data: { services: [...mockServices], total: mockServices.length } })
  }
  return request.get('/v1/goulingming/services')
}

/**
 * Goulingming 日志检索（透传现有 logs API，限定 log_types 为 application）
 * 完整参数见 src/api/logs.js searchLogs
 */
export function searchGoulingmingLogs(payload = {}) {
  return request.post('/logs/search', {
    ...payload,
    log_types: ['application']
  })
}
