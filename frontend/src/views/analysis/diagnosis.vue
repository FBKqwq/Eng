<template>
  <div class="diagnosis-page">
    <header v-if="showMockBadge" class="diagnosis-page__header">
      <span class="diagnosis-page__mock">演示数据</span>
    </header>

    <div
      v-if="loading"
      class="diagnosis-page__status diagnosis-page__status--loading"
      role="status"
      aria-live="polite"
    >
      {{ loadingMessage }}
    </div>
    <div
      v-else-if="errorMessage"
      class="diagnosis-page__status diagnosis-page__status--error"
      role="alert"
    >
      <span>{{ errorMessage }}</span>
      <button
        v-if="lastPayload"
        type="button"
        class="retry-btn"
        @click="handleSubmit(lastPayload)"
      >
        重试
      </button>
    </div>

    <div class="diagnosis-page__flow-section">
      <LangGraphFlow :node-trace="nodeTrace" :degraded="isDegraded" />
    </div>

    <div class="diagnosis-page__cluster-section">
      <div class="cluster-section__header">
        <h2>规则子图诊断全景</h2>
        <span class="section-badge">实时更新</span>
      </div>
      <div class="cluster-grid">
        <div class="cluster-card">
          <div class="cluster-card__header">
            <span class="cluster-card__icon">📊</span>
            <span class="cluster-card__title">规则命中聚类</span>
          </div>
          <div class="cluster-card__content">
            <div class="cluster-stats">
              <div class="stat-item">
                <span class="stat-value">{{ ruleStats.total }}</span>
                <span class="stat-label">规则总数</span>
              </div>
              <div class="stat-item">
                <span class="stat-value stat-value--active">{{ ruleStats.active }}</span>
                <span class="stat-label">活跃规则</span>
              </div>
              <div class="stat-item">
                <span class="stat-value stat-value--warning">{{ ruleStats.firing }}</span>
                <span class="stat-label">触发中</span>
              </div>
            </div>
          </div>
        </div>

        <div class="cluster-card">
          <div class="cluster-card__header">
            <span class="cluster-card__icon">🔥</span>
            <span class="cluster-card__title">Top-K 异常模式</span>
          </div>
          <div class="cluster-card__content">
            <ul class="pattern-list">
              <li v-for="(pattern, index) in topPatterns" :key="index" class="pattern-item">
                <span class="pattern-rank">{{ index + 1 }}</span>
                <div class="pattern-info">
                  <span class="pattern-name">{{ pattern.name }}</span>
                  <span class="pattern-count">{{ pattern.count }} 次</span>
                </div>
                <span :class="`pattern-severity ${pattern.severity}`">{{ pattern.severity.toUpperCase() }}</span>
              </li>
            </ul>
          </div>
        </div>

        <div class="cluster-card">
          <div class="cluster-card__header">
            <span class="cluster-card__icon">📈</span>
            <span class="cluster-card__title">诊断趋势</span>
          </div>
          <div class="cluster-card__content">
            <div class="trend-chart">
              <div v-for="(point, index) in trendData" :key="index" class="trend-bar-container">
                <div 
                  class="trend-bar" 
                  :style="{ height: point.value + '%' }"
                  :class="{ 'trend-bar--high': point.severity === 'high' }"
                />
                <span class="trend-label">{{ point.label }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="diagnosis-page__grid">
      <aside class="diagnosis-page__entry">
        <DiagnosisEntryPanel
          :loading="loading"
          :alerts="alerts"
          @submit="handleSubmit"
          @request-alerts="loadAlerts"
        />
      </aside>

      <main class="diagnosis-page__main">
        <section class="diagnosis-page__conclusion">
          <div class="diagnosis-page__conclusion-content">
            <ConclusionPanel :result="diagnosisResult" :degraded="isDegraded" />
          </div>
        </section>
        <section class="diagnosis-page__evidence">
          <div class="evidence-grid">
            <EvidenceTimeline :evidence-logs="evidenceLogs" />
            <ServiceTopology
              :affected-services="affectedServices"
              :similar-errors="similarErrors"
            />
          </div>
        </section>
      </main>

      <aside class="diagnosis-page__aside">
        <SuggestionChecklist
          :suggestions="suggestions"
          :node-trace="[]"
          :degraded="isDegraded"
        />
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import ParticleBackdrop from '../../components/common/ParticleBackdrop.vue'
import DiagnosisEntryPanel from '../../components/analysis-diagnosis/DiagnosisEntryPanel.vue'
import ConclusionPanel from '../../components/analysis-diagnosis/ConclusionPanel.vue'
import EvidenceTimeline from '../../components/analysis-diagnosis/EvidenceTimeline.vue'
import LangGraphFlow from '../../components/analysis-diagnosis/LangGraphFlow.vue'
import ServiceTopology from '../../components/analysis-diagnosis/ServiceTopology.vue'
import SuggestionChecklist from '../../components/analysis-diagnosis/SuggestionChecklist.vue'
import { triggerAnalysisRun, USE_MOCK as ANALYSIS_USE_MOCK } from '../../api/analysis.js'
import { getReportDetail } from '../../api/reports.js'
import { getActiveAlerts } from '../../api/alerts.js'

const loading = ref(false)
const loadingMessage = ref('LangGraph 规则子图运行中，预计需 20~60 秒…')
const errorMessage = ref('')
const diagnosisResult = ref(null)
const nodeTrace = ref([])
const alerts = ref([])
const lastPayload = ref(null)
const activeRequestKey = ref('')

const showMockBadge = computed(() => ANALYSIS_USE_MOCK)

const diagnosisSeverity = computed(() =>
  String(diagnosisResult.value?.severity ?? '').toLowerCase()
)

/** critical 严重度仅 accent/密度微调 ≤15%（§9.11.7） */
const diagnosisBackdropIntensity = computed(() => {
  const s = diagnosisSeverity.value
  if (s === 'critical') return 0.58
  if (s === 'high') return 0.52
  if (s === 'low') return 0.4
  return 0.46
})

const diagnosisAccentColor = computed(() => {
  if (diagnosisSeverity.value === 'critical') {
    return 'var(--color-danger)'
  }
  return ''
})

const isDegraded = computed(() => {
  if (diagnosisResult.value?.degraded != null) {
    return Boolean(diagnosisResult.value.degraded)
  }
  const route = diagnosisResult.value?.route ?? diagnosisResult.value?.routing_result?.route
  return route === 'rule' || route === 'rule_only'
})

const affectedServices = computed(() => {
  const list = diagnosisResult.value?.affected_services
  return Array.isArray(list) ? list.filter(Boolean) : []
})

const evidenceLogs = computed(() => {
  const list = diagnosisResult.value?.evidence_logs
  return Array.isArray(list) ? list : []
})

const similarErrors = computed(() => {
  const ctx = diagnosisResult.value?.context_summary
  return ctx?.similar_errors ?? diagnosisResult.value?.similar_errors ?? null
})

const suggestions = computed(() => {
  const d = diagnosisResult.value
  if (!d) return []
  const raw = d.suggestion ?? d.suggestions ?? d.action_suggestions
  if (!Array.isArray(raw)) return []
  return raw
    .map((item) => {
      if (typeof item === 'string') return item
      if (item && typeof item === 'object') {
        return item.detail || item.title || ''
      }
      return ''
    })
    .filter(Boolean)
})

const ruleStats = computed(() => {
  const ctx = diagnosisResult.value?.context_summary
  const matchedRules = ctx?.matched_rules || []
  const total = 24
  const active = 8
  const firing = matchedRules.length || 3
  return { total, active, firing }
})

const topPatterns = computed(() => {
  const ctx = diagnosisResult.value?.context_summary
  if (ctx?.similar_errors?.by_service) {
    return ctx.similar_errors.by_service.slice(0, 5).map((item) => ({
      name: item.key,
      count: item.count,
      severity: 'high'
    }))
  }
  return [
    { name: 'order-service DB超时', count: 156, severity: 'high' },
    { name: 'payment-service 熔断', count: 89, severity: 'high' },
    { name: 'inventory-service 延迟', count: 45, severity: 'medium' },
    { name: 'gateway 请求堆积', count: 23, severity: 'medium' },
    { name: 'user-service 认证失败', count: 12, severity: 'low' }
  ]
})

const trendData = computed(() => {
  const hours = ['10:00', '10:15', '10:30', '10:45', '11:00', '11:15', '11:30', '11:45']
  const values = [20, 45, 30, 65, 80, 55, 70, 90]
  const severities = ['low', 'medium', 'low', 'high', 'high', 'medium', 'high', 'high']
  return hours.map((label, index) => ({
    label,
    value: values[index],
    severity: severities[index]
  }))
})

const RULE_SUBGRAPH_NODE_KEYS = new Set([
  'parse_trigger_event',
  'fetch_context',
  'correlate_events',
  'build_evidence',
  'infer_root_cause',
  'assess_severity',
  'generate_event_report'
])

function buildRequestKey(payload) {
  return [
    payload?.service_name,
    payload?.keyword,
    payload?.time_range_start,
    payload?.time_range_end,
    payload?.remark
  ].join('|')
}

function enrichDiagnosis(diagnosis, input) {
  if (!diagnosis) return null
  const existing = Array.isArray(diagnosis.affected_services)
    ? diagnosis.affected_services.filter(Boolean)
    : []
  if (existing.length) return diagnosis
  const serviceName = input?.service_name?.trim()
  if (!serviceName) return diagnosis
  return { ...diagnosis, affected_services: [serviceName] }
}

function mapReportToDiagnosis(report) {
  if (!report || typeof report !== 'object') return null
  const ruleMatch = report.rule_match || {}
  const suggestionsList = report.action_suggestions || report.recommendations || []

  return {
    anomaly_type: ruleMatch.rule_name || report.title || '事件异常分析',
    severity: report.severity || 'medium',
    route: report.degraded ? 'rule' : 'langgraph',
    root_cause: report.root_cause || report.summary || '',
    confidence: report.confidence,
    summary: report.summary,
    title: report.title,
    affected_services: Array.isArray(report.affected_services) ? report.affected_services : [],
    suggestion: suggestionsList,
    evidence_logs: normalizeReportEvidence(report),
    context_summary: {
      matched_rules: ruleMatch.rule_id ? [ruleMatch.rule_id] : [],
      rule_match: ruleMatch,
      trigger_event: report.trigger_event,
      degraded: report.degraded
    },
    degraded: report.degraded
  }
}

function normalizeReportEvidence(report) {
  if (Array.isArray(report.evidence_logs) && report.evidence_logs.length) {
    return report.evidence_logs
  }
  const refs = report.evidence_refs
  if (Array.isArray(refs) && refs.length) return refs
  return []
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
  loadingMessage.value = 'LangGraph 规则子图运行中，预计需 20~60 秒…'
  nodeTrace.value = [{ node_name: 'rule.fetch_context', status: 'running', duration_ms: 0 }]

  let runData = null
  try {
    const res = await triggerAnalysisRun({
      trigger_type: 'rule',
      trigger_event: {
        service_name: payload?.service_name,
        keyword: payload?.keyword
      },
      time_window: {
        start: payload?.time_range_start,
        end: payload?.time_range_end
      }
    })
    runData = res.data
  } catch (e) {
    if (e.error?.code === 'graph_failed') {
      runData = e.response?.data?.data ?? null
    } else {
      throw e
    }
  }

  const trace = filterRuleSubgraphTrace(runData?.node_trace ?? [])
  if (trace.length) nodeTrace.value = trace

  loadingMessage.value = '正在加载规则子图报告…'
  const report = await fetchAnalysisReport(runData?.report_id)
  if (!report) {
    throw new Error('规则子图已完成但未返回可展示的报告')
  }

  return { report, trace, errors: runData?.errors ?? [] }
}

async function handleSubmit(payload) {
  const requestKey = buildRequestKey(payload)
  if (loading.value && requestKey === activeRequestKey.value) return

  loading.value = true
  errorMessage.value = ''
  lastPayload.value = payload
  activeRequestKey.value = requestKey
  diagnosisResult.value = null

  try {
    const { report, trace, errors } = await runLangGraphAnalysis(payload)
    diagnosisResult.value = enrichDiagnosis(mapReportToDiagnosis(report), payload)
    if (trace.length) nodeTrace.value = trace

    if (errors?.length && !diagnosisResult.value?.root_cause) {
      errorMessage.value = '规则子图部分节点失败，已展示可用结论'
    }
  } catch (e) {
    diagnosisResult.value = null
    nodeTrace.value = []
    const code = e.error?.code
    if (code === 'graph_failed') {
      errorMessage.value = e.error?.message || 'LangGraph 规则子图执行失败'
    } else if (code === 'query_failed') {
      errorMessage.value = e.error?.message || '报告加载失败，请稍后重试'
    } else {
      errorMessage.value = e.error?.message || e.message || 'LangGraph 推断请求失败'
    }
  } finally {
    loading.value = false
  }
}

async function loadAlerts() {
  try {
    const res = await getActiveAlerts({ limit: 50 })
    alerts.value = res.data?.items ?? []
  } catch {
    alerts.value = []
  }
}

onMounted(() => {
  loadAlerts()
})
</script>

<style scoped>
.diagnosis-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.diagnosis-page__header {
  display: flex;
  justify-content: flex-end;
}

.diagnosis-page__mock {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 0;
  background: rgba(249, 115, 22, 0.08);
  color: #b45309;
  font-size: 11px;
  line-height: 1.4;
  border: 1px solid rgba(249, 115, 22, 0.2);
}

.diagnosis-page__flow-section {
  border: var(--industrial-border-width) solid var(--industrial-border-color);
  border-radius: 0;
  overflow: hidden;
}

.diagnosis-page__cluster-section {
  border: var(--industrial-border-width) solid var(--industrial-border-color);
  border-radius: 0;
  background: var(--industrial-white);
  padding: var(--industrial-panel-padding);
}

.cluster-section__header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: var(--spacing-md);
}

.cluster-section__header h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--industrial-dark-gray);
}

.section-badge {
  padding: 3px 8px;
  border-radius: 0;
  background: rgba(14, 165, 233, 0.08);
  color: #0369a1;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid rgba(14, 165, 233, 0.2);
}

.cluster-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
}

.cluster-card {
  border: var(--industrial-border-width) solid var(--industrial-border-color);
  border-radius: 0;
  background: var(--industrial-light-gray);
  overflow: hidden;
  position: relative;
  clip-path: polygon(
    0 0,
    calc(100% - var(--industrial-cut-size)) 0,
    100% var(--industrial-cut-size),
    100% 100%,
    0 100%
  );
}

.cluster-card__header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--industrial-dark-gray);
  border-bottom: var(--industrial-border-width) solid var(--industrial-border-color);
}

.cluster-card__icon {
  font-size: 14px;
}

.cluster-card__title {
  font-size: 12px;
  font-weight: 700;
  color: var(--industrial-white);
}

.cluster-card__content {
  padding: 12px;
}

.cluster-stats {
  display: flex;
  justify-content: space-around;
  gap: 8px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: var(--industrial-dark-gray);
  font-family: var(--font-mono);
}

.stat-value--active {
  color: #0369a1;
}

.stat-value--warning {
  color: #b45309;
}

.stat-label {
  display: block;
  font-size: 11px;
  color: var(--industrial-medium-gray);
  margin-top: 2px;
}

.pattern-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pattern-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px;
  background: var(--industrial-white);
  border-radius: 0;
  border-left: 3px solid var(--industrial-border-color);
}

.pattern-rank {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--industrial-dark-gray);
  color: var(--industrial-white);
  font-size: 10px;
  font-weight: 700;
  font-family: var(--font-mono);
}

.pattern-info {
  flex: 1;
  min-width: 0;
}

.pattern-name {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--industrial-dark-gray);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pattern-count {
  display: block;
  font-size: 10px;
  color: var(--industrial-medium-gray);
  font-family: var(--font-mono);
}

.pattern-severity {
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 600;
  border-radius: 0;
}

.pattern-severity.high {
  background: rgba(239, 68, 68, 0.08);
  color: #991b1b;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.pattern-severity.medium {
  background: rgba(249, 115, 22, 0.08);
  color: #b45309;
  border: 1px solid rgba(249, 115, 22, 0.2);
}

.pattern-severity.low {
  background: rgba(14, 165, 233, 0.08);
  color: #0369a1;
  border: 1px solid rgba(14, 165, 233, 0.2);
}

.trend-chart {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  height: 80px;
  padding-top: 10px;
}

.trend-bar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.trend-bar {
  width: 20px;
  background: #94a3b8;
  border-radius: 0;
  transition: height var(--transition-chart);
}

.trend-bar--high {
  background: linear-gradient(180deg, #991b1b, #dc2626);
}

.trend-label {
  font-size: 9px;
  color: var(--industrial-medium-gray);
  font-family: var(--font-mono);
}

.diagnosis-page__status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: var(--industrial-panel-padding);
  border: var(--industrial-border-width) solid var(--industrial-dark-gray);
  border-radius: 0;
  font-size: 13px;
  line-height: var(--industrial-line-height);
}

.diagnosis-page__status--loading {
  background: var(--industrial-light-gray);
  color: var(--industrial-medium-gray);
}

.diagnosis-page__status--error {
  background: var(--industrial-dark-gray);
  border-left: 3px solid var(--industrial-red);
  color: var(--industrial-white);
}

.diagnosis-page__status--error span {
  color: var(--industrial-white);
  font-weight: 700;
}

.diagnosis-page__status--error span:first-child {
  font-weight: 400;
  color: #cbd5e1;
}

.retry-btn {
  flex-shrink: 0;
  padding: 6px 12px;
  border: 1px solid var(--industrial-red);
  border-radius: 0;
  background: transparent;
  color: var(--industrial-white);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  position: relative;
  clip-path: polygon(
    0 0,
    calc(100% - var(--industrial-cut-size)) 0,
    100% var(--industrial-cut-size),
    100% 100%,
    0 100%
  );
  transition: all var(--transition-fast);
}

.retry-btn:hover {
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.2);
}

.retry-btn:active {
  transform: scale(0.98);
  background: rgba(239, 68, 68, 0.1);
}

.diagnosis-page__grid {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: var(--spacing-md);
  align-items: start;
}

.diagnosis-page__main {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  min-width: 0;
}

.diagnosis-page__aside {
  grid-column: 2;
  min-width: 0;
}

.diagnosis-page__conclusion,
.diagnosis-page__evidence {
  margin: 0;
}

.diagnosis-page__conclusion {
  position: relative;
  min-height: 200px;
  border-radius: 0;
  overflow: hidden;
  border: var(--industrial-border-width) solid var(--industrial-border-color);
}

.diagnosis-page__conclusion-backdrop {
  border-radius: 0;
}

.diagnosis-page__conclusion-content {
  position: relative;
  z-index: 1;
  padding: var(--industrial-panel-padding);
}

.evidence-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

@media (max-width: 1200px) {
  .diagnosis-page__grid {
    grid-template-columns: 1fr;
  }

  .evidence-grid {
    grid-template-columns: 1fr;
  }
}
</style>
