<template>
  <div class="diagnosis-page">
    <header v-if="showMockBadge" class="diagnosis-page__header">
      <span class="diagnosis-page__mock">演示数据</span>
    </header>

    <div class="diagnosis-page__grid">
      <!-- 左侧栏：规则子图总览 -->
      <aside class="diagnosis-page__sidebar">
        <RuleSubgraphPanel
          :diagnoses="ruleDiagnoses"
          :last-run-at="lastRunAt"
          @select="handleSelectDiagnosis"
        />
      </aside>

      <!-- 主内容区 -->
      <main class="diagnosis-page__main">
        <!-- 单条诊断详情 -->
        <section class="diagnosis-page__section">
          <div
            v-if="detailLoading"
            class="diagnosis-page__status diagnosis-page__status--loading"
            role="status"
            aria-live="polite"
          >
            正在分析，请稍候…
          </div>
          <div
            v-else-if="detailError"
            class="diagnosis-page__status diagnosis-page__status--error"
            role="alert"
          >
            <span>{{ detailError }}</span>
            <button
              v-if="selectedDiagnosis"
              type="button"
              class="retry-btn"
              @click="handleSelectDiagnosis(selectedDiagnosis)"
            >
              重试
            </button>
          </div>

          <template v-else-if="diagnosisResult">
            <!-- 结论区 -->
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

            <!-- 证据区 -->
            <section class="diagnosis-page__evidence">
              <div class="evidence-grid">
                <EvidenceTimeline :evidence-logs="evidenceLogs" />
                <ServiceTopology
                  :affected-services="affectedServices"
                  :similar-errors="similarErrors"
                />
              </div>
            </section>
          </template>

          <EmptyState
            v-else
            compact
            title="请选择一条规则诊断"
            description="从左侧规则命中明细中点击查看具体诊断结论与证据"
          />
        </section>
      </main>

      <!-- 右侧栏：建议区 -->
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
import EmptyState from '../../components/common/EmptyState.vue'
import RuleSubgraphPanel from '../../components/analysis-diagnosis/RuleSubgraphPanel.vue'
import ConclusionPanel from '../../components/analysis-diagnosis/ConclusionPanel.vue'
import EvidenceTimeline from '../../components/analysis-diagnosis/EvidenceTimeline.vue'
import ServiceTopology from '../../components/analysis-diagnosis/ServiceTopology.vue'
import SuggestionChecklist from '../../components/analysis-diagnosis/SuggestionChecklist.vue'
import {
  submitDiagnosis,
  USE_MOCK as DIAGNOSIS_USE_MOCK
} from '../../api/diagnosis.js'
import {
  triggerAnalysisRun,
  USE_MOCK as ANALYSIS_USE_MOCK
} from '../../api/analysis.js'
import { getActiveAlerts } from '../../api/alerts.js'

const showMockBadge = computed(
  () => DIAGNOSIS_USE_MOCK || ANALYSIS_USE_MOCK
)

// 规则子图结果（聚类列表 + 整体图谱）
const ruleDiagnoses = ref([])
const lastRunAt = ref('')
const selectedDiagnosis = ref(null)

// 单条诊断详情
const detailLoading = ref(false)
const detailError = ref('')
const diagnosisResult = ref(null)
const nodeTrace = ref([])

const diagnosisSeverity = computed(() =>
  String(diagnosisResult.value?.severity ?? '').toLowerCase()
)

const diagnosisBackdropIntensity = computed(() => {
  const s = diagnosisSeverity.value
  if (s === 'critical') return 0.58
  if (s === 'high') return 0.52
  if (s === 'low') return 0.4
  return 0.46
})

const diagnosisAccentColor = computed(() => {
  if (diagnosisSeverity.value === 'critical') return 'var(--color-danger)'
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

// 加载规则子图结果
async function loadRuleSubgraph() {
  // 演示数据：模拟规则诊断聚类结果
  if (DIAGNOSIS_USE_MOCK || ANALYSIS_USE_MOCK) {
    ruleDiagnoses.value = [
      { id: 'r001', rule_name: 'order-service 超时检测', service: 'order-service', severity: 'high', hit_count: 47, time_window: '近 1 小时', status: 'active' },
      { id: 'r002', rule_name: 'payment 错误率激增', service: 'payment-service', severity: 'critical', hit_count: 23, time_window: '近 30 分钟', status: 'active' },
      { id: 'r003', rule_name: 'gateway 延迟告警', service: 'gateway', severity: 'medium', hit_count: 12, time_window: '近 1 小时', status: 'active' },
      { id: 'r004', rule_name: 'inventory 库存预警', service: 'inventory-service', severity: 'low', hit_count: 5, time_window: '近 6 小时', status: 'resolved' },
      { id: 'r005', rule_name: 'user-service 认证异常', service: 'user-service', severity: 'medium', hit_count: 8, time_window: '近 2 小时', status: 'acknowledged' }
    ]
    lastRunAt.value = new Date().toISOString()
    // 自动选中最高危
    if (ruleDiagnoses.value.length) {
      const top = [...ruleDiagnoses.value].sort((a, b) => {
        const order = { critical: 0, high: 1, medium: 2, low: 3 }
        return (order[a.severity] ?? 4) - (order[b.severity] ?? 4)
      })[0]
      handleSelectDiagnosis(top)
    }
    return
  }

  try {
    const res = await getActiveAlerts({ limit: 20 })
    const items = res.data?.items ?? []
    // 将预警映射为规则诊断结果
    ruleDiagnoses.value = items.map((item, idx) => ({
      id: item.alert_id || `r${idx}`,
      rule_name: item.title || item.alert_type || '未知规则',
      service: item.affected_service || '全局',
      severity: item.severity || 'medium',
      hit_count: item.evidence_count ?? 1,
      time_window: item.created_at
        ? new Date(item.created_at).toLocaleString('zh-CN', { hour12: false })
        : '—',
      status: item.status || 'active'
    }))
    lastRunAt.value = new Date().toISOString()
  } catch {
    ruleDiagnoses.value = []
  }
}

// 选中单条规则诊断 → 运行分析获取详细结论
async function handleSelectDiagnosis(diagnosis) {
  if (!diagnosis) return
  selectedDiagnosis.value = diagnosis
  diagnosisResult.value = null
  nodeTrace.value = [{ node_name: 'fetch_context', status: 'running', duration_ms: 0 }]
  detailLoading.value = true
  detailError.value = ''

  // 演示模式：模拟详细诊断结果
  if (DIAGNOSIS_USE_MOCK || ANALYSIS_USE_MOCK) {
    const mockResult = {
      severity: diagnosis.severity === 'critical' ? 'critical' : diagnosis.severity === 'high' ? 'high' : 'medium',
      confidence: 0.78 + Math.random() * 0.15,
      anomaly_type: 'service_timeout',
      summary: `${diagnosis.rule_name}：${diagnosis.service} 在 ${diagnosis.time_window} 内累计触发 ${diagnosis.hit_count} 次异常，当前状态 ${diagnosis.status === 'active' ? '活跃' : diagnosis.status}`,
      root_cause: `${diagnosis.service} 后端服务响应超时，连接池资源耗尽导致请求堆积`,
      affected_services: [diagnosis.service],
      evidence_logs: [
        { timestamp: new Date(Date.now() - 300000).toISOString(), service_name: diagnosis.service, log_level: 'ERROR', message: `Connection timeout after 30000ms to ${diagnosis.service}` },
        { timestamp: new Date(Date.now() - 240000).toISOString(), service_name: diagnosis.service, log_level: 'WARN', message: 'Thread pool exhausted: 200/200 active threads' },
        { timestamp: new Date(Date.now() - 180000).toISOString(), service_name: 'gateway', log_level: 'WARN', message: `Upstream response latency > 5s for ${diagnosis.service}` }
      ],
      suggestions: [
        '检查后端服务连接池配置，增加最大连接数',
        '排查是否存在慢查询导致资源阻塞',
        '考虑临时扩容或启用熔断机制',
        '检查上游依赖服务健康状态'
      ]
    }

    setTimeout(() => {
      diagnosisResult.value = mockResult
      nodeTrace.value = [
        { node_name: 'fetch_context', status: 'success', duration_ms: 820 },
        { node_name: 'rule_diagnose', status: 'success', duration_ms: 340 },
        { node_name: 'assess_severity', status: 'success', duration_ms: 125 },
        { node_name: 'generate_event_report', status: 'success', duration_ms: 210 }
      ]
      detailLoading.value = false
    }, 1200)
    return
  }

  try {
    const payload = {
      service_name: diagnosis.service,
      keyword: diagnosis.rule_name,
      time_range_start: diagnosis.time_window || undefined,
      time_range_end: new Date().toISOString()
    }
    const [diagRes, traceRes] = await Promise.all([
      submitDiagnosis(payload),
      triggerAnalysisRun({ trigger_type: 'rule', trigger_event: { service_name: diagnosis.service, keyword: diagnosis.rule_name } }).catch(() => ({ data: { node_trace: [] } }))
    ])
    diagnosisResult.value = diagRes.data?.diagnosis ?? null
    nodeTrace.value = traceRes.data?.node_trace ?? []
  } catch (e) {
    detailError.value = e.error?.message || e.message || '诊断请求失败'
    nodeTrace.value = []
  } finally {
    detailLoading.value = false
  }
}

onMounted(() => {
  loadRuleSubgraph()
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

.diagnosis-page__grid {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr) 300px;
  gap: var(--spacing-md);
  align-items: start;
}

.diagnosis-page__main {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  min-width: 0;
}

.diagnosis-page__section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.diagnosis-page__status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  font-size: 13px;
  line-height: 1.5;
}

.diagnosis-page__status--loading {
  border: 1px solid var(--color-border);
  background: var(--color-info-bg);
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

@media (max-width: 1400px) {
  .diagnosis-page__grid {
    grid-template-columns: 320px minmax(0, 1fr) 260px;
  }
}

@media (max-width: 1200px) {
  .diagnosis-page__grid {
    grid-template-columns: 1fr;
  }

  .diagnosis-page__aside {
    order: -1;
  }

  .evidence-grid {
    grid-template-columns: 1fr;
  }
}
</style>
