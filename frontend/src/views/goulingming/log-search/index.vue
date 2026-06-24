<template>
  <div class="log-search-page">
    <!-- 页头 -->
    <header class="page-header">
      <div class="page-header__main">
        <h2 class="page-header__title">业务日志全文检索</h2>
        <p class="page-header__desc">
          基于业务域的日志全文检索，支持时间窗联动、筛选与钻取。
        </p>
      </div>
      <dl class="page-header__stats">
        <div class="stat-item">
          <dt>时间窗</dt>
          <dd>{{ timeRangeLabel }}</dd>
        </div>
        <div class="stat-item">
          <dt>命中总量</dt>
          <dd class="tabular-nums">{{ loading && !total ? '…' : formatNumber(total) }}</dd>
        </div>
        <div class="stat-item">
          <dt>查询耗时</dt>
          <dd class="tabular-nums">{{ tookLabel }}</dd>
        </div>
      </dl>
    </header>

    <!-- 活跃筛选标签 -->
    <section class="query-summary" aria-label="查询摘要">
      <div class="query-summary__chips">
        <span v-if="!activeChips.length && !keyword" class="query-summary__empty">未应用筛选条件</span>
        <button
          v-for="chip in activeChips"
          :key="chip.key"
          type="button"
          class="filter-chip"
          :aria-label="`清除 ${chip.label}`"
          @click="clearChip(chip.key)"
        >
          <span class="filter-chip__label">{{ chip.label }}</span>
          <span class="filter-chip__value">{{ chip.display }}</span>
          <span class="filter-chip__close" aria-hidden="true">×</span>
        </button>
      </div>
      <button
        v-if="activeChips.length"
        type="button"
        class="query-summary__clear"
        @click="clearAllFilters"
      >
        清除全部
      </button>
    </section>

    <!-- 筛选区 -->
    <section class="page-section">
      <DynamicFilterBar
        log-type="application"
        v-model="draftFilters"
        v-model:keyword="draftKeyword"
        @catalog-fallback="catalogFallback = $event"
      />
    </section>

    <!-- 日志明细表 -->
    <section class="page-section log-search-page__table">
      <LogTable
        :columns="tableColumns"
        :items="items"
        :total="total"
        :page="page"
        :page-size="pageSize"
        :loading="loading"
        :error="error || ''"
        :sort="sort"
        log-type="application"
        :drillable-fields="drillableFields"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
        @sort-change="handleSortChange"
        @trace-navigate="handleTraceNavigate"
        @drill="handleDrill"
        @retry="fetch"
      />
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DynamicFilterBar from '../../../components/monitor/DynamicFilterBar.vue'
import LogTable from '../../../components/common/LogTable.vue'
import { useGoulingmingLogSearch } from '../../../composables/useGoulingmingLogSearch.js'
import { useTimeRange } from '../../../composables/useTimeRange.js'
import { buildActiveFilterChips } from '../../../utils/logQueryContract.js'
import { formatNumber } from '../../../utils/format.js'

const route = useRoute()
const router = useRouter()
const FILTER_DEBOUNCE_MS = 300

const { preset, range, presets, setCustomRange } = useTimeRange()

const {
  loading,
  error,
  items,
  total,
  tookMs,
  page,
  pageSize,
  sort,
  keyword,
  fetch,
  setPage,
  setSort,
  setFilters,
  resetAll
} = useGoulingmingLogSearch()

const draftFilters = ref({})
const draftKeyword = ref('')
const catalogFallback = ref(false)

const tableColumns = [
  { label: '时间', key: 'timestamp', renderType: 'timestamp', sortable: true, width: '168px' },
  { label: '级别', key: 'log_level', renderType: 'log_level', sortable: true, width: '88px' },
  { label: '服务', key: 'service_name', renderType: 'text', sortable: true },
  { label: '接口', key: 'request_path', renderType: 'copyable' },
  { label: '状态码', key: 'status_code', renderType: 'http_status', sortable: true, width: '88px' },
  { label: '耗时', key: 'response_time_ms', renderType: 'duration', sortable: true, width: '88px', unit: 'ms' },
  { label: '错误码', key: 'error_code', renderType: 'text' },
  { label: '链路', key: 'trace_id', renderType: 'trace', drillable: true, drillTarget: 'trace', width: '120px' }
]

const drillableFields = ['trace_id', 'user_id', 'request_path']

const activeChips = computed(() =>
  buildActiveFilterChips(draftFilters.value, draftKeyword.value)
)

const timeRangeLabel = computed(() => {
  const item = presets.find((p) => p.value === preset.value)
  if (preset.value !== 'custom') return item?.label || '近 1 小时'
  const start = new Date(range.value.start).toLocaleString('zh-CN', { hour12: false })
  const end = new Date(range.value.end).toLocaleString('zh-CN', { hour12: false })
  return `${start} — ${end}`
})

const tookLabel = computed(() => {
  if (loading.value && tookMs.value == null) return '查询中…'
  if (tookMs.value == null) return '—'
  return `${tookMs.value} ms`
})

let filterDebounceTimer = null

/** 解析来自业务漏斗/其他页面的预设 query，跳过未提供的字段 */
function applyRouteQuery() {
  const q = route.query || {}
  if (typeof q.keyword === 'string' && q.keyword) {
    draftKeyword.value = q.keyword
  }
  const from = Number(q.from)
  const to = Number(q.to)
  if (Number.isFinite(from) && Number.isFinite(to) && to > from) {
    setCustomRange(from, to)
  }
}

onMounted(() => {
  applyRouteQuery()
  // 同步到搜索 composable，立刻触发一次查询
  setFilters(draftFilters.value)
  keyword.value = draftKeyword.value
  page.value = 1
  fetch()
})

function scheduleFilterFetch() {
  if (filterDebounceTimer != null) clearTimeout(filterDebounceTimer)
  filterDebounceTimer = setTimeout(() => {
    filterDebounceTimer = null
    setFilters(draftFilters.value)
    keyword.value = draftKeyword.value
    page.value = 1
    fetch()
  }, FILTER_DEBOUNCE_MS)
}

watch(draftFilters, scheduleFilterFetch, { deep: true })
watch(draftKeyword, scheduleFilterFetch)

function clearChip(key) {
  if (key === 'keyword') {
    draftKeyword.value = ''
    return
  }
  const next = { ...draftFilters.value }
  delete next[key]
  draftFilters.value = next
}

function clearAllFilters() {
  draftFilters.value = {}
  draftKeyword.value = ''
  resetAll()
}

function handlePageChange(nextPage) {
  setPage(nextPage)
}

function handlePageSizeChange(nextSize) {
  const normalized = Number(nextSize)
  if (!Number.isFinite(normalized) || normalized < 1) return
  pageSize.value = normalized
  setPage(1)
}

function handleSortChange({ field, order }) {
  setSort(field, order)
}

function handleTraceNavigate(traceId) {
  if (!traceId) return
  router.push({ path: '/analysis/trace', query: { trace_id: traceId } })
}

function handleDrill({ target, value }) {
  if (!value) return
  if (target === 'trace') {
    handleTraceNavigate(value)
    return
  }
  if (target === 'user') {
    draftFilters.value = { ...draftFilters.value, user_id: String(value) }
    return
  }
  if (target === 'keyword') {
    draftKeyword.value = String(value)
  }
}
</script>

<style scoped>
.log-search-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.page-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.page-header__title {
  margin: 0 0 4px;
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text);
}

.page-header__desc {
  margin: 0;
  max-width: 640px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--color-text-secondary);
}

.page-header__stats {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  margin: 0;
}

.stat-item {
  min-width: 88px;
}

.stat-item dt {
  margin: 0 0 2px;
  font-size: 11px;
  color: var(--color-text-muted);
}

.stat-item dd {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.query-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: 10px var(--spacing-md);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-subtle);
}

.query-summary__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.query-summary__empty {
  font-size: 12px;
  color: var(--color-text-muted);
}

.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  padding: 4px 8px 4px 10px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface);
  font-size: 12px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: border-color var(--transition-fast), color var(--transition-fast);
}

.filter-chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.filter-chip__label {
  color: var(--color-text-muted);
}

.filter-chip__value {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 180px;
  color: var(--color-text);
}

.filter-chip__close {
  font-size: 14px;
  line-height: 1;
}

.query-summary__clear {
  flex-shrink: 0;
  padding: 4px 10px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-primary);
  font-size: 12px;
  cursor: pointer;
}

.page-section {
  margin-bottom: 0;
}

.log-search-page__table {
  min-width: 0;
}

@media (max-width: 640px) {
  .page-header__stats {
    width: 100%;
  }
}
</style>
