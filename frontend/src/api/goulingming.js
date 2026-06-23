import request from './request.js'

/**
 * 演示数据开关：true 时返回本地模拟数据，false 走后端接口。
 * 后端接口就绪后改为 false。
 */
export const USE_MOCK = true

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

/** 24 个时间桶（近 1 小时，每 2.5 分钟一个点），用于折线/柱状图 */
function _buildTimeBuckets() {
  const buckets = []
  const now = Date.now()
  const interval = 150_000 // 2.5 分钟
  for (let i = 23; i >= 0; i--) {
    const t = new Date(now - i * interval)
    buckets.push(
      `${String(t.getHours()).padStart(2, '0')}:${String(t.getMinutes()).padStart(2, '0')}`
    )
  }
  return buckets
}

/** 演示用折线图数据，模拟真实业务波动 */
function _mockTrafficSeries(categories) {
  const base = [420, 435, 412, 448, 472, 510, 538, 590, 632, 618, 654, 680,
    698, 672, 645, 620, 598, 572, 548, 520, 498, 475, 460, 445]
  const unit = categories.length / base.length
  return categories.map((_, i) => Math.round(base[Math.floor(i / unit)] * (0.88 + Math.sin(i * 0.4) * 0.12)))
}

/** 演示用错误率数据（百分比），波动较小 */
function _mockErrorRateSeries(categories) {
  return categories.map((_, i) => parseFloat((1.8 + Math.sin(i * 0.6) * 0.5 + (Math.random() * 0.3 - 0.15)).toFixed(2)))
}

/** 演示用延迟分布柱状图数据（毫秒，区间桶） */
const mockLatencyBuckets = ['<50ms', '50-100ms', '100-200ms', '200-500ms', '>500ms']
const mockLatencyData = [4128, 5432, 2654, 482, 151]

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

/**
 * 获取流量趋势时间序列（折线图）
 * @param {object} payload start_time (ms) / end_time (ms)
 */
export function getTrafficTrend(payload = {}) {
  if (USE_MOCK) {
    const cats = _buildTimeBuckets()
    return Promise.resolve({
      data: {
        categories: cats,
        series: [{ name: '请求量', data: _mockTrafficSeries(cats) }]
      }
    })
  }
  // 真实路径：后端 aggregate_traffic 返回的 buckets 做时间桶格式化
  return request.post('/logs/aggregate', {
    ...payload,
    aggregation_type: 'time_histogram',
    field: '@timestamp',
    interval: '5m',
    log_types: ['application']
  })
}

/**
 * 获取错误率趋势（折线图）
 * @param {object} payload start_time (ms) / end_time (ms)
 */
export function getErrorTrend(payload = {}) {
  if (USE_MOCK) {
    const cats = _buildTimeBuckets()
    return Promise.resolve({
      data: {
        categories: cats,
        series: [{ name: '错误率(%)', data: _mockErrorRateSeries(cats) }]
      }
    })
  }
  return request.post('/logs/aggregate', {
    ...payload,
    aggregation_type: 'errors',
    log_types: ['application']
  })
}

/**
 * 获取延迟分布柱状图
 * @param {object} payload start_time (ms) / end_time (ms)
 */
export function getLatencyDistribution(payload = {}) {
  if (USE_MOCK) {
    return Promise.resolve({
      data: {
        categories: mockLatencyBuckets,
        series: [{ name: '请求数', data: mockLatencyData }]
      }
    })
  }
  return request.post('/logs/aggregate', {
    ...payload,
    aggregation_type: 'latency',
    log_types: ['application']
  })
}
