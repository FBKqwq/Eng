<template>
  <AnalysisWorkbench
    title="调用链路追踪"
    eyebrow="ALERT REASONING CHAINS / TRACE BOARD"
    subtitle="不再手动检索 trace_id，直接消费预警中心持久化的预警推理链路，按严重程度展示待验证与已成功预警。"
    :tone="breakpointTone"
  >
    <template #actions>
      <button type="button" class="ak-button" :disabled="loading" @click="loadAlertChains">刷新链路</button>
    </template>

    <TacticalKpiStrip :items="kpiItems" />

    <section class="trace-chain-grid">
      <div class="ak-panel">
        <h2 class="ak-panel__title">已预警但不知是否成功 / TOP_K</h2>
        <div class="chain-list">
          <button
            v-for="chain in pendingTopK"
            :key="chain.id"
            type="button"
            class="chain-card"
            :class="[`chain-card--${chain.tone}`, { active: selectedChain?.id === chain.id }]"
            @click="selectedChain = chain"
          >
            <span>{{ chain.severity }}</span>
            <strong>{{ chain.title }}</strong>
            <small>{{ chain.service }} / {{ chain.age }}</small>
          </button>
          <p v-if="!pendingTopK.length" class="ak-muted">暂无待验证预警链路。</p>
        </div>
      </div>

      <div class="ak-panel">
        <h2 class="ak-panel__title">已预警并且成功 / TOP_K</h2>
        <div class="chain-list">
          <button
            v-for="chain in successTopK"
            :key="chain.id"
            type="button"
            class="chain-card"
            :class="[`chain-card--${chain.tone}`, { active: selectedChain?.id === chain.id }]"
            @click="selectedChain = chain"
          >
            <span>{{ chain.severity }}</span>
            <strong>{{ chain.title }}</strong>
            <small>{{ chain.service }} / {{ chain.age }}</small>
          </button>
          <p v-if="!successTopK.length" class="ak-muted">暂无成功预警链路，预警中心确认后会自动出现。</p>
        </div>
      </div>
    </section>

    <section class="ak-panel">
      <ReasoningInspector
        variant="compact"
        title="选中预警推理路径"
        subtitle="展示预警如何从报告/诊断产物、证据匹配、服务影响到成功验证"
        :node-trace="selectedChain?.node_trace || []"
      />
    </section>

    <main class="trace-layout">
      <section class="ak-panel">
        <h2 class="ak-panel__title">预警链路图谱</h2>
        <G6RelationGraph title="ALERT TRACE GRAPH" :nodes="traceNodes" :edges="traceEdges" @select-node="selectedService = $event.label" />
      </section>
      <section class="ak-panel">
        <h2 class="ak-panel__title">链路多维投影</h2>
        <DigitalTwinScene
          title="CHAIN TIME / SEVERITY / EVIDENCE"
          :points="traceProjectionPoints"
          :active-service="selectedService || selectedChain?.service"
        />
      </section>
    </main>

    <section class="ak-panel trace-breakpoint">
      <h2 class="ak-panel__title">链路断点解释</h2>
      <div v-if="selectedChain" class="trace-breakpoint__content">
        <strong>{{ selectedChain.service }}</strong>
        <span>{{ selectedChain.success ? '成功预警链路已验证' : '待验证预警链路，按严重度优先跟进' }}</span>
        <p>{{ selectedChain.summary }}</p>
      </div>
      <p v-else class="ak-muted">等待预警中心产出或持久化链路。</p>
    </section>

    <section v-if="listError" class="trace-status trace-status--error">
      <span>{{ listError }}</span>
      <button type="button" class="ak-button" @click="loadAlertChains">重试</button>
    </section>
  </AnalysisWorkbench>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import AnalysisWorkbench from '../../components/common/AnalysisWorkbench.vue'
import TacticalKpiStrip from '../../components/common/TacticalKpiStrip.vue'
import G6RelationGraph from '../../components/common/G6RelationGraph.vue'
import DigitalTwinScene from '../../components/common/DigitalTwinScene.vue'
import ReasoningInspector from '../../components/common/ReasoningInspector.vue'
import { getActiveAlerts } from '../../api/alerts.js'
import { formatDuration } from '../../utils/format.js'

const TRACE_STORE_KEY = 'elk_alert_success_chains'

const loading = ref(false)
const listError = ref('')
const activeAlerts = ref([])
const storedChains = ref([])
const selectedChain = ref(null)
const selectedService = ref('')

const allChains = computed(() => {
  const active = activeAlerts.value.map((alert) => normalizeAlertChain(alert, false))
  const stored = storedChains.value.map((chain) => normalizeStoredChain(chain))
  const map = new Map()
  for (const chain of [...active, ...stored]) {
    const existing = map.get(chain.id)
    if (!existing || (chain.success && !existing.success)) map.set(chain.id, chain)
  }
  return [...map.values()].sort((a, b) => severityWeight(b.severity) - severityWeight(a.severity) || b.ts - a.ts)
})

const pendingTopK = computed(() => allChains.value.filter((chain) => !chain.success).slice(0, 6))
const successTopK = computed(() => allChains.value.filter((chain) => chain.success).slice(0, 6))
const breakpointTone = computed(() => (pendingTopK.value.some((chain) => ['critical', 'high'].includes(chain.severity)) ? 'red' : 'blue'))

const kpiItems = computed(() => [
  { label: '待验证链路', value: pendingTopK.value.length, hint: 'warned / unknown', tone: pendingTopK.value.length ? 'red' : 'green' },
  { label: '成功链路', value: successTopK.value.length, hint: 'warned / success', tone: successTopK.value.length ? 'green' : 'blue' },
  { label: '最高严重度', value: allChains.value[0]?.severity || '-', hint: allChains.value[0]?.service || 'no chain', tone: breakpointTone.value === 'red' ? 'red' : 'blue' },
  { label: '影响服务', value: new Set(allChains.value.map((chain) => chain.service).filter(Boolean)).size, hint: 'service coverage', tone: 'blue' },
  { label: '链路总数', value: allChains.value.length, hint: 'alert chains', tone: 'green' }
])

const traceNodes = computed(() => {
  const chain = selectedChain.value || allChains.value[0]
  if (!chain) return []
  const nodes = [
    { id: 'alert-output', label: '预警产出', tone: chain.success ? 'success' : 'danger', size: 54 },
    { id: chain.id, label: chain.title, tone: chain.tone, size: 46 },
    { id: chain.service, label: chain.service, tone: chain.tone === 'red' ? 'danger' : 'blue', size: 40 }
  ]
  chain.node_trace.forEach((node, index) => {
    nodes.push({ id: `${chain.id}-node-${index}`, label: stageLabel(node.node_name || node.name || `node-${index}`), tone: resolveStatusTone(node.status), size: 30 })
  })
  return nodes
})

const traceEdges = computed(() => {
  const chain = selectedChain.value || allChains.value[0]
  if (!chain) return []
  const edges = [
    { source: 'alert-output', target: chain.id, label: chain.success ? '成功' : '待验证', tone: chain.success ? 'normal' : 'danger' },
    { source: chain.id, target: chain.service, label: '影响服务', tone: chain.tone === 'red' ? 'danger' : 'normal' }
  ]
  chain.node_trace.forEach((node, index) => {
    const id = `${chain.id}-node-${index}`
    edges.push({ source: index === 0 ? chain.id : `${chain.id}-node-${index - 1}`, target: id, label: node.status || 'node', tone: resolveStatusTone(node.status) === 'danger' ? 'danger' : 'normal' })
  })
  return edges
})

const traceProjectionPoints = computed(() =>
  allChains.value.map((chain, index) => ({
    id: chain.id,
    label: chain.service,
    type: chain.success ? 'success-chain' : 'pending-chain',
    severity: chain.severity,
    count: chain.evidenceCount || chain.node_trace.length || 1,
    time: chain.ts || index
  }))
)

function normalizeAlertChain(alert, forceSuccess) {
  const payload = alert?.payload && typeof alert.payload === 'object' ? alert.payload : {}
  const success = forceSuccess || isSuccessfulAlert(alert)
  const ts = Date.parse(alert.created_at || alert.updated_at || '')
  const nodeTrace = payload.node_trace || payload.reasoning_trace || alert.node_trace || [
    { node_name: 'alert.source_report', status: 'completed', duration_ms: 180, output_summary: '读取周期体检和异常诊断产物' },
    { node_name: 'alert.evidence_match', status: 'completed', duration_ms: 240, output_summary: '匹配证据日志、服务和时间窗' },
    { node_name: 'alert.success_verify', status: success ? 'completed' : 'pending', duration_ms: 160, output_summary: success ? '预警已被验证成功' : '等待业务结果或人工确认' }
  ]
  const severity = String(alert.severity || 'medium').toLowerCase()
  return {
    id: alert.alert_id || `${alert.alert_type}-${alert.created_at}`,
    title: alert.title || alert.alert_type || '预警链路',
    service: alert.affected_service || payload.affected_service || 'unknown-service',
    severity,
    tone: ['critical', 'high'].includes(severity) ? 'red' : severity === 'medium' ? 'amber' : 'blue',
    success,
    ts: Number.isFinite(ts) ? ts : 0,
    age: Number.isFinite(ts) ? formatDuration(Date.now() - ts) : '-',
    evidenceCount: Number(alert.evidence_count || payload.evidence_count || 0),
    summary: alert.description || payload.summary || payload.impact || '该链路来自预警中心产出，按严重度进入追踪队列。',
    node_trace: nodeTrace
  }
}

function normalizeStoredChain(chain) {
  const alert = chain.alert || {}
  const normalized = normalizeAlertChain(alert, Boolean(chain.success))
  const savedTs = Date.parse(chain.saved_at || alert.updated_at || alert.created_at || '')
  return {
    ...normalized,
    id: chain.id || normalized.id,
    title: chain.title || normalized.title,
    severity: String(chain.severity || normalized.severity || 'medium').toLowerCase(),
    success: Boolean(chain.success),
    ts: Number.isFinite(savedTs) ? savedTs : normalized.ts,
    age: Number.isFinite(savedTs) ? formatDuration(Date.now() - savedTs) : normalized.age,
    node_trace: Array.isArray(chain.node_trace) && chain.node_trace.length ? chain.node_trace : normalized.node_trace
  }
}

function isSuccessfulAlert(alert) {
  const payload = alert?.payload && typeof alert.payload === 'object' ? alert.payload : {}
  const status = String(alert?.status || '').toLowerCase()
  return Boolean(payload.success || payload.prediction_success || payload.verified_success || ['resolved', 'success', 'successful'].includes(status))
}

function severityWeight(value) {
  return { critical: 4, high: 3, medium: 2, low: 1 }[String(value || '').toLowerCase()] || 0
}

function resolveStatusTone(status) {
  const lower = String(status || '').toLowerCase()
  if (['failed', 'error'].includes(lower)) return 'danger'
  if (['pending', 'degraded'].includes(lower)) return 'warning'
  if (['completed', 'success', 'ok'].includes(lower)) return 'success'
  return 'blue'
}

function stageLabel(name) {
  const lower = String(name).toLowerCase()
  if (lower.includes('source') || lower.includes('report')) return '产物读取'
  if (lower.includes('evidence')) return '证据匹配'
  if (lower.includes('success') || lower.includes('verify')) return '成功验证'
  if (lower.includes('alert')) return '预警决策'
  return '推理节点'
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

async function loadAlertChains() {
  loading.value = true
  listError.value = ''
  try {
    const res = await getActiveAlerts({ limit: 80 })
    activeAlerts.value = Array.isArray(res?.data?.items) ? res.data.items : []
    storedChains.value = readStoredChains()
    selectedChain.value = selectedChain.value && allChains.value.find((chain) => chain.id === selectedChain.value.id)
      ? allChains.value.find((chain) => chain.id === selectedChain.value.id)
      : allChains.value[0] || null
  } catch (err) {
    activeAlerts.value = []
    storedChains.value = readStoredChains()
    selectedChain.value = allChains.value[0] || null
    listError.value = err?.error?.message || err?.message || '预警链路加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadAlertChains)
</script>

<style scoped>
.trace-chain-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 10px;
}

.chain-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 7px;
}

.chain-card {
  --chain-accent: #6f9eac;
  min-height: 78px;
  padding: 9px;
  color: #dce4eb;
  background: rgba(7, 10, 14, 0.58);
  border: 1px solid rgba(185, 196, 207, 0.16);
  border-left: 3px solid var(--chain-accent);
  border-radius: 2px;
  text-align: left;
  cursor: pointer;
}

.chain-card--red {
  --chain-accent: #b96a61;
}

.chain-card--amber {
  --chain-accent: #b28b5a;
}

.chain-card.active,
.chain-card:hover {
  border-color: color-mix(in srgb, var(--chain-accent) 58%, rgba(185, 196, 207, 0.18));
}

.chain-card span,
.chain-card small {
  display: block;
  overflow: hidden;
  color: #8e9aa6;
  font-size: 10px;
  text-overflow: ellipsis;
  text-transform: uppercase;
  white-space: nowrap;
}

.chain-card strong {
  display: block;
  margin: 5px 0;
  overflow: hidden;
  color: #f2f5f7;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.trace-layout {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 0.72fr);
  gap: 10px;
  margin-top: 10px;
}

.trace-breakpoint {
  margin-top: 10px;
}

.trace-breakpoint__content {
  display: grid;
  gap: 5px;
}

.trace-breakpoint__content strong {
  color: #d4877c;
  font-size: 18px;
}

.trace-breakpoint__content span,
.trace-breakpoint__content p {
  margin: 0;
  color: #aab4bf;
}

.trace-status {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
  padding: 10px 12px;
  color: #c9dde2;
  background: rgba(111, 158, 172, 0.1);
  border: 1px solid rgba(111, 158, 172, 0.32);
  border-radius: 3px;
}

.trace-status--error {
  color: #e2b8b2;
  background: rgba(185, 106, 97, 0.12);
  border-color: rgba(185, 106, 97, 0.42);
}

@media (max-width: 1280px) {
  .trace-chain-grid,
  .trace-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .chain-list {
    grid-template-columns: 1fr;
  }
}
</style>
