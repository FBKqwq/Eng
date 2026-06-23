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
          <ParticleBackdrop
            class="diagnosis-page__conclusion-backdrop"
            variant="diagnosis"
            :intensity="diagnosisBackdropIntensity"
            :accent-color="diagnosisAccentColor"
          />
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
          :node-trace="nodeTrace"
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
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 11px;
  line-height: 1.4;
}

.diagnosis-page__status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  font-size: 13px;
  line-height: 1.5;
}

.diagnosis-page__status--loading {
  border: 1px solid var(--color-border);
  background: var(--color-info-bg, var(--color-bg));
  color: var(--color-text-secondary);
}

.diagnosis-page__status--error {
  border: 1px solid var(--color-danger);
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.retry-btn {
  flex-shrink: 0;
  padding: 4px 10px;
  border: 1px solid currentColor;
  border-radius: var(--radius-sm);
  background: transparent;
  color: inherit;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.retry-btn:hover {
  opacity: 0.85;
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
  border-radius: var(--radius-md);
  overflow: hidden;
}

.diagnosis-page__conclusion-backdrop {
  border-radius: var(--radius-md);
}

.diagnosis-page__conclusion-content {
  position: relative;
  z-index: 1;
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
