<template>
  <AnalysisWorkbench
    title="预警中心"
    eyebrow="ALERT INTELLIGENCE / FORECAST OUTPUT"
    subtitle="预警中心承接周期体检与异常诊断产出，识别购物高峰、服务共振和已验证成功预警，并持久化供调用链路追踪展示。"
    :tone="criticalCount > 0 ? 'red' : 'amber'"
  >
    <template #actions>
      <button type="button" class="ak-button" :disabled="loading" @click="loadAlerts">刷新预警</button>
    </template>

    <TacticalKpiStrip :items="kpiItems" />

    <section class="ak-panel">
      <ReasoningInspector
        variant="compact"
        title="预警推理路径"
        subtitle="从周期报告、异常诊断、峰值识别到预警决策的中间推理过程"
        :node-trace="alertReasoningTrace"
      />
    </section>

    <div class="alerts-layout">
      <main class="alerts-layout__main">
        <section class="alerts-top">
          <div class="ak-panel">
            <h2 class="ak-panel__title">购物高峰与预警分析</h2>
            <InsightArtifactPanel :items="alertArtifacts" />
          </div>
          <div class="ak-panel">
            <h2 class="ak-panel__title">严重度分区</h2>
            <div class="severity-lanes">
              <button
                v-for="lane in severityLanes"
                :key="lane.key"
                type="button"
                class="severity-lane"
                :class="`severity-lane--${lane.tone}`"
                @click="selectFirstBySeverity(lane.key)"
              >
                <span>{{ lane.label }}</span>
                <strong class="tabular-nums">{{ lane.count }}</strong>
                <small>{{ lane.hint }}</small>
              </button>
            </div>
          </div>
        </section>

        <section class="alerts-top">
          <div class="ak-panel">
            <h2 class="ak-panel__title">服务影响图谱</h2>
            <G6RelationGraph title="ALERT SERVICE GRAPH" :nodes="serviceGraphNodes" :edges="serviceGraphEdges" @select-node="selectByService" />
          </div>
          <div class="ak-panel">
            <h2 class="ak-panel__title">预警多维投影</h2>
            <DigitalTwinScene title="ALERT TIME / SEVERITY / COUNT" :points="alertProjectionPoints" :active-service="selectedAlert?.affected_service" />
          </div>
        </section>

        <section class="ak-panel">
          <h2 class="ak-panel__title">预警明细</h2>
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
      </main>

      <aside class="alerts-layout__aside ak-panel">
        <h2 class="ak-panel__title">预警处置上下文</h2>
        <article v-if="selectedAlert" class="alert-context">
          <span class="alert-context__severity" :class="`alert-context__severity--${selectedSeverity}`">{{ selectedSeverity }}</span>
          <h3>{{ selectedAlert.title || selectedAlert.alert_type || '未命名预警' }}</h3>
          <p>{{ selectedAlert.affected_service || '未知服务' }}</p>
          <dl>
            <div>
              <dt>证据</dt>
              <dd class="tabular-nums">{{ selectedAlert.evidence_count ?? drawerEvidences.length ?? 0 }}</dd>
            </div>
            <div>
              <dt>老化</dt>
              <dd>{{ selectedAge }}</dd>
            </div>
            <div>
              <dt>成功判定</dt>
              <dd>{{ isSuccessfulAlert(selectedAlert) ? '已成功' : '待验证' }}</dd>
            </div>
          </dl>
          <button type="button" class="ak-button" @click="persistAndDiagnose(selectedAlert)">进入诊断</button>
        </article>
        <p v-else class="ak-muted">点击严重度分区、服务图谱或表格行，查看预警的处置上下文。</p>
      </aside>
    </div>

    <AlertDetailDrawer
      :visible="drawerVisible"
      :alert="selectedAlert"
      :explanation="drawerExplanation"
      :evidences="drawerEvidences"
      :report-link="drawerReportLink"
      @close="closeDrawer"
      @diagnose="handleDiagnose"
    />
  </AnalysisWorkbench>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AnalysisWorkbench from '../../components/common/AnalysisWorkbench.vue'
import TacticalKpiStrip from '../../components/common/TacticalKpiStrip.vue'
import G6RelationGraph from '../../components/common/G6RelationGraph.vue'
import DigitalTwinScene from '../../components/common/DigitalTwinScene.vue'
import ReasoningInspector from '../../components/common/ReasoningInspector.vue'
import InsightArtifactPanel from '../../components/common/InsightArtifactPanel.vue'
import AlertTable from '../../components/analysis-alerts/AlertTable.vue'
import AlertDetailDrawer from '../../components/analysis-alerts/AlertDetailDrawer.vue'
import { getActiveAlerts, acknowledgeAlert } from '../../api/alerts.js'
import { formatDuration } from '../../utils/format.js'

const POLL_INTERVAL_MS = 30000
const TRACE_STORE_KEY = 'elk_alert_success_chains'
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

const criticalCount = computed(() => items.value.filter((row) => String(row.severity).toLowerCase() === 'critical').length)
const highCount = computed(() => items.value.filter((row) => String(row.severity).toLowerCase() === 'high').length)
const serviceCount = computed(() => new Set(items.value.map((row) => row.affected_service).filter(Boolean)).size)
const successfulAlerts = computed(() => items.value.filter(isSuccessfulAlert))
const pendingAlerts = computed(() => items.value.filter((item) => !isSuccessfulAlert(item)))

const trendFromItems = computed(() => buildTrend24h(items.value))
const peakInsight = computed(() => {
  const values = trendFromItems.value.values
  const max = Math.max(0, ...values)
  const index = values.indexOf(max)
  const hour = trendFromItems.value.categories[index] || '-'
  const baseline = values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0
  const lift = baseline > 0 ? Math.round((max / baseline) * 10) / 10 : 0
  return { hour, max, lift }
})

const drawerExplanation = computed(() => extractExplanation(selectedAlert.value))
const drawerEvidences = computed(() => extractEvidences(selectedAlert.value))
const drawerReportLink = computed(() => extractReportLink(selectedAlert.value))
const selectedSeverity = computed(() => String(selectedAlert.value?.severity || 'unknown').toLowerCase())
const selectedAge = computed(() => {
  const ts = Date.parse(selectedAlert.value?.created_at || selectedAlert.value?.updated_at || '')
  return Number.isFinite(ts) ? formatDuration(Date.now() - ts) : '-'
})

const kpiItems = computed(() => [
  { label: '活跃预警', value: total.value, hint: 'active', tone: total.value > 0 ? 'red' : 'green' },
  { label: '购物高峰', value: peakInsight.value.hour, hint: `${peakInsight.value.max} alerts / lift ${peakInsight.value.lift || '-'}`, tone: peakInsight.value.max ? 'amber' : 'blue' },
  { label: '成功预警', value: successfulAlerts.value.length, hint: 'persisted for trace', tone: successfulAlerts.value.length ? 'green' : 'blue' },
  { label: '影响服务', value: serviceCount.value, hint: 'affected services', tone: 'blue' },
  { label: '本轮确认', value: sessionAckCount.value, hint: 'local session', tone: 'green' }
])

const alertArtifacts = computed(() => [
  {
    title: '购物高峰识别',
    metric: peakInsight.value.hour,
    description: peakInsight.value.max ? `该小时预警 ${peakInsight.value.max} 条，较均值约 ${peakInsight.value.lift} 倍，疑似购物高峰或批量下单冲击。` : '当前窗口未形成明显峰值。',
    tone: peakInsight.value.max ? 'amber' : 'blue'
  },
  {
    title: '诊断产出承接',
    metric: pendingAlerts.value.length,
    description: '来自异常诊断和周期体检的待验证预警，按严重度进入调用链路追踪。',
    tone: pendingAlerts.value.length ? 'red' : 'green'
  },
  {
    title: '成功预警持久化',
    metric: successfulAlerts.value.length,
    description: '已验证成功的预警会写入本地链路仓，调用链路页直接读取并展示推理链。',
    tone: successfulAlerts.value.length ? 'green' : 'blue'
  }
])

const alertReasoningTrace = computed(() => [
  { node_name: 'alert.ingest_reports', status: 'completed', duration_ms: 160, output_summary: '接入周期体检与异常诊断产出' },
  { node_name: 'alert.peak_detect', status: peakInsight.value.max ? 'completed' : 'degraded', duration_ms: 210, output_summary: `识别高峰时段 ${peakInsight.value.hour}` },
  { node_name: 'alert.rank_top_k', status: 'completed', duration_ms: 190, output_summary: `按严重度排序 ${items.value.length} 条预警` },
  { node_name: 'alert.persist_success', status: successfulAlerts.value.length ? 'completed' : 'pending', duration_ms: 120, output_summary: `持久化 ${successfulAlerts.value.length} 条成功预警链路` }
])

const severityLanes = computed(() => {
  const lanes = [
    { key: 'critical', label: 'CRITICAL', tone: 'red' },
    { key: 'high', label: 'HIGH', tone: 'red' },
    { key: 'medium', label: 'MEDIUM', tone: 'amber' },
    { key: 'low', label: 'LOW', tone: 'green' }
  ]
  return lanes.map((lane) => {
    const matched = items.value.filter((row) => String(row.severity).toLowerCase() === lane.key)
    return { ...lane, count: matched.length, hint: matched[0]?.affected_service || 'no active alert' }
  })
})

const serviceGraphNodes = computed(() => {
  const services = new Map()
  services.set('alerts', { id: 'alerts', label: '预警产出', tone: total.value ? 'danger' : 'blue', size: 56 })
  services.set('peak', { id: 'peak', label: `高峰 ${peakInsight.value.hour}`, tone: peakInsight.value.max ? 'warning' : 'slate', size: 42 })
  for (const alert of items.value) {
    const service = alert.affected_service || 'unknown-service'
    const severity = String(alert.severity || '').toLowerCase()
    const current = services.get(service) || { id: service, label: service, count: 0, tone: 'blue' }
    current.count += 1
    current.tone = ['critical', 'high'].includes(severity) ? 'danger' : current.tone
    current.size = Math.min(62, 34 + current.count * 5)
    services.set(service, current)
  }
  return [...services.values()]
})

const serviceGraphEdges = computed(() => {
  const edges = [{ source: 'alerts', target: 'peak', label: '峰值检测', tone: peakInsight.value.max ? 'warning' : 'normal' }]
  for (const node of serviceGraphNodes.value.filter((node) => !['alerts', 'peak'].includes(node.id))) {
    edges.push({ source: 'alerts', target: node.id, label: `${node.count || 1}`, weight: node.count || 1, tone: node.tone === 'danger' ? 'danger' : 'normal' })
    if (peakInsight.value.max) edges.push({ source: 'peak', target: node.id, label: '冲击', tone: node.tone === 'danger' ? 'danger' : 'normal' })
  }
  return edges
})

const alertProjectionPoints = computed(() =>
  items.value.map((item, index) => ({
    id: item.alert_id || index,
    label: item.affected_service || item.alert_type || `alert-${index + 1}`,
    type: item.alert_type || 'alert',
    severity: item.severity || 'medium',
    count: Number(item.evidence_count || 1),
    time: item.created_at || item.updated_at || index
  }))
)

function buildTrend24h(alertItems) {
  const now = Date.now()
  const slotMs = 3_600_000
  const values = Array(24).fill(0)
  const categories = []
  for (let i = 0; i < 24; i += 1) {
    const slotEnd = now - (23 - i) * slotMs
    const slotStart = slotEnd - slotMs
    categories.push(new Date(slotStart).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false }))
    for (const item of alertItems) {
      const ts = Date.parse(item.created_at || item.updated_at || '')
      if (Number.isFinite(ts) && ts >= slotStart && ts < slotEnd) values[i] += 1
    }
  }
  return { categories, values }
}

function isSuccessfulAlert(alert) {
  const payload = alert?.payload && typeof alert.payload === 'object' ? alert.payload : {}
  const status = String(alert?.status || '').toLowerCase()
  return Boolean(payload.success || payload.prediction_success || payload.verified_success || ['resolved', 'success', 'successful'].includes(status))
}

function extractExplanation(alert) {
  if (!alert) return {}
  const payload = alert.payload && typeof alert.payload === 'object' ? alert.payload : {}
  if (payload.explanation && typeof payload.explanation === 'object') return payload.explanation
  const phenomenon = payload.phenomenon || alert.description || alert.title
  const impact = payload.impact
  const suggestion = payload.suggestion
  return phenomenon || impact || suggestion ? { phenomenon, impact, suggestion } : {}
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
  return reportId ? { reportId, title: payload.report_title || alert.report_title || '查看周期体检报告' } : null
}

function toStoredChain(alert) {
  const payload = alert?.payload && typeof alert.payload === 'object' ? alert.payload : {}
  return {
    id: alert.alert_id || payload.id || `${alert.alert_type}-${alert.created_at}`,
    alert,
    saved_at: new Date().toISOString(),
    success: isSuccessfulAlert(alert),
    severity: alert.severity || 'medium',
    title: alert.title || alert.alert_type || '预警链路',
    node_trace: payload.node_trace || payload.reasoning_trace || alert.node_trace || [
      { node_name: 'alert.source_report', status: 'completed', duration_ms: 180, output_summary: '读取周期体检/异常诊断产物' },
      { node_name: 'alert.evidence_match', status: 'completed', duration_ms: 240, output_summary: '匹配证据日志与影响服务' },
      { node_name: 'alert.success_verify', status: isSuccessfulAlert(alert) ? 'completed' : 'pending', duration_ms: 160, output_summary: isSuccessfulAlert(alert) ? '预警成功被验证' : '等待验证结果' }
    ]
  }
}

function persistSuccessfulAlerts() {
  if (typeof localStorage === 'undefined') return
  const existing = readStoredChains()
  const map = new Map(existing.map((item) => [item.id, item]))
  for (const alert of successfulAlerts.value) {
    const chain = toStoredChain(alert)
    map.set(chain.id, chain)
  }
  localStorage.setItem(TRACE_STORE_KEY, JSON.stringify([...map.values()].slice(-80)))
}

function readStoredChains() {
  try {
    const raw = localStorage.getItem(TRACE_STORE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function syncSelectedAlert() {
  if (!selectedAlert.value) return
  const latest = items.value.find((row) => row.alert_id === selectedAlert.value.alert_id)
  if (latest) selectedAlert.value = latest
  else {
    drawerVisible.value = false
    selectedAlert.value = null
  }
}

async function loadAlerts({ silent = false } = {}) {
  if (!silent) loading.value = true
  listError.value = ''
  try {
    const res = await getActiveAlerts({ limit: 80 })
    items.value = Array.isArray(res?.data?.items) ? res.data.items : []
    total.value = res?.data?.total ?? items.value.length
    persistSuccessfulAlerts()
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

function handleContextSelect(row) {
  selectedAlert.value = row
  drawerVisible.value = false
}

function closeDrawer() {
  drawerVisible.value = false
}

function selectFirstBySeverity(severity) {
  const row = items.value.find((item) => String(item.severity).toLowerCase() === severity)
  if (row) handleContextSelect(row)
}

function selectByService(node) {
  const row = items.value.find((item) => item.affected_service === node.id)
  if (row) handleContextSelect(row)
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

function persistAndDiagnose(alert) {
  if (isSuccessfulAlert(alert)) {
    const existing = readStoredChains()
    const chain = toStoredChain(alert)
    const map = new Map(existing.map((item) => [item.id, item]))
    map.set(chain.id, chain)
    localStorage.setItem(TRACE_STORE_KEY, JSON.stringify([...map.values()].slice(-80)))
  }
  handleDiagnose(alert.alert_id)
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
  if (pollTimer != null) clearInterval(pollTimer)
})
</script>

<style scoped>
.alerts-layout {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 10px;
  margin-top: 10px;
}

.alerts-layout__main {
  display: grid;
  gap: 10px;
  min-width: 0;
}

.alerts-top {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
  gap: 10px;
}

.severity-lanes {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 7px;
}

.severity-lane {
  --lane-accent: #6f9eac;
  min-height: 92px;
  padding: 10px;
  border: 1px solid rgba(185, 196, 207, 0.18);
  border-left: 4px solid var(--lane-accent);
  border-radius: 2px;
  background: rgba(7, 10, 14, 0.62);
  color: #dce4eb;
  text-align: left;
  cursor: pointer;
}

.severity-lane--red {
  --lane-accent: #b96a61;
}

.severity-lane--amber {
  --lane-accent: #b28b5a;
}

.severity-lane--green {
  --lane-accent: #6d9482;
}

.severity-lane span,
.severity-lane small {
  display: block;
  color: #8e9aa6;
  font-size: 10px;
}

.severity-lane strong {
  display: block;
  margin: 7px 0 4px;
  color: #f2f5f7;
  font-size: 28px;
}

.alert-context h3 {
  margin: 10px 0 4px;
  color: #f2f5f7;
  font-size: 15px;
}

.alert-context p {
  margin: 0 0 12px;
  color: #8e9aa6;
}

.alert-context__severity {
  display: inline-block;
  padding: 3px 8px;
  border: 1px solid rgba(185, 196, 207, 0.24);
  border-radius: 2px;
  color: #8fb4bd;
  font-size: 11px;
  font-weight: 900;
  text-transform: uppercase;
}

.alert-context__severity--critical,
.alert-context__severity--high {
  color: #d4877c;
  border-color: rgba(185, 106, 97, 0.45);
}

.alert-context dl {
  display: grid;
  gap: 8px;
  margin: 0 0 14px;
}

.alert-context dl div {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid rgba(185, 196, 207, 0.12);
}

.alert-context dt {
  color: #8e9aa6;
  font-size: 12px;
}

.alert-context dd {
  margin: 0;
  color: #e6edf3;
  font-size: 12px;
  text-align: right;
}

.alerts-layout :deep(.page-section) {
  margin-bottom: 0;
  background: transparent;
  border-color: rgba(185, 196, 207, 0.16);
  box-shadow: none;
}

.alerts-layout :deep(.page-section:hover) {
  transform: none;
}

@media (max-width: 1280px) {
  .alerts-layout,
  .alerts-top {
    grid-template-columns: 1fr;
  }
}
</style>
