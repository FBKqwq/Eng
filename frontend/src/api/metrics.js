import { aggregateLogs } from './logs.js'

/**
 * 离线演示时临时改为 true；默认走后端 POST /logs/aggregate（template 路由六类预置模板）。
 */
export const USE_MOCK = false

/**
 * @param {string} template
 * @param {string} [interval]
 * @returns {Promise<{ data: { group_by: string, buckets: [], took_ms: number, interval?: string } }>}
 */
const mockAggregate = (template, interval) =>
  Promise.resolve({
    data: {
      group_by: template,
      buckets: [],
      took_ms: 0,
      ...(interval ? { interval } : {})
    }
  })

/**
 * 六类业务聚合模板 → POST /logs/aggregate { template, ... }
 * 与后端 aggregation_service 预置模板对齐，禁止手写 group_by 冒充模板响应。
 *
 * @param {string} template traffic | errors | latency | behavior_funnel | security | infra_health
 * @param {Record<string, unknown>} payload start_time / end_time 及可选 interval、top_n 等
 */
function queryByTemplate(template, payload = {}) {
  if (USE_MOCK) {
    return mockAggregate(template, payload.interval)
  }
  return aggregateLogs({
    template,
    ...payload
  })
}

/** 按日志类型和聚合字段执行通用聚合，用于 7 个监控子页的差异化分析。 */
export const queryGroupedLogs = (payload = {}) => aggregateLogs(payload)

/** 流量趋势模板 */
export const queryTraffic = (payload) =>
  queryByTemplate('traffic', { interval: '1m', ...payload })

/** 错误分布 / 错误量时间序列（传 interval 时返回时间直方图） */
export const queryErrors = (payload) => queryByTemplate('errors', payload)

/** 耗时分位模板 */
export const queryLatency = (payload) => queryByTemplate('latency', payload)

/** 行为漏斗模板 */
export const queryBehaviorFunnel = (payload) => queryByTemplate('behavior_funnel', payload)

/** 安全事件分布模板 */
export const querySecurity = (payload) => queryByTemplate('security', payload)

/** 基础设施健康模板 */
export const queryInfraHealth = (payload) => queryByTemplate('infra_health', payload)
