import { ref, watch, onUnmounted } from 'vue'
import { useTimeRange } from './useTimeRange.js'
import { searchLogs } from '../api/logs.js'

const DEFAULT_PAGE_SIZE = 20
const DEFAULT_SORT_FIELD = '@timestamp'
const DEFAULT_SORT_ORDER = 'desc'
const RANGE_DEBOUNCE_MS = 300

/** ES 排序字段：UI 常用 @timestamp，API 契约为 timestamp */
function mapSortField(field) {
  if (field === '@timestamp') return 'timestamp'
  return field
}

/**
 * 统一监控页日志查询状态机：时间窗 + 筛选 + 分页 + 排序。
 * @param {string} logType 日志大类（behavior/application/...）
 * @param {{ field?: string, order?: string }} [defaultSort]
 */
export function useLogQuery(logType, defaultSort) {
  const { range } = useTimeRange()

  const loading = ref(false)
  const error = ref(null)
  const errorCode = ref(null)
  const items = ref([])
  const total = ref(0)
  const tookMs = ref(null)
  const hasMore = ref(false)
  const page = ref(1)
  const pageSize = ref(DEFAULT_PAGE_SIZE)
  const sort = ref({
    field: defaultSort?.field || DEFAULT_SORT_FIELD,
    order: defaultSort?.order === 'asc' ? 'asc' : DEFAULT_SORT_ORDER
  })
  const keyword = ref('')
  const filters = ref({})

  let fetchGeneration = 0
  let unmounted = false
  let rangeDebounceTimer = null

  function buildPayload() {
    const { field, order } = sort.value
    return {
      ...(logType ? { log_types: [logType] } : {}),
      start_time: new Date(range.value.start).toISOString(),
      end_time: new Date(range.value.end).toISOString(),
      page: page.value,
      page_size: pageSize.value,
      sort_by: mapSortField(field),
      sort_order: order === 'asc' ? 'asc' : 'desc',
      keyword: keyword.value || undefined,
      ...filters.value
    }
  }

  async function fetch() {
    if (unmounted) return

    const generation = ++fetchGeneration
    loading.value = true
    error.value = null
    errorCode.value = null

    try {
      const res = await searchLogs(buildPayload())
      if (unmounted || generation !== fetchGeneration) return

      items.value = (res.data?.items ?? []).map(enrichLogRow)
      total.value = res.data?.total ?? 0
      tookMs.value = res.data?.took_ms ?? null
      hasMore.value = Boolean(res.data?.has_more)
    } catch (e) {
      if (unmounted || generation !== fetchGeneration) return

      const code = e.error?.code ?? null
      errorCode.value = code
      error.value = e.message ?? '查询失败'
      items.value = []
      total.value = 0
      tookMs.value = null
      hasMore.value = false
    } finally {
      if (!unmounted && generation === fetchGeneration) {
        loading.value = false
      }
    }
  }

  function setPage(n) {
    const normalized = Number(n)
    page.value =
      Number.isFinite(normalized) && normalized >= 1 ? Math.floor(normalized) : 1
    return fetch()
  }

  function setSort(field, order) {
    sort.value = {
      field: field || DEFAULT_SORT_FIELD,
      order: order === 'asc' ? 'asc' : 'desc'
    }
    page.value = 1
    return fetch()
  }

  function setKeyword(k) {
    keyword.value = k ?? ''
    page.value = 1
    return fetch()
  }

  function setFilters(obj) {
    filters.value = obj && typeof obj === 'object' ? { ...obj } : {}
    page.value = 1
    return fetch()
  }

  function resetFilters() {
    filters.value = {}
    keyword.value = ''
    page.value = 1
    return fetch()
  }

  watch(
    range,
    () => {
      if (rangeDebounceTimer != null) {
        clearTimeout(rangeDebounceTimer)
      }
      rangeDebounceTimer = setTimeout(() => {
        rangeDebounceTimer = null
        if (unmounted) return
        page.value = 1
        fetch()
      }, RANGE_DEBOUNCE_MS)
    },
    { deep: true, immediate: true }
  )

  onUnmounted(() => {
    unmounted = true
    fetchGeneration += 1
    if (rangeDebounceTimer != null) {
      clearTimeout(rangeDebounceTimer)
      rangeDebounceTimer = null
    }
  })

  return {
    loading,
    error,
    errorCode,
    items,
    total,
    tookMs,
    hasMore,
    page,
    pageSize,
    sort,
    keyword,
    filters,
    fetch,
    setPage,
    setSort,
    setKeyword,
    setFilters,
    resetFilters
  }
}

/** 将 payload 中的专有字段提升到行顶层，便于表格渲染 */
function enrichLogRow(item) {
  if (!item || typeof item !== 'object') return item
  const payload = item.payload && typeof item.payload === 'object' ? item.payload : {}
  return {
    ...payload,
    ...item,
    payload
  }
}
