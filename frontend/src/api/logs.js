import request from './request'
import { LOG_QUERY_REQUEST_FIELDS, normalizeFiltersForRequest } from '../utils/logQueryContract.js'

/** 分页默认值（对齐后端 LogQueryRequest） */
const DEFAULT_PAGE = 1
const DEFAULT_PAGE_SIZE = 20
const DEFAULT_SORT_BY = 'timestamp'
const DEFAULT_SORT_ORDER = 'desc'
const MAX_PAGE_SIZE = 500

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
 * - 将遗留 time_range 映射为 start_time / end_time
 * - 仅保留后端契约字段
 * - status_codes 归一化为 number[]
 *
 * @param {Record<string, unknown>} [payload]
 * @returns {Record<string, unknown>}
 */
export function buildLogQueryPayload(payload = {}) {
  const {
    time_range: timeRange,
    page,
    page_size: pageSize,
    sort_by: sortBy,
    sort_order: sortOrder,
    keyword,
    filters,
    ...rest
  } = payload

  const mergedFilters =
    filters && typeof filters === 'object'
      ? { ...filters, ...rest }
      : { ...rest }

  const normalized = normalizeFiltersForRequest(mergedFilters, keyword)

  const body = {}

  for (const key of LOG_QUERY_REQUEST_FIELDS) {
    if (normalized[key] !== undefined && normalized[key] !== null && normalized[key] !== '') {
      body[key] = normalized[key]
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
 * @param {Record<string, unknown>} [payload]
 */
export const searchLogs = (payload) =>
  request.post('/logs/search', buildLogQueryPayload(payload))

export const getLogFields = (logType) => {
  const config =
    logType != null && String(logType).trim() !== ''
      ? { params: { log_type: String(logType).trim() } }
      : {}
  return request.get('/logs/fields', config)
}

export const aggregateLogs = (data) => request.post('/logs/aggregate', data)

export const searchByTraceId = (traceId) =>
  searchLogs({
    trace_id: traceId,
    page: 1,
    page_size: 500,
    sort_by: 'timestamp',
    sort_order: 'asc'
  })

export { LOG_QUERY_REQUEST_FIELDS }
