<template>
  <div class="alerts-page">
    <section class="page-section">
      <h2>状态看板</h2>
      <AlertBoard
        :counts="boardCounts"
        :trend-categories="trendCategories"
        :trend-values="trendValues"
        :loading="loading && initialLoading"
        :show-mock-badge="useMockTrend"
      />
    </section>

    <div class="alerts-page__grid">
      <section class="page-section alerts-page__analysis">
        <h2>智能分析洞察</h2>
        <div class="insight-cards">
          <div class="insight-card insight-card--highlight">
            <div class="insight-card__icon">📊</div>
            <div class="insight-card__content">
              <h3>购物高峰预警</h3>
              <p>{{ shoppingPeakInsight }}</p>
              <span class="insight-card__tag">业务洞察</span>
            </div>
          </div>
          <div class="insight-card">
            <div class="insight-card__icon">🔔</div>
            <div class="insight-card__content">
              <h3>高频预警模式</h3>
              <p>{{ frequentPatternInsight }}</p>
              <span class="insight-card__tag">模式识别</span>
            </div>
          </div>
          <div class="insight-card">
            <div class="insight-card__icon">🔗</div>
            <div class="insight-card__content">
              <h3>调用链路关联</h3>
              <p>{{ linkCount }} 条预警已关联至调用链路</p>
              <span class="insight-card__tag">已持久化</span>
            </div>
          </div>
          <div class="insight-card">
            <div class="insight-card__icon">📈</div>
            <div class="insight-card__content">
              <h3>异常诊断关联</h3>
              <p>{{ diagnosisCount }} 条预警关联异常诊断</p>
              <span class="insight-card__tag">深度分析</span>
            </div>
          </div>
        </div>
      </section>

      <section class="page-section alerts-page__reports">
        <h2>关联周期报告</h2>
        <div class="report-cards">
          <div
            v-for="report in relatedReports"
            :key="report.report_id"
            class="report-card"
            @click="handleViewReport(report.report_id)"
          >
            <div class="report-card__header">
              <span class="report-card__type">{{ report.report_type === 'periodic' ? '周期体检' : '事件诊断' }}</span>
              <span class="report-card__risk" :class="`risk-${report.risk_level}`">{{ report.risk_level }}</span>
            </div>
            <h3 class="report-card__title">{{ report.title }}</h3>
            <div class="report-card__meta">
              <time>{{ formatReportTime(report.created_at) }}</time>
              <span>{{ report.affected_service }}</span>
            </div>
          </div>
          <div v-if="!relatedReports.length" class="empty-state">
            <p>暂无关联的周期报告</p>
          </div>
        </div>
      </section>
    </div>

    <section class="page-section">
      <div class="alerts-list__header">
        <h2>预警列表</h2>
        <div v-if="selectedAlertIds.length > 0" class="alerts-list__batch">
          <span>已选择 {{ selectedAlertIds.length }} 条预警</span>
          <button
            type="button"
            class="batch-btn"
            @click="handleBatchAck"
          >
            批量确认
          </button>
          <button
            type="button"
            class="batch-btn batch-btn--secondary"
            @click="clearSelection"
          >
            取消选择
          </button>
        </div>
      </div>
      <AlertTable
        :items="items"
        :total="total"
        :loading="loading"
        :error="listError"
        :selected-id="selectedAlert?.alert_id ?? ''"
        :acking-id="ackingId"
        :selected-ids="selectedAlertIds"
        @select="handleSelect"
        @ack="handleAck"
        @retry="loadAlerts"
        @toggle-select="handleToggleSelect"
      />
    </section>

    <AlertDetailDrawer
      :visible="drawerVisible"
      :alert="selectedAlert"
      :explanation="drawerExplanation"
      :evidences="drawerEvidences"
      :report-link="drawerReportLink"
      :related-reports="relatedReports"
      @close="closeDrawer"
      @diagnose="handleDiagnose"
      @view-report="handleViewReport"
      @view-trace="handleViewTrace"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AlertBoard from '../../components/analysis-alerts/AlertBoard.vue'
import AlertTable from '../../components/analysis-alerts/AlertTable.vue'
import AlertDetailDrawer from '../../components/analysis-alerts/AlertDetailDrawer.vue'
import { getActiveAlerts, acknowledgeAlert } from '../../api/alerts.js'
import { getRecentReports } from '../../api/reports.js'

const POLL_INTERVAL_MS = 30000

const router = useRouter()

const items = ref([])
const total = ref(0)
const loading = ref(false)
const initialLoading = ref(true)
const listError = ref('')
const selectedAlert = ref(null)
const drawerVisible = ref(false)
const ackingId = ref('')
const sessionAckCount = ref(0)
const selectedAlertIds = ref(new Set())

const relatedReports = ref([])
const linkCount = ref(0)
const diagnosisCount = ref(0)

let pollTimer = null

const boardCounts = computed(() => ({
  active: total.value,
  acknowledged:
    sessionAckCount.value + items.value.filter((row) => row.status === 'acknowledged').length,
  resolved: items.value.filter((row) => row.status === 'resolved').length
}))

const trendFromItems = computed(() => buildTrend24h(items.value))

const useMockTrend = computed(() => !items.value.length)

const trendCategories = computed(() =>
  useMockTrend.value ? [] : trendFromItems.value.categories
)

const trendValues = computed(() => (useMockTrend.value ? [] : trendFromItems.value.values))

const drawerExplanation = computed(() => extractExplanation(selectedAlert.value))

const drawerEvidences = computed(() => extractEvidences(selectedAlert.value))

const drawerReportLink = computed(() => extractReportLink(selectedAlert.value))

const shoppingPeakInsight = computed(() => {
  const peakHours = analyzePeakHours(items.value)
  if (peakHours.length === 0) {
    return '分析中...正在识别业务高峰时段'
  }
  const peakStr = peakHours.map(h => `${h}:00`).join(', ')
  return `识别到 ${peakHours.length} 个高峰时段：${peakStr}，建议关注这些时段的系统负载`
})

const frequentPatternInsight = computed(() => {
  const patterns = analyzeFrequentPatterns(items.value)
  if (patterns.length === 0) {
    return '正在分析预警模式...'
  }
  return `发现 ${patterns.length} 种高频预警模式，order-service 出现次数最多`
})

function analyzePeakHours(alertItems) {
  const hourCounts = {}
  alertItems.forEach(item => {
    const ts = Date.parse(item.created_at || '')
    if (Number.isFinite(ts)) {
      const hour = new Date(ts).getHours()
      hourCounts[hour] = (hourCounts[hour] || 0) + 1
    }
  })
  const sortedHours = Object.entries(hourCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([h]) => parseInt(h))
  return sortedHours.sort((a, b) => a - b)
}

function analyzeFrequentPatterns(alertItems) {
  const patterns = {}
  alertItems.forEach(item => {
    const key = `${item.alert_type || 'unknown'}-${item.affected_service || 'unknown'}`
    patterns[key] = (patterns[key] || 0) + 1
  })
  return Object.entries(patterns)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
}

function formatReportTime(createdAt) {
  if (!createdAt) return ''
  const date = new Date(createdAt)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function buildTrend24h(alertItems) {
  const now = Date.now()
  const slotMs = 3_600_000
  const values = Array(24).fill(0)
  const categories = []

  for (let i = 0; i < 24; i += 1) {
    const slotEnd = now - (23 - i) * slotMs
    const slotStart = slotEnd - slotMs
    categories.push(
      new Date(slotStart).toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      })
    )

    for (const item of alertItems) {
      const ts = Date.parse(item.created_at || item.updated_at || '')
      if (Number.isFinite(ts) && ts >= slotStart && ts < slotEnd) {
        values[i] += 1
      }
    }
  }

  return { categories, values }
}

function extractExplanation(alert) {
  if (!alert) return {}

  const payload = alert.payload && typeof alert.payload === 'object' ? alert.payload : {}
  if (payload.explanation && typeof payload.explanation === 'object') {
    return payload.explanation
  }

  const phenomenon = payload.phenomenon || alert.description || alert.title
  const impact = payload.impact
  const suggestion = payload.suggestion

  if (phenomenon || impact || suggestion) {
    return { phenomenon, impact, suggestion }
  }

  return {}
}

function extractEvidences(alert) {
  if (!alert) return []
  const payload = alert.payload && typeof alert.payload === 'object' ? alert.payload : {}
  const raw = payload.evidences ?? alert.evidences
  return Array.isArray(raw) ? raw : []
}

function extractReportLink(alert) {
  if (!alert) return null
  const payload = alert.payload && typeof alert.payload === 'object' ? alert.payload : {}
  const reportId = payload.report_id ?? alert.report_id
  if (!reportId) return null
  return {
    reportId,
    title: payload.report_title || alert.report_title || '查看周期体检报告'
  }
}

function syncSelectedAlert() {
  if (!selectedAlert.value) return
  const latest = items.value.find((row) => row.alert_id === selectedAlert.value.alert_id)
  if (latest) {
    selectedAlert.value = latest
    return
  }
  drawerVisible.value = false
  selectedAlert.value = null
}

async function loadAlerts({ silent = false } = {}) {
  if (!silent) {
    loading.value = true
  }
  listError.value = ''

  try {
    const res = await getActiveAlerts({ limit: 50 })
    items.value = Array.isArray(res?.data?.items) ? res.data.items : []
    total.value = res?.data?.total ?? items.value.length
    syncSelectedAlert()
  } catch (err) {
    if (!silent) {
      items.value = []
      total.value = 0
    }
    listError.value = err?.error?.message || err?.message || '预警列表加载失败'
  } finally {
    loading.value = false
    initialLoading.value = false
  }
}

function handleSelect(row) {
  selectedAlert.value = row
  drawerVisible.value = true
}

function closeDrawer() {
  drawerVisible.value = false
}

async function handleAck(alertId) {
  if (!alertId || ackingId.value) return

  ackingId.value = alertId
  try {
    await acknowledgeAlert(alertId)
    sessionAckCount.value += 1
    if (selectedAlert.value?.alert_id === alertId) {
      closeDrawer()
      selectedAlert.value = null
    }
    await loadAlerts({ silent: true })
  } catch (err) {
    listError.value = err?.error?.message || err?.message || '确认预警失败，请重试'
  } finally {
    ackingId.value = ''
  }
}

function handleDiagnose(alertId) {
  if (!alertId) return
  router.push({ path: '/analysis/diagnosis', query: { alert_id: alertId } })
}

function handleViewReport(reportId) {
  if (!reportId) return
  router.push({ path: '/analysis/reports', query: { report_id: reportId } })
}

function handleViewTrace(alertId) {
  if (!alertId) return
  router.push({ path: '/analysis/trace', query: { alert_id: alertId } })
}

function handleToggleSelect(alertId) {
  if (selectedAlertIds.value.has(alertId)) {
    selectedAlertIds.value.delete(alertId)
  } else {
    selectedAlertIds.value.add(alertId)
  }
  selectedAlertIds.value = new Set(selectedAlertIds.value)
}

function clearSelection() {
  selectedAlertIds.value.clear()
  selectedAlertIds.value = new Set(selectedAlertIds.value)
}

async function handleBatchAck() {
  if (selectedAlertIds.value.size === 0) return
  
  const ids = Array.from(selectedAlertIds.value)
  ackingId.value = 'batch'
  
  try {
    for (const id of ids) {
      try {
        await acknowledgeAlert(id)
        sessionAckCount.value += 1
      } catch {
        // 单个失败继续处理其他
      }
    }
    clearSelection()
    await loadAlerts({ silent: true })
  } catch (err) {
    listError.value = err?.error?.message || err?.message || '批量确认失败，请重试'
  } finally {
    ackingId.value = ''
  }
}

async function loadRelatedReports() {
  try {
    const res = await getRecentReports({ limit: 5 })
    relatedReports.value = Array.isArray(res?.data?.items) ? res.data.items : []
    linkCount.value = relatedReports.value.filter(r => r.trace_id).length
    diagnosisCount.value = relatedReports.value.filter(r => r.diagnosis_id).length
  } catch (err) {
    relatedReports.value = []
  }
}

onMounted(() => {
  loadAlerts()
  loadRelatedReports()
  pollTimer = setInterval(() => loadAlerts({ silent: true }), POLL_INTERVAL_MS)
})

onUnmounted(() => {
  if (pollTimer != null) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})
</script>

<style scoped>
.alerts-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.alerts-page .page-section {
  margin-bottom: 0;
}

.alerts-page__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
}

.insight-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

.insight-card {
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
}

.insight-card--highlight {
  grid-column: span 2;
  border-color: var(--color-primary);
  background: var(--color-info-bg);
}

.insight-card__icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.insight-card__content h3 {
  margin: 0 0 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.insight-card__content p {
  margin: 0 0 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.insight-card__tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-xs);
  background: var(--color-surface);
  font-size: 11px;
  color: var(--color-text-muted);
}

.report-cards {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.report-card {
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  cursor: pointer;
  transition: all 120ms ease;
}

.report-card:hover {
  border-color: var(--color-primary);
  background: var(--color-info-bg);
}

.report-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.report-card__type {
  padding: 2px 8px;
  border-radius: var(--radius-xs);
  background: var(--color-surface);
  font-size: 11px;
  color: var(--color-text-muted);
}

.report-card__risk {
  padding: 2px 8px;
  border-radius: var(--radius-xs);
  font-size: 11px;
  font-weight: 600;
}

.report-card__risk.risk-high {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.report-card__risk.risk-medium {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.report-card__risk.risk-low {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.report-card__title {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.report-card__meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 12px;
  color: var(--color-text-muted);
}

.empty-state {
  padding: var(--spacing-lg);
  text-align: center;
  color: var(--color-text-muted);
}

.alerts-list__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.alerts-list__batch {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
}

.alerts-list__batch span {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.batch-btn {
  padding: 4px 12px;
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-xs);
  background: var(--color-primary);
  color: var(--color-surface);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 120ms ease;
}

.batch-btn:hover {
  opacity: 0.9;
}

.batch-btn--secondary {
  background: transparent;
  color: var(--color-text-secondary);
}

.batch-btn--secondary:hover {
  background: var(--color-surface);
}

@media (max-width: 768px) {
  .alerts-page__grid {
    grid-template-columns: 1fr;
  }
  
  .insight-cards {
    grid-template-columns: 1fr;
  }
  
  .insight-card--highlight {
    grid-column: span 1;
  }
}
</style>
