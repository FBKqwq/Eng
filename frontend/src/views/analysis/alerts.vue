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

    <section class="page-section">
      <h2>预警列表</h2>
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
import AlertBoard from '../../components/analysis-alerts/AlertBoard.vue'
import AlertTable from '../../components/analysis-alerts/AlertTable.vue'
import AlertDetailDrawer from '../../components/analysis-alerts/AlertDetailDrawer.vue'
import { getActiveAlerts, acknowledgeAlert } from '../../api/alerts.js'

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
</style>
