<template>
  <div class="trace-page">
    <header class="trace-page__header">
      <div class="header-info">
        <h2 class="header-title">预警推理链路</h2>
        <p class="header-desc">展示来自预警中心与诊断分析的推理链路轨迹，按严重程度排序</p>
      </div>
      <div class="header-stats">
        <span class="stat-pill">
          <span class="stat-pill__dot dot--danger" />
          {{ pendingCount }} 待确认
        </span>
        <span class="stat-pill">
          <span class="stat-pill__dot dot--success" />
          {{ successfulCount }} 已确认
        </span>
      </div>
    </header>

    <!-- 搜索过滤栏 -->
    <div class="trace-page__filters">
      <div class="filter-search">
        <svg class="filter-search__icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          v-model="searchText"
          type="search"
          class="filter-search__input"
          placeholder="搜索预警标题、服务、ID…"
          aria-label="搜索预警链路"
        />
        <button
          v-if="searchText"
          type="button"
          class="filter-search__clear"
          aria-label="清除搜索"
          @click="searchText = ''"
        >×</button>
      </div>

      <div class="filter-group" role="group" aria-label="严重程度筛选">
        <button
          v-for="s in SEVERITY_OPTIONS"
          :key="s.value"
          type="button"
          class="filter-chip"
          :class="{ active: activeSeverities.has(s.value) }"
          @click="toggleSeverity(s.value)"
        >{{ s.label }}</button>
      </div>

      <div class="filter-group" role="group" aria-label="状态筛选">
        <button
          v-for="s in STATUS_OPTIONS"
          :key="s.value"
          type="button"
          class="filter-chip"
          :class="{ active: activeStatuses.has(s.value) }"
          @click="toggleStatus(s.value)"
        >{{ s.label }}</button>
      </div>

      <button
        v-if="hasActiveFilters"
        type="button"
        class="filter-reset"
        @click="resetFilters"
      >重置</button>

      <span class="filter-count">{{ filteredAll.length }} 条</span>
    </div>

    <div
      v-if="loading && !filteredAll.length"
      class="trace-page__status trace-page__status--loading"
      role="status"
      aria-live="polite"
    >
      正在加载预警链路…
    </div>

    <EmptyState
      v-else-if="!filteredAll.length"
      :title="hasActiveFilters ? '无匹配结果' : '暂无预警链路'"
      :description="hasActiveFilters ? '调整筛选条件后再试' : '预警中心产生预警后，对应的推理链路将在此自动展示'"
    />

    <template v-else>
      <section class="trace-page__section" v-if="filteredPending.length">
        <header class="section-header">
          <div class="section-header__left">
            <span class="section-dot dot--danger" />
            <h3>待确认预警</h3>
            <span class="section-count tabular-nums">{{ filteredPending.length }} 条</span>
          </div>
          <span class="section-hint">严重程度 Top 10</span>
        </header>
        <div class="trace-grid">
          <AlertTracePanel
            v-for="trace in filteredPending"
            :key="trace.alertId"
            :trace="trace"
            @click="openTraceDetail(trace)"
          />
        </div>
      </section>

      <section class="trace-page__section" v-if="filteredSuccessful.length">
        <header class="section-header">
          <div class="section-header__left">
            <span class="section-dot dot--success" />
            <h3>已确认预警链路</h3>
            <span class="section-count tabular-nums">{{ filteredSuccessful.length }} 条</span>
          </div>
          <span class="section-hint">按时间倒序</span>
        </header>
        <div class="trace-grid">
          <AlertTracePanel
            v-for="trace in filteredSuccessful"
            :key="trace.alertId"
            :trace="trace"
            :degraded="trace.degraded"
            @click="openTraceDetail(trace)"
          />
        </div>
      </section>
    </template>

    <TraceDetailDrawer
      :visible="drawerVisible"
      :trace="selectedTrace"
      @close="closeDrawer"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import EmptyState from '../../components/common/EmptyState.vue'
import AlertTracePanel from '../../components/analysis-trace/AlertTracePanel.vue'
import TraceDetailDrawer from '../../components/analysis-trace/TraceDetailDrawer.vue'
import { getActiveAlerts } from '../../api/alerts.js'
import { USE_MOCK as ALERTS_MOCK } from '../../api/alerts.js'
import { USE_MOCK as ANALYSIS_MOCK } from '../../api/analysis.js'

const loading = ref(false)
const allTraces = ref([])
const selectedTrace = ref(null)
const drawerVisible = ref(false)

const searchText = ref('')
const activeSeverities = ref(new Set(['critical', 'high', 'medium', 'low']))
const activeStatuses = ref(new Set(['active', 'acknowledged', 'resolved']))

const SEVERITY_OPTIONS = [
  { value: 'critical', label: '严重' },
  { value: 'high', label: '高危' },
  { value: 'medium', label: '中危' },
  { value: 'low', label: '低危' }
]

const STATUS_OPTIONS = [
  { value: 'active', label: '待确认' },
  { value: 'acknowledged', label: '已确认' },
  { value: 'resolved', label: '已解决' }
]

const SEVERITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 }

function toggleSeverity(val) {
  const next = new Set(activeSeverities.value)
  if (next.has(val)) {
    if (next.size > 1) next.delete(val)
  } else {
    next.add(val)
  }
  activeSeverities.value = next
}

function toggleStatus(val) {
  const next = new Set(activeStatuses.value)
  if (next.has(val)) {
    if (next.size > 1) next.delete(val)
  } else {
    next.add(val)
  }
  activeStatuses.value = next
}

function resetFilters() {
  searchText.value = ''
  activeSeverities.value = new Set(['critical', 'high', 'medium', 'low'])
  activeStatuses.value = new Set(['active', 'acknowledged', 'resolved'])
}

const hasActiveFilters = computed(() => {
  return (
    searchText.value.trim() !== '' ||
    activeSeverities.value.size < 4 ||
    activeStatuses.value.size < 3
  )
})

function buildNodeTrace() {
  return [
    { node_name: 'fetch_context', status: 'success', duration_ms: 820 },
    { node_name: 'correlate_events', status: 'success', duration_ms: 560 },
    { node_name: 'infer_root_cause', status: 'success', duration_ms: 340 },
    { node_name: 'assess_severity', status: 'success', duration_ms: 125 },
    { node_name: 'generate_event_report', status: 'success', duration_ms: 210 }
  ]
}

async function loadTraces() {
  loading.value = true

  if (ALERTS_MOCK || ANALYSIS_MOCK) {
    allTraces.value = [
      { alertId: 'a001', title: 'order-service 超时异常', alert_type: 'service_timeout', service: 'order-service', severity: 'critical', status: 'active', created_at: new Date(Date.now() - 1800000).toISOString(), node_trace: buildNodeTrace(), degraded: false },
      { alertId: 'a002', title: 'payment 错误率激增', alert_type: 'error_rate_spike', service: 'payment-service', severity: 'high', status: 'active', created_at: new Date(Date.now() - 3600000).toISOString(), node_trace: buildNodeTrace(), degraded: false },
      { alertId: 'a003', title: 'gateway 延迟劣化', alert_type: 'latency_degradation', service: 'gateway', severity: 'medium', status: 'acknowledged', created_at: new Date(Date.now() - 7200000).toISOString(), node_trace: buildNodeTrace(), degraded: true },
      { alertId: 'a004', title: 'inventory 响应超时', alert_type: 'service_timeout', service: 'inventory-service', severity: 'low', status: 'resolved', created_at: new Date(Date.now() - 14400000).toISOString(), node_trace: buildNodeTrace(), degraded: false },
      { alertId: 'a005', title: 'user-service 认证异常', alert_type: 'security_risk', service: 'user-service', severity: 'high', status: 'acknowledged', created_at: new Date(Date.now() - 5400000).toISOString(), node_trace: buildNodeTrace(), degraded: false }
    ]
    loading.value = false
    return
  }

  try {
    const res = await getActiveAlerts({ limit: 50 })
    const items = res.data?.items ?? []
    allTraces.value = items.map((item) => ({
      alertId: item.alert_id,
      title: item.title || item.alert_type || '预警链路',
      alert_type: item.alert_type,
      service: item.affected_service || '全局',
      severity: item.severity || 'medium',
      status: item.status || 'active',
      created_at: item.created_at,
      node_trace: item.node_trace || buildNodeTrace(),
      degraded: Boolean(item.degraded)
    }))
  } catch {
    allTraces.value = []
  } finally {
    loading.value = false
  }
}

const pendingTraces = computed(() =>
  [...allTraces.value]
    .filter((t) => t.status === 'active')
    .sort((a, b) => (SEVERITY_ORDER[a.severity] ?? 4) - (SEVERITY_ORDER[b.severity] ?? 4))
    .slice(0, 10)
)

const successfulTraces = computed(() =>
  [...allTraces.value]
    .filter((t) => ['acknowledged', 'resolved'].includes(t.status))
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 10)
)

const filteredAll = computed(() => {
  const q = searchText.value.trim().toLowerCase()
  return allTraces.value.filter((t) => {
    if (!activeSeverities.value.has(t.severity)) return false
    if (!activeStatuses.value.has(t.status)) return false
    if (q) {
      return (
        (t.title || '').toLowerCase().includes(q) ||
        (t.service || '').toLowerCase().includes(q) ||
        (t.alertId || '').toLowerCase().includes(q) ||
        (t.alert_type || '').toLowerCase().includes(q)
      )
    }
    return true
  })
})

const filteredPending = computed(() =>
  filteredAll.value
    .filter((t) => t.status === 'active')
    .sort((a, b) => (SEVERITY_ORDER[a.severity] ?? 4) - (SEVERITY_ORDER[b.severity] ?? 4))
    .slice(0, 10)
)

const filteredSuccessful = computed(() =>
  filteredAll.value
    .filter((t) => ['acknowledged', 'resolved'].includes(t.status))
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 10)
)

const pendingCount = computed(() => pendingTraces.value.length)
const successfulCount = computed(() => successfulTraces.value.length)

function openTraceDetail(trace) {
  selectedTrace.value = trace
  drawerVisible.value = true
}

function closeDrawer() {
  drawerVisible.value = false
  selectedTrace.value = null
}

onMounted(() => {
  loadTraces()
})
</script>

<style scoped>
.trace-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.trace-page__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.header-title {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text);
}

.header-desc {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-muted);
}

.header-stats {
  display: flex;
  gap: var(--spacing-sm);
}

.stat-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface);
  font-size: 12px;
  color: var(--color-text-secondary);
}

.stat-pill__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.trace-page__status {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  font-size: 13px;
}

.trace-page__status--loading {
  border: 1px solid var(--color-border);
  background: var(--color-info-bg);
  color: var(--color-text-secondary);
}

.trace-page__section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-header__left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.section-header h3 {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text);
}

.section-count {
  padding: 1px 8px;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  font-size: 11px;
  color: var(--color-text-muted);
}

.section-hint {
  font-size: 12px;
  color: var(--color-text-muted);
}

.trace-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: var(--spacing-sm);
}

.trace-grid > * {
  cursor: pointer;
}

/* 搜索过滤栏 */
.trace-page__filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  padding: 10px var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.filter-search {
  position: relative;
  display: flex;
  align-items: center;
}

.filter-search__icon {
  position: absolute;
  left: 10px;
  color: var(--color-text-muted);
  pointer-events: none;
}

.filter-search__input {
  min-height: 34px;
  width: 240px;
  padding: 6px 30px 6px 32px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text);
  font-size: 13px;
  outline: none;
  transition: border-color var(--transition-fast);
}

.filter-search__input::placeholder {
  color: var(--color-text-muted);
}

.filter-search__input:focus {
  border-color: var(--color-primary);
  background: var(--color-surface);
}

/* 清除搜索按钮 */
.filter-search__clear {
  position: absolute;
  right: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 4px;
  background: var(--color-border);
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
}

.filter-search__clear:hover {
  background: var(--color-border-strong);
}

/* 过滤 Chip 组 */
.filter-group {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.filter-chip {
  padding: 4px 10px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition:
    color var(--transition-fast),
    border-color var(--transition-fast),
    background var(--transition-fast);
}

.filter-chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.filter-chip.active {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: 600;
}

/* 重置按钮 */
.filter-reset {
  padding: 4px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  font-size: 12px;
  cursor: pointer;
  transition: color var(--transition-fast);
}

.filter-reset:hover {
  color: var(--color-danger);
  border-color: var(--color-danger);
}

/* 结果计数 */
.filter-count {
  margin-left: auto;
  font-size: 12px;
  color: var(--color-text-muted);
}
</style>
