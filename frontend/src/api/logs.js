import request from './request'

/** 分页默认值（对齐后端 LogQueryRequest） */
const DEFAULT_PAGE = 1
const DEFAULT_PAGE_SIZE = 20
const DEFAULT_SORT_BY = 'timestamp'
const DEFAULT_SORT_ORDER = 'desc'
const MAX_PAGE_SIZE = 500

/** LogQueryRequest 允许的请求字段（不含已废弃的 time_range） */
const LOG_QUERY_FIELDS = [
  'start_time',
  'end_time',
  'service_names',
  'log_levels',
  'log_types',
  'event_types',
  'error_codes',
  'trace_id',
  'request_id',
  'user_id',
  'session_id',
  'order_id',
  'keyword',
  'status_codes',
  'statuses',
  'envs',
  'tags'
]

/**
 * 将 Date / 时间戳转为 ISO-8601 UTC 字符串（如 2026-06-22T16:00:00.000Z）。
 * @param {string | number | Date | null | undefined} value
 * @returns {string | undefined}
 */
function toIsoUtc(value) {
  if (value == null || value === '') return undefined
  if (typeof value === 'string') return value
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return undefined
  return date.toISOString()
}

/**
 * 归一化 LogQueryRequest 请求体：
 * - 将遗留 time_range 映射为 start_time / end_time，最终请求体不含 time_range
 * - 补全 page / page_size / sort_by / sort_order 默认值
 * - page_size 钳制在 1~500
 *
 * @param {Record<string, unknown>} [payload]
 * @returns {Record<string, unknown>}
 */
function buildLogQueryPayload(payload = {}) {
  const {
    time_range: timeRange,
    page,
    page_size: pageSize,
    sort_by: sortBy,
    sort_order: sortOrder,
    ...rest
  } = payload

  const body = {}

  for (const key of LOG_QUERY_FIELDS) {
    if (rest[key] !== undefined && rest[key] !== null && rest[key] !== '') {
      body[key] = rest[key]
    }
  }

  const rangeStart = timeRange?.start_time ?? timeRange?.start
  const rangeEnd = timeRange?.end_time ?? timeRange?.end

  const startTime = toIsoUtc(body.start_time ?? rangeStart)
  const endTime = toIsoUtc(body.end_time ?? rangeEnd)
  if (startTime) body.start_time = startTime
  if (endTime) body.end_time = endTime

  const normalizedPage = Number(page ?? DEFAULT_PAGE)
  body.page =
    Number.isFinite(normalizedPage) && normalizedPage >= 1
      ? Math.floor(normalizedPage)
      : DEFAULT_PAGE

  const normalizedSize = Number(pageSize ?? DEFAULT_PAGE_SIZE)
  body.page_size = Number.isFinite(normalizedSize)
    ? Math.min(MAX_PAGE_SIZE, Math.max(1, Math.floor(normalizedSize)))
    : DEFAULT_PAGE_SIZE

  body.sort_by = String(sortBy ?? DEFAULT_SORT_BY) || DEFAULT_SORT_BY
  body.sort_order = sortOrder === 'asc' ? 'asc' : DEFAULT_SORT_ORDER

  return body
}

/**
 * 日志检索 → POST /logs/search
 *
 * 请求体对齐 LogQueryRequest；调用方传入 start_time/end_time（ISO-8601 带时区），
 * 或由遗留 time_range 自动映射。分页默认 page=1、page_size=20；
 * 排序默认 sort_by=timestamp、sort_order=desc。
 *
 * 解包后 res.data：{ items, total, page, page_size, has_more, took_ms }
 * 失败：catch (e) { e.error?.code }，如 es_unavailable
 *
 * @param {Record<string, unknown>} [payload]
 */
export const searchLogs = (payload) =>
  request.post('/logs/search', buildLogQueryPayload(payload))

/**
 * 字段目录 → GET /logs/fields?log_type=
 *
 * @param {string} [logType] 日志大类；省略时返回全量 registered_log_types
 * @returns {Promise<import('axios').AxiosResponse>}
 *
 * 带 logType 解包后 res.data：
 * { log_type, catalog: { filter_fields[], terms_fields[], metric_fields[], ... } }
 * catalog.filter_fields 可驱动 DynamicFilterBar 动态筛选。
 *
 * 不带参解包后 res.data：{ registered_log_types[] }
 *
 * 非法 log_type：reject，e.error?.code === 'invalid_param'
 */
export const getLogFields = (logType) => {
  const config =
    logType != null && String(logType).trim() !== ''
      ? { params: { log_type: String(logType).trim() } }
      : {}
  return request.get('/logs/fields', config)
}

/**
 * 受控聚合 → POST /logs/aggregate
 *
 * 解包后 res.data：{ group_by, interval, buckets[], took_ms, extra? }
 *
 * @param {Record<string, unknown>} data LogAggregateRequest
 */
export const aggregateLogs = (data) => request.post('/logs/aggregate', data)

/**
 * 按 trace_id 检索链路日志（无 GET /logs/trace/{id}）
 *
 * 内部走 searchLogs，page_size=500、sort_by=timestamp、sort_order=asc。
 * 解包后 res.data.items 为时序升序链路日志。
 *
 * @param {string} traceId
 */
export const searchByTraceId = (traceId) =>
  searchLogs({
    trace_id: traceId,
    page: 1,
    page_size: 500,
    sort_by: 'timestamp',
    sort_order: 'asc'
  })
