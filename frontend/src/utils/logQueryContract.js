/**
 * 与后端 LogQueryRequest 对齐的查询契约。
 * 仅在此映射内的字段会作为精确筛选进入 POST /logs/search。
 */

/** 后端 LogQueryRequest 允许的请求键 */
export const LOG_QUERY_REQUEST_FIELDS = Object.freeze([
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
  'tags',
  'page',
  'page_size',
  'sort_by',
  'sort_order'
])

const TERM_OPTIONS = {
  log_level: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
  env: ['dev', 'test', 'prod'],
  status: ['success', 'fail', 'timeout', 'blocked', 'partial_success', 'unknown']
}

/**
 * catalog / UI 字段名 → 请求契约
 * @type {Record<string, { key: string, type: 'terms'|'keyword', options?: string[], tier: 'common'|'advanced', label: string }>}
 */
export const QUERY_FIELD_MAP = Object.freeze({
  service_name: {
    key: 'service_names',
    type: 'terms',
    tier: 'common',
    label: '服务'
  },
  log_level: {
    key: 'log_levels',
    type: 'terms',
    options: TERM_OPTIONS.log_level,
    tier: 'common',
    label: '日志级别'
  },
  event_type: {
    key: 'event_types',
    type: 'terms',
    tier: 'common',
    label: '事件类型'
  },
  error_code: {
    key: 'error_codes',
    type: 'terms',
    tier: 'common',
    label: '错误码'
  },
  status_code: {
    key: 'status_codes',
    type: 'terms',
    tier: 'common',
    label: '状态码',
    numeric: true
  },
  trace_id: {
    key: 'trace_id',
    type: 'keyword',
    tier: 'advanced',
    label: '链路 ID'
  },
  request_id: {
    key: 'request_id',
    type: 'keyword',
    tier: 'advanced',
    label: '请求 ID'
  },
  user_id: {
    key: 'user_id',
    type: 'keyword',
    tier: 'advanced',
    label: '用户 ID'
  },
  session_id: {
    key: 'session_id',
    type: 'keyword',
    tier: 'advanced',
    label: '会话 ID'
  },
  order_id: {
    key: 'order_id',
    type: 'keyword',
    tier: 'advanced',
    label: '订单 ID'
  },
  env: {
    key: 'envs',
    type: 'terms',
    options: TERM_OPTIONS.env,
    tier: 'advanced',
    label: '环境'
  },
  status: {
    key: 'statuses',
    type: 'terms',
    options: TERM_OPTIONS.status,
    tier: 'advanced',
    label: '状态'
  },
  tags: {
    key: 'tags',
    type: 'terms',
    tier: 'advanced',
    label: '标签'
  }
})

/** keyword multi_match 已覆盖的字段提示（不可精确筛选） */
export const KEYWORD_HINT_FIELDS = Object.freeze([
  'message',
  'request_path',
  'event_type',
  'service_name',
  'error_code',
  'trace_id'
])

/** 后端 search 未支持精确筛选的 catalog 字段（不渲染为 terms 控件） */
export const UNSUPPORTED_PRECISE_FIELDS = Object.freeze([
  'action',
  'request_uri',
  'uri',
  'remote_addr',
  'client_ip',
  'rule_name',
  'rule_id',
  'component',
  'operator_name',
  'operator_id',
  'operator_role',
  'page',
  'product_id',
  'product_name',
  'http_method',
  'upstream_addr',
  'risk_level',
  'metric_name',
  'resource_type',
  'severity',
  'target_type',
  'attack_type'
])

const EXCLUDED_CATALOG_FIELDS = new Set([
  'timestamp',
  'log_type',
  'log_id',
  'message',
  'span_id',
  'source_type',
  'service_instance',
  'user_agent',
  'host',
  ...UNSUPPORTED_PRECISE_FIELDS
])

const DISPLAY_PRIORITY = [
  'service_name',
  'log_level',
  'event_type',
  'error_code',
  'status_code',
  'trace_id',
  'user_id',
  'session_id',
  'order_id',
  'env',
  'status',
  'tags'
]

/**
 * 从 field_catalog 生成可渲染的筛选描述符（仅契约内字段）
 * @param {object} catalog
 * @returns {{ common: object[], advanced: object[] }}
 */
export function buildFilterDescriptorsFromCatalog(catalog) {
  const filterFields = catalog?.filter_fields || []

  const candidates = filterFields
    .filter((name) => !EXCLUDED_CATALOG_FIELDS.has(name) && QUERY_FIELD_MAP[name])
    .sort((a, b) => {
      const pa = DISPLAY_PRIORITY.indexOf(a)
      const pb = DISPLAY_PRIORITY.indexOf(b)
      return (pa === -1 ? 999 : pa) - (pb === -1 ? 999 : pb)
    })

  const descriptors = candidates.map((fieldName) => descriptorFromField(fieldName))

  return {
    common: descriptors.filter((d) => d.tier === 'common'),
    advanced: descriptors.filter((d) => d.tier === 'advanced')
  }
}

/**
 * @param {import('./logTypeMeta.js').FallbackFilter[]} fallbackFilters
 */
export function buildFilterDescriptorsFromFallback(fallbackFilters = []) {
  const list = []
  for (const raw of fallbackFilters) {
    const fieldName = raw.field || raw.name
    if (!fieldName || EXCLUDED_CATALOG_FIELDS.has(fieldName)) continue
    const mapped = QUERY_FIELD_MAP[fieldName]
    if (!mapped) continue
    list.push({
      ...descriptorFromField(fieldName),
      label: raw.label || mapped.label
    })
  }
  return {
    common: list.filter((d) => d.tier === 'common'),
    advanced: list.filter((d) => d.tier === 'advanced')
  }
}

function descriptorFromField(fieldName) {
  const mapped = QUERY_FIELD_MAP[fieldName]
  return {
    field: fieldName,
    key: mapped.key,
    label: mapped.label,
    type: mapped.type,
    tier: mapped.tier,
    numeric: Boolean(mapped.numeric),
    options: mapped.type === 'terms' ? mapped.options : undefined,
    multiple: mapped.type === 'terms',
    placeholder: mapped.type === 'keyword' ? '精确匹配' : '多个值用逗号分隔'
  }
}

/**
 * 将 UI 筛选模型归一化为 LogQueryRequest 片段（不含分页/时间）
 * @param {Record<string, unknown>} filters
 * @param {string} [keyword]
 */
export function normalizeFiltersForRequest(filters = {}, keyword = '') {
  const body = {}

  for (const [key, value] of Object.entries(filters)) {
    if (!LOG_QUERY_REQUEST_FIELDS.includes(key)) continue
    if (value == null || value === '' || (Array.isArray(value) && !value.length)) continue

    if (key === 'status_codes') {
      const nums = (Array.isArray(value) ? value : String(value).split(','))
        .map((v) => Number(String(v).trim()))
        .filter((n) => Number.isFinite(n))
      if (nums.length) body.status_codes = nums
      continue
    }

    if (Array.isArray(value)) {
      body[key] = value.map((v) => String(v).trim()).filter(Boolean)
      continue
    }

    body[key] = value
  }

  const kw = String(keyword || '').trim()
  if (kw) body.keyword = kw

  return body
}

/** 请求键 → 人类可读标签 */
export function requestKeyLabel(key) {
  for (const mapped of Object.values(QUERY_FIELD_MAP)) {
    if (mapped.key === key) return mapped.label
  }
  if (key === 'keyword') return '关键字'
  return key
}

/**
 * 从 filters + keyword 生成活跃 chip 列表
 * @returns {{ key: string, label: string, display: string }[]}
 */
export function buildActiveFilterChips(filters = {}, keyword = '') {
  const chips = []

  for (const [key, value] of Object.entries(filters)) {
    if (value == null || value === '' || (Array.isArray(value) && !value.length)) continue
    const label = requestKeyLabel(key)
    const display = Array.isArray(value) ? value.join(', ') : String(value)
    chips.push({ key, label, display })
  }

  const kw = String(keyword || '').trim()
  if (kw) {
    chips.push({ key: 'keyword', label: '关键字', display: kw })
  }

  return chips
}
