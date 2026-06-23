/**
 * Kibana 外链生成工具（离线拼 URL，不访问 Kibana API）。
 * 规则与后端 tools/kibana_tools.kibana_generate_link 对齐，供配置页与监控页消费。
 */

const MAX_TIME_WINDOW_MS = 24 * 60 * 60 * 1000

/**
 * 读取 VITE_KIBANA_URL，未配置或空白时返回 null。
 * @returns {string|null}
 */
export function getKibanaBaseUrl() {
  const base = String(import.meta.env.VITE_KIBANA_URL || '').trim()
  return base ? base.replace(/\/+$/, '') : null
}

/**
 * 读取可选默认索引模式。
 * @returns {string|null}
 */
function getDefaultIndexPattern() {
  const pattern = String(import.meta.env.VITE_KIBANA_DEFAULT_INDEX_PATTERN || '').trim()
  return pattern || null
}

/**
 * @param {string} value
 */
function risonEscape(value) {
  return value.replace(/\\/g, '\\\\').replace(/'/g, "\\'")
}

/**
 * @param {number|string|Date} value
 * @returns {string|null}
 */
function toUtcIso(value) {
  if (value == null || value === '') return null
  let date
  if (value instanceof Date) {
    date = value
  } else if (typeof value === 'number') {
    date = new Date(value < 1e12 ? value * 1000 : value)
  } else {
    date = new Date(value)
  }
  if (Number.isNaN(date.getTime())) return null
  return date.toISOString()
}

/**
 * 从 timeRange 对象解析起止时间（兼容 useTimeRange 与 API 字段名）。
 * @param {{ start?: number|string|Date, end?: number|string|Date, start_time?: number|string|Date, end_time?: number|string|Date }|null|undefined} timeRange
 * @returns {{ start: Date, end: Date }|null}
 */
function resolveTimeRange(timeRange) {
  if (!timeRange) return null
  const startRaw = timeRange.start_time ?? timeRange.start
  const endRaw = timeRange.end_time ?? timeRange.end
  const startIso = toUtcIso(startRaw)
  const endIso = toUtcIso(endRaw)
  if (!startIso || !endIso) return null
  const start = new Date(startIso)
  const end = new Date(endIso)
  if (end.getTime() <= start.getTime()) return null
  if (end.getTime() - start.getTime() > MAX_TIME_WINDOW_MS) return null
  return { start, end }
}

/**
 * 拼装 Kibana Discover 深链（KQL + 时间窗 + 索引模式）。
 * @param {{ index?: string, query?: string, timeRange?: { start?: number|string|Date, end?: number|string|Date, start_time?: number|string|Date, end_time?: number|string|Date } }} [options]
 * @returns {string|null} 无 base URL 或参数无效时返回 null
 */
export function buildDiscoverLink(options = {}) {
  const baseUrl = getKibanaBaseUrl()
  if (!baseUrl) return null

  const indexPattern = String(options.index || getDefaultIndexPattern() || '').trim()
  if (!indexPattern) return null

  const resolved = resolveTimeRange(options.timeRange)
  if (!resolved) return null

  const kqlQuery = String(options.query || '').trim()
  const fromIso = toUtcIso(resolved.start)
  const toIso = toUtcIso(resolved.end)
  if (!fromIso || !toIso) return null

  const escapedIndex = risonEscape(indexPattern)
  const escapedQuery = risonEscape(kqlQuery)

  const globalState = `(filters:!(),refreshInterval:(pause:!t,value:0),time:(from:'${fromIso}',to:'${toIso}'))`
  const appState = `(columns:!(),filters:!(),index:'${escapedIndex}',interval:auto,query:(language:kuery,query:'${escapedQuery}'),sort:!(!('@timestamp',desc)))`

  return `${baseUrl}/app/discover#/?_g=${globalState}&_a=${appState}`
}

/**
 * 拼装 Kibana Dashboard 查看页外链。
 * @param {string} id Dashboard 标识
 * @returns {string|null}
 */
export function buildDashboardLink(id) {
  const baseUrl = getKibanaBaseUrl()
  const dashboardId = String(id || '').trim()
  if (!baseUrl || !dashboardId) return null
  return `${baseUrl}/app/dashboards#/view/${encodeURIComponent(dashboardId)}`
}
