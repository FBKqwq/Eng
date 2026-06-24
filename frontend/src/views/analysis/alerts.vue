<template>
  <div class="alerts-page">
    <!-- 分析洞察卡片 -->
    <section class="page-section">
      <AlertInsightCards
        :items="items"
        :loading="loading"
        @view-trace="handleViewTrace"
      />
    </section>

    <!-- 预警记录列表 -->
    <section class="page-section">
      <div class="section-header">
        <h2>预警记录</h2>
        <button
          v-if="items.length"
          type="button"
          class="export-btn"
          :disabled="loading"
          @click="handleExport"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          导出 CSV
        </button>
      </div>
      <AlertTable
        :items="items"
        :total="total"
        :loading="loading"
        :error="listError"
        :selected-id="selectedAlert?.alert_id ?? ''"
        :acking-id="ackingId"
        @select="handleSelect"
        @ack="handleAck"
        @retry="loadAlerts"
      />
    </section>

    <AlertDetailDrawer
      :visible="drawerVisible"
      :alert="selectedAlert"
      :explanation="drawerExplanation"
      :evidences="drawerEvidences"
      :report-link="drawerReportLink"
      @close="closeDrawer"
      @diagnose="handleDiagnose"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AlertInsightCards from '../../components/analysis-alerts/AlertInsightCards.vue'
import AlertTable from '../../components/analysis-alerts/AlertTable.vue'
import AlertDetailDrawer from '../../components/analysis-alerts/AlertDetailDrawer.vue'
import { getActiveAlerts, acknowledgeAlert } from '../../api/alerts.js'
import { useToast } from '../../composables/useToast.js'
import { exportCSV } from '../../utils/export.js'
import { formatTime } from '../../utils/format.js'

const POLL_INTERVAL_MS = 30000

const router = useRouter()
const toast = useToast()

const items = ref([])
const total = ref(0)
const loading = ref(false)
const listError = ref('')
const selectedAlert = ref(null)
const drawerVisible = ref(false)
const ackingId = ref('')
const sessionAckCount = ref(0)

let pollTimer = null

const drawerExplanation = computed(() => extractExplanation(selectedAlert.value))
const drawerEvidences = computed(() => extractEvidences(selectedAlert.value))
const drawerReportLink = computed(() => extractReportLink(selectedAlert.value))

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
    toast.success('预警已确认')
  } catch (err) {
    listError.value = err?.error?.message || err?.message || '确认预警失败，请重试'
    toast.error('确认失败，请重试')
  } finally {
    ackingId.value = ''
  }
}

const ALERT_TYPE_LABELS = {
  error_rate_spike: '错误率',
  latency_degradation: '耗时',
  security_risk: '安全',
  infra_health: '基础设施',
  traffic_anomaly: '流量',
  pay_fail: '支付失败',
  error_spike: '错误激增',
  latency_spike: '延迟异常'
}

const SEVERITY_LABELS = {
  low: '低',
  medium: '中',
  high: '高',
  critical: '严重'
}

const STATUS_LABELS = {
  active: '活跃',
  acknowledged: '已确认',
  resolved: '已解决'
}

function handleExport() {
  const headers = ['类型', '严重度', '服务', '首次时间', '最近时间', '证据数', '状态']
  const fields = ['alert_type', 'severity', 'affected_service', 'created_at', 'updated_at', 'evidence_count', 'status']

  const rows = items.value.map((row) => ({
    ...row,
    alert_type: ALERT_TYPE_LABELS[row.alert_type] ?? row.alert_type,
    severity: SEVERITY_LABELS[row.severity?.toLowerCase()] ?? row.severity,
    created_at: formatTime(row.created_at),
    updated_at: formatTime(row.updated_at),
    status: STATUS_LABELS[row.status] ?? row.status
  }))

  exportCSV('预警记录', headers, fields, rows)
}

function handleDiagnose(alertId) {
  if (!alertId) return
  router.push({ path: '/analysis/diagnosis', query: { alert_id: alertId } })
}

function handleViewTrace(alertItem) {
  if (!alertItem) return
  router.push({
    path: '/analysis/trace',
    query: { alert_id: alertItem.alertId, trace_id: alertItem.traceId || alertItem.alertId }
  })
}

onMounted(() => {
  loadAlerts()
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

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
}

.section-header h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text);
}

.export-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition:
    color var(--transition-fast),
    border-color var(--transition-fast),
    background var(--transition-fast);
}

.export-btn:hover:not(:disabled) {
  color: var(--color-primary);
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.export-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
