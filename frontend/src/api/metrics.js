import { aggregateLogs } from './logs.js'

/** 后端聚合未对接或离线演示时启用；mock 形态对齐解包后的 aggregate 负载 */
export const USE_MOCK = true

const mockAggregate = (groupBy) =>
  Promise.resolve({
    data: { group_by: groupBy, buckets: [], took_ms: 0 }
  })

/** 流量趋势：application + web_server，按服务名与时间粒度聚合 */
export const queryTraffic = (payload) => {
  if (USE_MOCK) return mockAggregate('service_name')
  return aggregateLogs({
    group_by: 'service_name',
    interval: '1m',
    log_types: ['application', 'web_server'],
    ...payload
  })
}

/** 错误分布：application + web_server，按 error_code 聚合 */
export const queryErrors = (payload) => {
  if (USE_MOCK) return mockAggregate('error_code')
  return aggregateLogs({
    group_by: 'error_code',
    log_types: ['application', 'web_server'],
    ...payload
  })
}

/** 耗时趋势：application + web_server + performance，按 service_name 聚合 */
export const queryLatency = (payload) => {
  if (USE_MOCK) return mockAggregate('service_name')
  return aggregateLogs({
    group_by: 'service_name',
    log_types: ['application', 'web_server', 'performance'],
    ...payload
  })
}

/** 行为漏斗：按 event_type 聚合 behavior 类日志 */
export const queryBehaviorFunnel = (payload) => {
  if (USE_MOCK) return mockAggregate('event_type')
  return aggregateLogs({
    group_by: 'event_type',
    log_types: ['behavior'],
    ...payload
  })
}

/** 安全分布：security 类日志，按 event_type 聚合（通用 aggregate 无 risk_level 维度） */
export const querySecurity = (payload) => {
  if (USE_MOCK) return mockAggregate('event_type')
  return aggregateLogs({
    group_by: 'event_type',
    log_types: ['security'],
    ...payload
  })
}

/** 基础设施健康：infrastructure + performance，按 service_name 聚合 */
export const queryInfraHealth = (payload) => {
  if (USE_MOCK) return mockAggregate('service_name')
  return aggregateLogs({
    group_by: 'service_name',
    log_types: ['infrastructure', 'performance'],
    ...payload
  })
}
