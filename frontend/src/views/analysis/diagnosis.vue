<template>
  <AnalysisWorkbench
    title="异常诊断中心"
    eyebrow="RULE SUBGRAPH / CONTINUOUS DIAGNOSIS"
    subtitle="先看整段规则命中的聚类、拓扑扩散与 top_k 风险，再下钻到单个诊断报告和证据链。"
    :tone="workbenchTone"
  >
    <template #actions>
      <span v-if="showMockBadge" class="diagnosis-badge">演示数据</span>
      <button v-if="lastPayload" type="button" class="ak-button" :disabled="loading || graphLoading" @click="handleSubmit(lastPayload)">
        重新推断
      </button>
    </template>

    <TacticalKpiStrip :items="kpiItems" />

    <div v-if="loading || graphLoading || errorMessage" class="diagnosis-status" :class="{ 'diagnosis-status--error': errorMessage }" role="status">
      <span>{{ errorMessage || loadingMessage }}</span>
    </div>

    <section class="ak-panel diagnosis-reasoning">
      <ReasoningInspector
        variant="compact"
        title="规则子图推理路径"
        subtitle="作为次级组件置顶：展示当前规则子图从取证、聚类、关联到定级的中间节点"
        :node-trace="displayTrace"
      />
    </section>

    <div class="diagnosis-grid">
      <div class="diagnosis-grid__upper">
        <section class="diagnosis-overview">
          <div class="ak-panel">
            <h2 class="ak-panel__title">规则命中聚类 / TOP_K</h2>
            <div class="cluster-rank">
              <button
                v-for="cluster in ruleClusters"
                :key="cluster.id"
                type="button"
                class="cluster-rank__item"
                :class="[`cluster-rank__item--${cluster.tone}`, { active: selectedClusterId === cluster.id }]"
                @click="selectedClusterId = cluster.id"
              >
                <span class="tabular-nums">{{ cluster.rank }}</span>
                <strong>{{ cluster.title }}</strong>
                <small>{{ cluster.service }} / {{ cluster.count }} hits / {{ cluster.window }}</small>
              </button>
            </div>
          </div>

          <div class="ak-panel">
            <h2 class="ak-panel__title">风险分段</h2>
            <RiskLevelStrip
              :level="selectedCluster?.severity || diagnosisResult?.severity || 'medium'"
              :score="diagnosisResult?.confidence"
              :reason="selectedCluster?.reason || diagnosisResult?.root_cause || '基于规则命中密度、服务影响面与证据节点数进行分段。'"
            />
          </div>
        </section>

        <section class="diagnosis-visual">
          <div class="ak-panel">
            <h2 class="ak-panel__title">规则子图结果图谱</h2>
            <G6RelationGraph
              title="RULE CLUSTER GRAPH"
              :nodes="subgraphNodes"
              :edges="subgraphEdges"
              @select-node="selectedService = $event.label"
            />
          </div>
          <div class="ak-panel">
            <h2 class="ak-panel__title">多维诊断投影 / PCA</h2>
            <DigitalTwinScene
              title="TIME / TYPE / SEVERITY / COUNT"
              :points="diagnosisPoints"
              :active-service="selectedService || selectedCluster?.service"
            />
          </div>
        </section>
      </div>

      <section class="ak-panel diagnosis-single">
        <h2 class="ak-panel__title">推理路径</h2>
        <SuggestionChecklist
          :suggestions="suggestions"
          :node-trace="nodeTrace"
          :degraded="isDegraded"
          :show-title="false"
          :show-checklist="false"
        />
      </section>

      <aside class="diagnosis-grid__side ak-panel">
        <h2 class="ak-panel__title">诊断入口</h2>
      <DiagnosisEntryPanel
          :loading="loading || graphLoading"
          :alerts="alerts"
          @submit="handleSubmit"
          @request-alerts="loadAlerts"
        />
      </aside>

      <section class="diagnosis-evidence">
        <div class="ak-panel">
          <h2 class="ak-panel__title">证据时间线</h2>
          <div class="evidence-scroll">
            <EvidenceTimeline :evidence-logs="evidenceLogs" />
          </div>
        </div>
        <div class="ak-panel">
          <h2 class="ak-panel__title">单次诊断结果</h2>
          <div class="single-result">
            <RiskLevelStrip
              :level="diagnosisResult?.severity || selectedCluster?.severity || 'medium'"
              :score="diagnosisResult?.confidence"
              :reason="diagnosisResult?.root_cause || diagnosisResult?.summary || '选择左侧入口运行一次规则子图后，将展示可落地的根因结论。'"
            />
            <div class="single-result__text">
              <h3>{{ diagnosisResult?.title || diagnosisResult?.anomaly_type || '等待单次诊断报告' }}</h3>
              <p>{{ diagnosisResult?.summary || diagnosisResult?.root_cause || '首屏已展示整段规则子图聚类；单个诊断结果作为后置详情用于处置。' }}</p>
            </div>
            <div class="single-result__suggestions">
              <h3>建议结果</h3>
              <SuggestionChecklist
                :suggestions="suggestions"
                :node-trace="nodeTrace"
                :degraded="isDegraded"
                :show-title="false"
                :show-stage="false"
              />
            </div>
          </div>
        </div>
      </section>
    </div>
  </AnalysisWorkbench>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import AnalysisWorkbench from '../../components/common/AnalysisWorkbench.vue'
import TacticalKpiStrip from '../../components/common/TacticalKpiStrip.vue'
import G6RelationGraph from '../../components/common/G6RelationGraph.vue'
import DigitalTwinScene from '../../components/common/DigitalTwinScene.vue'
import ReasoningInspector from '../../components/common/ReasoningInspector.vue'
import RiskLevelStrip from '../../components/common/RiskLevelStrip.vue'
import DiagnosisEntryPanel from '../../components/analysis-diagnosis/DiagnosisEntryPanel.vue'
import EvidenceTimeline from '../../components/analysis-diagnosis/EvidenceTimeline.vue'
import SuggestionChecklist from '../../components/analysis-diagnosis/SuggestionChecklist.vue'
import { submitDiagnosis, USE_MOCK as DIAGNOSIS_USE_MOCK } from '../../api/diagnosis.js'
import { triggerAnalysisRun, USE_MOCK as ANALYSIS_USE_MOCK } from '../../api/analysis.js'
import { getReportDetail } from '../../api/reports.js'
import { getActiveAlerts } from '../../api/alerts.js'

const loading = ref(false)
const graphLoading = ref(false)
const loadingMessage = ref('LangGraph 规则子图运行中：拉取上下文、聚类命中段、构建证据并生成根因结论')
const errorMessage = ref('')
const diagnosisResult = ref(null)
const nodeTrace = ref([])
const alerts = ref([])
const lastPayload = ref(null)
const activeRequestKey = ref('')
const selectedService = ref('')
const selectedClusterId = ref('')

const showMockBadge = computed(() => DIAGNOSIS_USE_MOCK || ANALYSIS_USE_MOCK)
const diagnosisSeverity = computed(() => String(diagnosisResult.value?.severity ?? selectedCluster.value?.severity ?? '').toLowerCase())
const workbenchTone = computed(() => {
  if (['critical', 'high'].includes(diagnosisSeverity.value)) return 'red'
  if (diagnosisSeverity.value === 'medium') return 'amber'
  return 'blue'
})

const isDegraded = computed(() => {
  if (diagnosisResult.value?.degraded != null) return Boolean(diagnosisResult.value.degraded)
  const route = diagnosisResult.value?.route ?? diagnosisResult.value?.routing_result?.route
  return route === 'rule' || route === 'rule_only'
})

const affectedServices = computed(() => {
  const list = diagnosisResult.value?.affected_services
  const normalized = Array.isArray(list) ? list.map(String).filter(Boolean) : []
  return normalized.length ? normalized : [...new Set(ruleClusters.value.map((item) => item.service).filter(Boolean))]
})

const evidenceLogs = computed(() => {
  const list = diagnosisResult.value?.evidence_logs
  return Array.isArray(list) ? list : []
})

const suggestions = computed(() => {
  const raw = diagnosisResult.value?.suggestion ?? diagnosisResult.value?.suggestions ?? diagnosisResult.value?.action_suggestions
  if (!Array.isArray(raw)) return []
  return raw.map((item) => (typeof item === 'string' ? item : item?.detail || item?.title || '')).filter(Boolean)
})

const ruleClusters = computed(() => {
  const source = alerts.value.length ? alerts.value : fallbackAlerts.value
  const buckets = new Map()
  for (const alert of source) {
    const service = alert.affected_service || alert.service_name || alert.service || 'unknown-service'
    const rule = alert.alert_type || alert.rule_id || alert.title || 'rule-match'
    const severity = String(alert.severity || 'medium').toLowerCase()
    const key = `${service}|${rule}|${severity}`
    const current = buckets.get(key) || {
      id: key,
      title: rule,
      service,
      severity,
      count: 0,
      firstTs: Number.POSITIVE_INFINITY,
      lastTs: 0,
      reason: alert.description || alert.summary || '规则命中段持续聚集，建议结合证据日志定位触发字段。'
    }
    const ts = Date.parse(alert.created_at || alert.updated_at || '')
    current.count += 1
    if (Number.isFinite(ts)) {
      current.firstTs = Math.min(current.firstTs, ts)
      current.lastTs = Math.max(current.lastTs, ts)
    }
    buckets.set(key, current)
  }
  return [...buckets.values()]
    .sort((a, b) => severityWeight(b.severity) - severityWeight(a.severity) || b.count - a.count)
    .slice(0, 6)
    .map((item, index) => ({
      ...item,
      rank: `TOP ${index + 1}`,
      tone: item.severity === 'critical' || item.severity === 'high' ? 'red' : item.severity === 'medium' ? 'amber' : 'blue',
      window: formatWindow(item.firstTs, item.lastTs)
    }))
})

const selectedCluster = computed(() => ruleClusters.value.find((item) => item.id === selectedClusterId.value) || ruleClusters.value[0])

const displayTrace = computed(() => {
  if (nodeTrace.value.length) return nodeTrace.value
  return [
    { node_name: 'rule.fetch_context', status: 'completed', duration_ms: 220, output_summary: '汇总活跃预警与全局时间窗上下文' },
    { node_name: 'rule.cluster_hits', status: 'completed', duration_ms: 360, output_summary: `聚类 ${ruleClusters.value.length} 个规则命中段` },
    { node_name: 'rule.rank_top_k', status: 'completed', duration_ms: 180, output_summary: `输出 ${ruleClusters.value.length} 个 top_k 诊断候选` },
    { node_name: 'rule.assess_severity', status: selectedCluster.value?.tone === 'red' ? 'degraded' : 'completed', duration_ms: 140, output_summary: '根据命中密度、服务影响面和证据数定级' }
  ]
})

const confidencePercent = computed(() => {
  const raw = diagnosisResult.value?.confidence
  if (raw == null || Number.isNaN(Number(raw))) return isDegraded.value ? '40%' : '-'
  const num = Number(raw)
  return `${num <= 1 ? Math.round(num * 100) : Math.round(num)}%`
})

const kpiItems = computed(() => [
  { label: '规则聚类', value: ruleClusters.value.length, hint: 'rule clusters', tone: 'blue' },
  { label: 'TOP 风险', value: selectedCluster.value?.severity || diagnosisResult.value?.severity || '-', hint: selectedCluster.value?.service || 'selected cluster', tone: workbenchTone.value === 'red' ? 'red' : 'amber' },
  { label: '置信度', value: confidencePercent.value, hint: isDegraded.value ? '规则降级' : 'graph inference', tone: 'blue' },
  { label: '影响服务', value: affectedServices.value.length || '-', hint: affectedServices.value.slice(0, 2).join(' / '), tone: 'green' },
  { label: '推理节点', value: displayTrace.value.length, hint: 'node_trace', tone: 'blue' }
])

const subgraphNodes = computed(() => {
  const nodes = [{ id: 'rule-subgraph', label: '规则子图', tone: selectedCluster.value?.tone || 'blue', size: 58 }]
  for (const cluster of ruleClusters.value) {
    nodes.push({ id: cluster.id, label: `${cluster.rank} ${cluster.title}`, tone: cluster.tone, size: Math.min(60, 34 + cluster.count * 6) })
    nodes.push({ id: cluster.service, label: cluster.service, tone: cluster.service === selectedService.value ? 'warning' : 'slate', size: 34 })
  }
  return dedupeNodes(nodes)
})

const subgraphEdges = computed(() => {
  const edges = []
  for (const cluster of ruleClusters.value) {
    edges.push({ source: 'rule-subgraph', target: cluster.id, label: cluster.rank, weight: cluster.count, tone: cluster.tone === 'red' ? 'danger' : 'normal' })
    edges.push({ source: cluster.id, target: cluster.service, label: '影响服务', tone: cluster.tone === 'red' ? 'danger' : 'normal' })
  }
  return edges
})

const diagnosisPoints = computed(() =>
  ruleClusters.value.map((cluster, index) => ({
    id: cluster.id,
    label: cluster.service,
    type: cluster.title,
    severity: cluster.severity,
    count: cluster.count,
    time: Number.isFinite(cluster.lastTs) && cluster.lastTs > 0 ? cluster.lastTs : index,
    tone: cluster.tone
  }))
)

const fallbackAlerts = computed(() => [
  { alert_type: '订单服务多类型错误并发', severity: 'high', affected_service: 'order-service', created_at: new Date(Date.now() - 52 * 60_000).toISOString(), description: 'ERROR 与 timeout 在同一时间窗内共振。' },
  { alert_type: '支付回调延迟升高', severity: 'medium', affected_service: 'payment-service', created_at: new Date(Date.now() - 43 * 60_000).toISOString() },
  { alert_type: '库存扣减失败聚集', severity: 'high', affected_service: 'inventory-service', created_at: new Date(Date.now() - 31 * 60_000).toISOString() },
  { alert_type: '网关 5xx 抖动', severity: 'medium', affected_service: 'gateway', created_at: new Date(Date.now() - 18 * 60_000).toISOString() }
])

const RULE_SUBGRAPH_NODE_KEYS = new Set([
  'parse_trigger_event',
  'fetch_context',
  'correlate_events',
  'build_evidence',
  'infer_root_cause',
  'assess_severity',
  'generate_event_report'
])

function severityWeight(value) {
  const level = String(value || '').toLowerCase()
  return { critical: 4, high: 3, medium: 2, low: 1 }[level] || 0
}

function formatWindow(first, last) {
  if (!Number.isFinite(first) || !Number.isFinite(last) || !last) return 'live window'
  const minutes = Math.max(1, Math.round((last - first) / 60_000))
  return `${minutes} min`
}

function dedupeNodes(nodes) {
  const map = new Map()
  for (const node of nodes) {
    const existing = map.get(node.id)
    if (!existing || (node.size || 0) > (existing.size || 0)) map.set(node.id, node)
  }
  return [...map.values()]
}

function buildRequestKey(payload) {
  return [payload?.service_name, payload?.keyword, payload?.time_range_start, payload?.time_range_end, payload?.remark].join('|')
}

function enrichDiagnosis(diagnosis, input) {
  if (!diagnosis) return null
  const existing = Array.isArray(diagnosis.affected_services) ? diagnosis.affected_services.filter(Boolean) : []
  if (existing.length) return diagnosis
  const serviceName = input?.service_name?.trim()
  return serviceName ? { ...diagnosis, affected_services: [serviceName] } : diagnosis
}

function mapFacadeToDiagnosis(data) {
  const diagnosis = data?.diagnosis
  if (!diagnosis || typeof diagnosis !== 'object') return null
  const input = data?.input || {}
  return {
    ...diagnosis,
    title: diagnosis.title || diagnosis.anomaly_type || '单次规则诊断',
    summary: diagnosis.summary || diagnosis.root_cause || '',
    confidence: diagnosis.confidence ?? (diagnosis.route === 'rule' ? 0.4 : undefined),
    affected_services: Array.isArray(diagnosis.affected_services)
      ? diagnosis.affected_services
      : [input.service_name].filter(Boolean),
    degraded: diagnosis.degraded ?? ['rule', 'rule_only'].includes(diagnosis.route)
  }
}

function mapReportToDiagnosis(report) {
  if (!report || typeof report !== 'object') return null
  const ruleMatch = report.rule_match || {}
  return {
    anomaly_type: ruleMatch.rule_name || report.title || '事件异常分析',
    severity: report.severity || report.risk_level || 'medium',
    route: report.degraded ? 'rule' : 'langgraph',
    root_cause: report.root_cause || report.summary || '',
    confidence: report.confidence,
    summary: report.summary,
    title: report.title,
    affected_services: Array.isArray(report.affected_services) ? report.affected_services : [],
    suggestion: report.action_suggestions || report.recommendations || [],
    evidence_logs: Array.isArray(report.evidence_logs) ? report.evidence_logs : (report.evidence_refs || []),
    context_summary: {
      matched_rules: ruleMatch.rule_id ? [ruleMatch.rule_id] : [],
      rule_match: ruleMatch,
      trigger_event: report.trigger_event,
      degraded: report.degraded,
      similar_errors: report.similar_errors
    },
    degraded: report.degraded
  }
}

function normalizeStringList(value) {
  if (!Array.isArray(value)) return []
  return value
    .map((item) => {
      if (typeof item === 'string') return item.trim()
      if (item && typeof item === 'object') return String(item.name || item.key || item.service || item.title || item.detail || '').trim()
      return ''
    })
    .filter(Boolean)
}

function mapRunDataToDiagnosis(runData) {
  const decision = runData?.alert_decision
  if (!decision || typeof decision !== 'object') return null
  const candidate = decision.alert_candidate || {}
  const payload = candidate.payload || {}
  const explanation = typeof decision.explanation === 'object' ? decision.explanation : { detail: decision.explanation }
  const detail = explanation.detail || candidate.description || ''
  const evidenceRefs = normalizeStringList(payload.evidence_refs || candidate.evidence_refs)
  const affected = [candidate.affected_service, ...normalizeStringList(candidate.affected_services)].filter(Boolean)
  return {
    anomaly_type: candidate.alert_type || candidate.rule_id || payload.error_code || 'event',
    severity: candidate.severity || 'medium',
    route: 'langgraph',
    root_cause: detail || explanation.title || candidate.description || '',
    confidence: payload.confidence,
    summary: explanation.title || detail,
    title: explanation.title || candidate.title || '事件诊断报告',
    affected_services: [...new Set(affected)],
    suggestion: normalizeStringList(candidate.action_suggestions || candidate.suggestions || candidate.recommendations),
    evidence_logs: evidenceRefs,
    context_summary: {
      matched_rules: normalizeStringList([candidate.rule_id]),
      rule_match: { rule_id: candidate.rule_id, error_code: payload.error_code },
      trigger_event: { trigger_log_id: candidate.trigger_log_id, trace_id: payload.trace_id },
      degraded: false
    },
    degraded: false
  }
}

function filterRuleSubgraphTrace(trace) {
  if (!Array.isArray(trace) || !trace.length) return []
  const ruleNodes = trace.filter((entry) => {
    const name = String(entry?.node_name || '')
    if (name.startsWith('rule.')) return true
    const key = name.includes('.') ? name.split('.').pop() : name
    return RULE_SUBGRAPH_NODE_KEYS.has(key)
  })
  return ruleNodes.length ? ruleNodes : trace
}

async function fetchAnalysisReport(reportId) {
  if (!reportId) return null
  const { data } = await getReportDetail(reportId)
  return data?.report ?? null
}

async function runLangGraphAnalysis(payload) {
  loadingMessage.value = 'LangGraph 规则子图运行中：拉取上下文、构建证据并生成根因结论'
  nodeTrace.value = [{ node_name: 'rule.fetch_context', status: 'running', duration_ms: 0, output_summary: '正在拉取上下文日志' }]

  let runData = null
  try {
    const res = await triggerAnalysisRun({
      trigger_type: 'rule',
      trigger_event: { service_name: payload?.service_name, keyword: payload?.keyword },
      time_window: { start: payload?.time_range_start, end: payload?.time_range_end }
    })
    runData = res.data
  } catch (e) {
    if (e.error?.code === 'graph_failed') runData = e.response?.data?.data ?? null
    else throw e
  }

  const trace = filterRuleSubgraphTrace(runData?.node_trace ?? [])
  if (trace.length) nodeTrace.value = trace

  loadingMessage.value = '正在加载规则子图报告详情'
  const runDiagnosis = mapRunDataToDiagnosis(runData)
  let report = null
  try {
    report = await fetchAnalysisReport(runData?.report_id)
  } catch (e) {
    if (!runDiagnosis) throw e
  }
  if (!report && !runDiagnosis) throw new Error('规则子图已完成但未返回可展示报告')
  return { report, runDiagnosis, trace, errors: runData?.errors ?? [] }
}

async function runSingleDiagnosis(payload) {
  loadingMessage.value = '正在执行单次规则诊断'
  const res = await submitDiagnosis(payload)
  return mapFacadeToDiagnosis(res.data)
}

async function enrichWithGraphAnalysis(payload, requestKey) {
  graphLoading.value = true
  loadingMessage.value = '单次规则诊断已完成，正在补充 LangGraph 规则子图分析'
  try {
    const { report, runDiagnosis, trace, errors } = await runLangGraphAnalysis(payload)
    if (activeRequestKey.value !== requestKey) return
    const graphDiagnosis = enrichDiagnosis(mapReportToDiagnosis(report) || runDiagnosis, payload)
    if (graphDiagnosis?.root_cause || graphDiagnosis?.summary) {
      diagnosisResult.value = graphDiagnosis
    }
    if (trace.length) nodeTrace.value = trace
    if (errors?.length && !diagnosisResult.value?.root_cause) {
      errorMessage.value = '规则子图部分节点失败，已展示单次规则诊断结论'
    }
  } catch (e) {
    if (activeRequestKey.value !== requestKey) return
    const code = e.error?.code
    if (code === 'graph_failed' || code === 'query_failed') {
      errorMessage.value = '单次规则诊断已完成；LangGraph 规则子图补充分析暂不可用'
      return
    }
    errorMessage.value = e.error?.message || e.message || '单次规则诊断已完成；LangGraph 规则子图补充分析失败'
  } finally {
    if (activeRequestKey.value === requestKey) graphLoading.value = false
  }
}

async function handleSubmit(payload) {
  const requestKey = buildRequestKey(payload)
  if ((loading.value || graphLoading.value) && requestKey === activeRequestKey.value) return

  loading.value = true
  graphLoading.value = false
  errorMessage.value = ''
  lastPayload.value = payload
  activeRequestKey.value = requestKey
  diagnosisResult.value = null

  try {
    const singleDiagnosis = await runSingleDiagnosis(payload)
    diagnosisResult.value = enrichDiagnosis(singleDiagnosis, payload)
    nodeTrace.value = []
  } catch (e) {
    diagnosisResult.value = null
    nodeTrace.value = []
    const code = e.error?.code
    if (code === 'diagnosis_failed') errorMessage.value = e.error?.message || '单次规则诊断失败'
    else errorMessage.value = e.error?.message || e.message || '单次规则诊断请求失败'
    return
  } finally {
    loading.value = false
  }

  await enrichWithGraphAnalysis(payload, requestKey)
}

async function loadAlerts() {
  try {
    const res = await getActiveAlerts({ limit: 80 })
    alerts.value = res.data?.items ?? []
    selectedClusterId.value = ruleClusters.value[0]?.id || ''
  } catch {
    alerts.value = []
    selectedClusterId.value = ruleClusters.value[0]?.id || ''
  }
}

onMounted(loadAlerts)
</script>

<style scoped>
.diagnosis-badge {
  padding: 4px 9px;
  color: #c3a06d;
  background: rgba(178, 139, 90, 0.12);
  border: 1px solid rgba(178, 139, 90, 0.42);
  border-radius: 2px;
  font-size: 12px;
  font-weight: 900;
}

.diagnosis-status {
  position: relative;
  z-index: 1;
  margin-bottom: 10px;
  padding: 9px 11px;
  color: #c9dde2;
  background: rgba(111, 158, 172, 0.1);
  border: 1px solid rgba(111, 158, 172, 0.32);
  border-radius: 3px;
}

.diagnosis-status--error {
  color: #e2b8b2;
  background: rgba(185, 106, 97, 0.12);
  border-color: rgba(185, 106, 97, 0.42);
}

.diagnosis-reasoning {
  margin-bottom: 10px;
}

.diagnosis-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  grid-template-rows: auto auto auto;
  grid-template-areas:
    'upper upper'
    'single side'
    'evidence evidence';
  gap: 10px;
  align-items: stretch;
}

.diagnosis-grid__upper {
  grid-area: upper;
  display: grid;
  grid-template-rows: minmax(210px, 2fr) minmax(320px, 3fr);
  gap: 10px;
  min-height: 560px;
  max-height: min(720px, 62vh);
  overflow: hidden;
}

.diagnosis-single {
  grid-area: single;
  margin: 0;
  display: flex;
  flex-direction: column;
  min-height: 430px;
}

.diagnosis-single :deep(.suggestion-panel) {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 0;
  border: 0;
}

.diagnosis-single :deep(.stage-section) {
  flex: 1 1 auto;
  min-height: 0;
}

.diagnosis-grid__side {
  grid-area: side;
  margin: 0;
  padding: 10px;
  box-sizing: border-box;
  align-self: stretch;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.diagnosis-evidence {
  grid-area: evidence;
}

.diagnosis-evidence > .ak-panel {
  min-height: 0;
}

.diagnosis-grid__side :deep(.entry-panel) {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
}

.diagnosis-overview,
.diagnosis-visual,
.diagnosis-evidence {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(340px, 0.75fr);
  gap: 10px;
  min-height: 0;
  overflow: hidden;
}

.diagnosis-grid__upper .diagnosis-overview,
.diagnosis-grid__upper .diagnosis-visual {
  min-height: 0;
  max-height: 100%;
  overflow: hidden;
}

.diagnosis-overview > .ak-panel,
.diagnosis-visual > .ak-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  max-height: 100%;
  overflow: hidden;
}

.diagnosis-overview > .ak-panel .cluster-rank {
  flex: 1 1 auto;
  min-height: 0;
  grid-auto-rows: minmax(76px, 1fr);
  align-content: stretch;
  overflow: auto;
}

.diagnosis-overview > .ak-panel .risk-strip {
  flex: 1;
  justify-content: space-between;
}

.diagnosis-visual :deep(.g6-graph),
.diagnosis-visual :deep(.digital-twin) {
  flex: 1 1 auto;
  min-height: 0;
  max-height: 100%;
  overflow: hidden;
}

.evidence-scroll {
  max-height: 320px;
  overflow-y: auto;
  padding-right: 6px;
  scrollbar-color: rgba(111, 158, 172, 0.58) rgba(185, 196, 207, 0.08);
  scrollbar-width: thin;
}

.evidence-scroll::-webkit-scrollbar {
  width: 8px;
}

.evidence-scroll::-webkit-scrollbar-track {
  background: rgba(185, 196, 207, 0.08);
}

.evidence-scroll::-webkit-scrollbar-thumb {
  background: rgba(111, 158, 172, 0.58);
  border-radius: 999px;
}

.cluster-rank {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 7px;
}

.cluster-rank__item {
  --cluster-accent: #6f9eac;
  min-height: 76px;
  height: 100%;
  padding: 9px;
  color: #dce4eb;
  background: rgba(7, 10, 14, 0.56);
  border: 1px solid rgba(185, 196, 207, 0.16);
  border-left: 3px solid var(--cluster-accent);
  border-radius: 2px;
  text-align: left;
  cursor: pointer;
}

.cluster-rank__item--red {
  --cluster-accent: #b96a61;
}

.cluster-rank__item--amber {
  --cluster-accent: #b28b5a;
}

.cluster-rank__item.active,
.cluster-rank__item:hover {
  border-color: color-mix(in srgb, var(--cluster-accent) 58%, rgba(185, 196, 207, 0.18));
}

.cluster-rank__item span,
.cluster-rank__item small {
  display: block;
  overflow: hidden;
  color: #8e9aa6;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cluster-rank__item strong {
  display: block;
  margin: 5px 0;
  overflow: hidden;
  color: #f2f5f7;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.single-result {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 12px;
}

.diagnosis-evidence .single-result {
  grid-template-columns: 1fr;
}

.single-result__text h3 {
  margin: 0 0 8px;
  color: #f2f5f7;
  font-size: 16px;
}

.single-result__text p {
  margin: 0;
  color: #aab4bf;
  font-size: 13px;
  line-height: 1.6;
}

.single-result__suggestions {
  padding-top: 12px;
  border-top: 1px dashed rgba(185, 196, 207, 0.18);
}

.single-result__suggestions h3 {
  margin: 0 0 10px;
  color: #f2f5f7;
  font-size: 14px;
}

.diagnosis-grid :deep(.page-section) {
  margin-bottom: 0;
  background: transparent;
  border-color: rgba(185, 196, 207, 0.16);
  box-shadow: none;
}

.diagnosis-grid :deep(.page-section:hover) {
  transform: none;
}

@media (max-width: 1280px) {
  .diagnosis-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
    grid-template-areas:
      'upper'
      'single'
      'side'
      'evidence';
  }

  .diagnosis-grid__upper {
    min-height: 0;
    grid-template-rows: auto auto;
  }

  .diagnosis-overview,
  .diagnosis-visual,
  .diagnosis-evidence,
  .single-result {
    grid-template-columns: 1fr;
  }

  .diagnosis-overview > .ak-panel,
  .diagnosis-visual > .ak-panel {
    height: auto;
  }

  .cluster-rank {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .cluster-rank {
    grid-template-columns: 1fr;
  }
}
</style>
