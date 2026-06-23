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
      正在分析，请稍候…
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
import { submitDiagnosis, USE_MOCK as DIAGNOSIS_USE_MOCK } from '../../api/diagnosis.js'
import { triggerAnalysisRun, USE_MOCK as ANALYSIS_USE_MOCK } from '../../api/analysis.js'
import { getActiveAlerts } from '../../api/alerts.js'

const loading = ref(false)
const errorMessage = ref('')
const diagnosisResult = ref(null)
const nodeTrace = ref([])
const alerts = ref([])
const lastPayload = ref(null)

const showMockBadge = computed(() => DIAGNOSIS_USE_MOCK || ANALYSIS_USE_MOCK)

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

async function fetchNodeTrace(payload) {
  try {
    const res = await triggerAnalysisRun({
      trigger_type: 'rule',
      trigger_event: {
        service_name: payload?.service_name,
        keyword: payload?.keyword
      }
    })
    return res.data?.node_trace ?? []
  } catch (e) {
    if (e.error?.code === 'graph_failed') {
      return e.response?.data?.data?.node_trace ?? []
    }
    return []
  }
}

async function handleSubmit(payload) {
  loading.value = true
  errorMessage.value = ''
  lastPayload.value = payload
  nodeTrace.value = [
    { node_name: 'fetch_context', status: 'running', duration_ms: 0 }
  ]

  try {
    const { data } = await submitDiagnosis(payload)
    diagnosisResult.value = enrichDiagnosis(data?.diagnosis, data?.input)
    loading.value = false

    fetchNodeTrace(payload)
      .then((trace) => {
        if (Array.isArray(trace) && trace.length) {
          nodeTrace.value = trace
          return
        }
        nodeTrace.value = [
          { node_name: 'fetch_context', status: 'success', duration_ms: 0 },
          { node_name: 'rule_diagnose', status: 'success', duration_ms: 0 },
          { node_name: 'assess_severity', status: 'success', duration_ms: 0 },
          { node_name: 'generate_event_report', status: 'success', duration_ms: 0 }
        ]
      })
      .catch(() => {
        nodeTrace.value = [
          { node_name: 'fetch_context', status: 'success', duration_ms: 0 },
          { node_name: 'rule_diagnose', status: 'success', duration_ms: 0 },
          { node_name: 'assess_severity', status: 'success', duration_ms: 0 },
          { node_name: 'generate_event_report', status: 'success', duration_ms: 0 }
        ]
      })
  } catch (e) {
    diagnosisResult.value = null
    nodeTrace.value = []
    const code = e.error?.code
    if (code === 'diagnosis_failed') {
      errorMessage.value = e.error?.message || '诊断失败，请检查输入后重试'
    } else {
      errorMessage.value = e.error?.message || e.message || '诊断请求失败'
    }
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
