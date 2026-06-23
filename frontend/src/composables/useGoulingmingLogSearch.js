/**
 * Goulingming 日志检索状态机：
 * - 时间窗联动 useTimeRange（全局共享）
 * - 筛选 + 关键字 + 分页 + 排序
 * - 透传 searchGoulingmingLogs（内部调用 /logs/search）
 */
import { ref, watch, onUnmounted } from 'vue'
import { useTimeRange } from './useTimeRange.js'
import { searchGoulingmingLogs } from '../api/goulingming.js'

const DEFAULT_PAGE_SIZE = 20
const DEFAULT_SORT_FIELD = 'timestamp'
const DEFAULT_SORT_ORDER = 'desc'
const RANGE_DEBOUNCE_MS = 300

export function useGoulingmingLogSearch() {
  const { range } = useTimeRange()

  const loading = ref(false)
  const error = ref(null)
  const items = ref([])
  const total = ref(0)
  const tookMs = ref(null)
  const page = ref(1)
  const pageSize = ref(DEFAULT_PAGE_SIZE)
  const sort = ref({ field: DEFAULT_SORT_FIELD, order: DEFAULT_SORT_ORDER })
  const keyword = ref('')
  const filters = ref({})

  let fetchGeneration = 0
  let unmounted = false
  let rangeDebounceTimer = null

  function buildPayload() {
    return {
      start_time: new Date(range.value.start).toISOString(),
      end_time: new Date(range.value.end).toISOString(),
      page: page.value,
      page_size: pageSize.value,
      sort_by: sort.value.field,
      sort_order: sort.value.order === 'asc' ? 'asc' : 'desc',
      keyword: keyword.value || undefined,
      ...filters.value
    }
  }

  async function fetch() {
    if (unmounted) return
    const generation = ++fetchGeneration
    loading.value = true
    error.value = null

    try {
      const res = await searchGoulingmingLogs(buildPayload())
      if (unmounted || generation !== fetchGeneration) return
      items.value = (res.data?.items ?? []).map(enrichRow)
      total.value = res.data?.total ?? 0
      tookMs.value = res.data?.took_ms ?? null
    } catch (e) {
      if (unmounted || generation !== fetchGeneration) return
      error.value = e.message ?? '查询失败'
      items.value = []
      total.value = 0
    } finally {
      if (!unmounted && generation === fetchGeneration) {
        loading.value = false
      }
    }
  }

  function setPage(n) {
    const normalized = Math.floor(Number(n))
    page.value = Number.isFinite(normalized) && normalized >= 1 ? normalized : 1
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

  function resetAll() {
    filters.value = {}
    keyword.value = ''
    page.value = 1
    return fetch()
  }

  watch(
    range,
    () => {
      if (rangeDebounceTimer != null) clearTimeout(rangeDebounceTimer)
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
    items,
    total,
    tookMs,
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
    resetAll
  }
}

function enrichRow(item) {
  if (!item || typeof item !== 'object') return item
  const payload = item.payload && typeof item.payload === 'object' ? item.payload : {}
  return { ...payload, ...item, payload }
}
