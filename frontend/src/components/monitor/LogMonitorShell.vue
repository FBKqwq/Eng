<template>
  <div class="log-monitor-shell">
    <section class="page-section">
      <DynamicFilterBar
        :log-type="logType"
        v-model="draftFilters"
        v-model:keyword="draftKeyword"
      />
    </section>

    <section class="page-section">
      <ChartBand :chart-templates="chartTemplates" :log-type="logType" />
    </section>

    <section class="page-section log-monitor-shell__detail">
      <LogTable
        :columns="tableColumns"
        :items="items"
        :total="total"
        :page="page"
        :page-size="pageSize"
        :loading="loading"
        :error="error || ''"
        :sort="sort"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
        @sort-change="handleSortChange"
        @trace-navigate="handleTraceNavigate"
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

const FILTER_DEBOUNCE_MS = 300

/** 展示列标签 → API 字段键（对齐总体规划 §3.2 与 LogSearchItem） */
const COLUMN_LABEL_KEYS = {
  时间: { key: 'timestamp', sortable: true, width: '168px' },
  级别: { key: 'log_level', sortable: true, width: '88px' },
  服务: { key: 'service_name', sortable: true },
  接口: { key: 'request_path' },
  状态码: { key: 'status_code', sortable: true, width: '88px' },
  耗时: { key: 'duration_ms', sortable: true, width: '88px' },
  错误码: { key: 'error_code' },
  用户: { key: 'user_id' },
  action: { key: 'action' },
  页面: { key: 'page' },
  商品: { key: 'product_name' },
  停留时长: { key: 'stay_duration', sortable: true, width: '96px' },
  URI: { key: 'request_uri' },
  upstream: { key: 'upstream_addr' },
  UA: { key: 'user_agent' },
  指标名: { key: 'metric_name' },
  指标值: { key: 'metric_value', sortable: true },
  主机: { key: 'host' },
  事件类型: { key: 'event_type' },
  风险级: { key: 'risk_level', width: '88px' },
  IP: { key: 'client_ip' },
  规则: { key: 'rule_name' },
  组件: { key: 'component' },
  资源类型: { key: 'resource_type' },
  状态: { key: 'status', width: '80px' },
  详情: { key: 'summary' },
  操作人: { key: 'operator_name' },
  操作: { key: 'action' },
  对象: { key: 'target' },
  变更前后值: { key: 'change_detail' }
}

const FALLBACK_COLUMNS = [
  { key: 'timestamp', label: '时间', sortable: true, width: '168px' },
  { key: 'log_level', label: '级别', sortable: true, width: '88px' },
  { key: 'service_name', label: '服务', sortable: true },
  { key: 'message', label: '消息' }
]

const props = defineProps({
  logType: { type: String, required: true },
  chartTemplates: { type: Array, default: () => [] },
  defaultColumns: { type: Array, default: () => [] }
})

const route = useRoute()
const router = useRouter()

/** 路由 query 预置筛选（漏斗跳转等）：逗号分隔数组字段、单值 keyword/trace_id */
function parseRoutePreset(query) {
  const presetFilters = {}
  let presetKeyword = ''

  if (query.keyword) {
    presetKeyword = String(query.keyword)
  }

  const arrayKeys = ['log_levels', 'error_codes', 'service_names', 'event_types', 'envs', 'statuses']
  for (const key of arrayKeys) {
    const raw = query[key]
    if (!raw) continue
    const values = String(raw)
      .split(',')
      .map((entry) => entry.trim())
      .filter(Boolean)
    if (values.length) presetFilters[key] = values
  }

  if (query.trace_id) {
    presetFilters.trace_id = String(query.trace_id)
  }

  return { filters: presetFilters, keyword: presetKeyword }
}

const routePreset = parseRoutePreset(route.query)

const {
  loading,
  error,
  items,
  total,
  page,
  pageSize,
  sort,
  filters,
  keyword,
  fetch,
  setPage,
  setSort
} = useLogQuery(props.logType)

const draftFilters = ref({ ...routePreset.filters })
const draftKeyword = ref(routePreset.keyword)

if (Object.keys(routePreset.filters).length || routePreset.keyword) {
  filters.value = { ...routePreset.filters }
  keyword.value = routePreset.keyword
}

let filterDebounceTimer = null

const tableColumns = computed(() => buildColumns(props.defaultColumns))

function buildColumns(labels) {
  if (!labels?.length) return FALLBACK_COLUMNS
  return labels.map((label) => {
    const spec = COLUMN_LABEL_KEYS[label]
    if (spec) {
      return { label, ...spec }
    }
    return {
      key: label,
      label,
      sortable: label === 'timestamp' || label === '@timestamp'
    }
  })
}

function scheduleFilterFetch() {
  if (filterDebounceTimer != null) {
    clearTimeout(filterDebounceTimer)
  }
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
  router.push({
    path: '/analysis/trace',
    query: { trace_id: traceId }
  })
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

.log-monitor-shell__detail {
  margin-bottom: 0;
}
</style>
