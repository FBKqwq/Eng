<template>
  <div class="log-monitor-shell">
    <!-- 类型页头 -->
    <header class="monitor-page-header">
      <div class="monitor-page-header__main">
        <h2 class="monitor-page-header__title">{{ meta.title }}</h2>
        <p class="monitor-page-header__desc">{{ meta.pageDescription }}</p>
      </div>
      <dl class="monitor-page-header__stats">
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

    <!-- 查询摘要条 + 活跃筛选 chip -->
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

    <!-- 筛选命令区 -->
    <section class="page-section monitor-section">
      <DynamicFilterBar
        :log-type="meta.logType"
        v-model="draftFilters"
        v-model:keyword="draftKeyword"
        @catalog-fallback="catalogFallback = $event"
      />
    </section>

    <!-- 重点图表带 -->
    <section class="page-section monitor-section">
      <ChartBand
        :chart-templates="meta.chartTemplates"
        :log-type="meta.logType"
        :primary-chart-id="meta.primaryChartId"
        :filters="filters"
      />
    </section>

    <!-- 明细表 -->
    <section class="page-section monitor-section log-monitor-shell__detail">
      <LogTable
        :columns="tableColumns"
        :items="items"
        :total="total"
        :page="page"
        :page-size="pageSize"
        :loading="loading"
        :error="error || ''"
        :sort="sort"
        :log-type="meta.logType"
        :drillable-fields="meta.drillableFields"
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
import { computed, ref, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DynamicFilterBar from './DynamicFilterBar.vue'
import ChartBand from './ChartBand.vue'
import LogTable from '../common/LogTable.vue'
import { useLogQuery } from '../../composables/useLogQuery.js'
import { useTimeRange } from '../../composables/useTimeRange.js'
import { buildActiveFilterChips } from '../../utils/logQueryContract.js'
import { resolveMonitorColumns } from '../../utils/logTypeMeta.js'
import { formatNumber } from '../../utils/format.js'

const FILTER_DEBOUNCE_MS = 300

const props = defineProps({
  meta: { type: Object, required: true }
})

const route = useRoute()
const router = useRouter()
const { preset, range, presets } = useTimeRange()
const catalogFallback = ref(false)

function parseRoutePreset(query) {
  const presetFilters = {}
  let presetKeyword = ''

  if (query.keyword) presetKeyword = String(query.keyword)

  const arrayKeys = [
    'log_levels',
    'error_codes',
    'service_names',
    'event_types',
    'envs',
    'statuses',
    'status_codes',
    'tags'
  ]
  for (const key of arrayKeys) {
    const raw = query[key]
    if (!raw) continue
    const values = String(raw)
      .split(',')
      .map((entry) => entry.trim())
      .filter(Boolean)
    if (values.length) presetFilters[key] = values
  }

  if (query.trace_id) presetFilters.trace_id = String(query.trace_id)
  if (query.user_id) presetFilters.user_id = String(query.user_id)

  return { filters: presetFilters, keyword: presetKeyword }
}

const routePreset = parseRoutePreset(route.query)

const {
  loading,
  error,
  items,
  total,
  tookMs,
  page,
  pageSize,
  sort,
  filters,
  keyword,
  fetch,
  setPage,
  setSort
} = useLogQuery(props.meta.logType, props.meta.defaultSort)

const draftFilters = ref({ ...routePreset.filters })
const draftKeyword = ref(routePreset.keyword)

if (Object.keys(routePreset.filters).length || routePreset.keyword) {
  filters.value = { ...routePreset.filters }
  keyword.value = routePreset.keyword
}

let filterDebounceTimer = null

const tableColumns = computed(() => resolveMonitorColumns(props.meta))

const activeChips = computed(() => buildActiveFilterChips(draftFilters.value, draftKeyword.value))

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

function scheduleFilterFetch() {
  if (filterDebounceTimer != null) clearTimeout(filterDebounceTimer)
  filterDebounceTimer = setTimeout(() => {
    filterDebounceTimer = null
    filters.value = { ...draftFilters.value }
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

onUnmounted(() => {
  if (filterDebounceTimer != null) {
    clearTimeout(filterDebounceTimer)
    filterDebounceTimer = null
  }
})
</script>

<style scoped>
.log-monitor-shell {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.monitor-page-header {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  padding-left: 30px;
  border: 1px solid #111827;
  border-radius: 0;
  background: var(--color-surface);
  box-shadow: 6px 6px 0 rgba(15, 23, 42, 0.08);
}

.monitor-page-header::before {
  position: absolute;
  inset: 0 auto 0 0;
  width: 18px;
  background: #111827;
  clip-path: polygon(0 0, 100% 0, 58% 100%, 0 100%);
  content: '';
}

.monitor-page-header__title {
  margin: 0 0 4px;
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text);
}

.monitor-page-header__desc {
  margin: 0;
  max-width: 720px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--color-text-secondary);
}

.monitor-page-header__stats {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  margin: 0;
}

.stat-item {
  min-width: 88px;
  padding-left: 10px;
  border-left: 2px solid #111827;
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
  border: 1px dashed #64748b;
  border-radius: 0;
  background: #f8fafc;
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
  border-radius: 0;
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

.monitor-section {
  margin-bottom: 0;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.monitor-section:hover {
  border-color: transparent;
  box-shadow: none;
  transform: none;
}

.log-monitor-shell__detail {
  min-width: 0;
}

@media (max-width: 640px) {
  .monitor-page-header__stats {
    width: 100%;
  }
}
</style>
