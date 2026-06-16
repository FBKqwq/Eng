import request from './request'

/** 后端聚合接口就绪前使用 mock，页面走真实调用路径 */
export const USE_MOCK = true

const mockEmptyAggregate = { buckets: [], series: [], total: 0 }

export const queryTrafficAggregate = (data) => {
  if (USE_MOCK) return Promise.resolve({ data: mockEmptyAggregate })
  return request.post('/metrics/traffic', data)
}

export const queryErrorsAggregate = (data) => {
  if (USE_MOCK) return Promise.resolve({ data: mockEmptyAggregate })
  return request.post('/metrics/errors', data)
}

export const queryLatencyAggregate = (data) => {
  if (USE_MOCK) return Promise.resolve({ data: mockEmptyAggregate })
  return request.post('/metrics/latency', data)
}

export const queryBehaviorFunnelAggregate = (data) => {
  if (USE_MOCK) return Promise.resolve({ data: mockEmptyAggregate })
  return request.post('/metrics/behavior_funnel', data)
}

export const querySecurityAggregate = (data) => {
  if (USE_MOCK) return Promise.resolve({ data: mockEmptyAggregate })
  return request.post('/metrics/security', data)
}

export const queryInfraHealthAggregate = (data) => {
  if (USE_MOCK) return Promise.resolve({ data: mockEmptyAggregate })
  return request.post('/metrics/infra_health', data)
}
