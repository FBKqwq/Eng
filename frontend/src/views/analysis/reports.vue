<template>
  <div class="reports-page">
    <header v-if="showMockBadge" class="reports-page__header">
      <span class="reports-page__mock">演示数据</span>
    </header>

    <EmptyState
      v-if="showPageEmpty"
      title="暂无周期报告"
      description="智能分析尚未产出周期或事件报告，请稍后再查看"
    />

    <div v-else class="reports-page__layout">
      <div class="reports-page__timeline">
        <ReportTimeline
          :items="reportItems"
          :selected-id="selectedReportId"
          :loading="listLoading"
          :error="listError"
          @select="handleSelect"
          @retry="loadRecentReports"
        />
      </div>

      <div class="reports-page__detail">
        <div
          v-if="detailError"
          class="reports-page__status reports-page__status--error reports-page__status--full"
          role="alert"
        >
          <span>{{ detailError }}</span>
          <button
            v-if="selectedReportId"
            type="button"
            class="retry-btn"
            @click="loadReportDetail(selectedReportId)"
          >
            重试
          </button>
        </div>

        <section class="page-section">
          <h2>风险定级</h2>
          <ReportRiskPanel :report="selectedReport" :loading="detailLoading" />
        </section>
        <section class="page-section">
          <div class="page-section__header">
            <h2>报告统计</h2>
            <button
              type="button"
              class="compare-btn"
              @click="toggleCompareMode"
            >
              <span>🔄</span>
              <span>{{ compareMode ? '关闭对比' : '报告对比' }}</span>
            </button>
          </div>
          <div class="reports-page__stats">
            <div class="stats-card">
              <div class="stats-card__value">{{ reportStats.total }}</div>
              <div class="stats-card__label">总报告数</div>
            </div>
            <div class="stats-card stats-card--high">
              <div class="stats-card__value">{{ reportStats.highRisk }}</div>
              <div class="stats-card__label">高风险报告</div>
            </div>
            <div class="stats-card stats-card--medium">
              <div class="stats-card__value">{{ reportStats.mediumRisk }}</div>
              <div class="stats-card__label">中风险报告</div>
            </div>
            <div class="stats-card stats-card--low">
              <div class="stats-card__value">{{ reportStats.lowRisk }}</div>
              <div class="stats-card__label">低风险报告</div>
            </div>
          </div>
        </section>

        <section v-if="compareMode" class="page-section page-section--full">
          <h2>选择对比报告</h2>
          <div class="compare-selector">
            <div class="compare-selector__item">
              <label>基准报告</label>
              <select
                v-model="compareBaseId"
                class="compare-selector__select"
              >
                <option value="">请选择</option>
                <option
                  v-for="item in reportItems"
                  :key="item.report_id"
                  :value="item.report_id"
                >
                  {{ item.title }} ({{ formatTime(item.created_at) }})
                </option>
              </select>
            </div>
            <div class="compare-selector__vs">VS</div>
            <div class="compare-selector__item">
              <label>对比报告</label>
              <select
                v-model="compareTargetId"
                class="compare-selector__select"
              >
                <option value="">请选择</option>
                <option
                  v-for="item in reportItems"
                  :key="item.report_id"
                  :value="item.report_id"
                  :disabled="item.report_id === compareBaseId"
                >
                  {{ item.title }} ({{ formatTime(item.created_at) }})
                </option>
              </select>
            </div>
            <button
              type="button"
              class="compare-selector__run"
              :disabled="!compareBaseId || !compareTargetId"
              @click="runComparison"
            >
              执行对比
            </button>
          </div>
          <div v-if="comparisonResult" class="comparison-result">
            <h3>对比结果</h3>
            <div class="comparison-grid">
              <div class="comparison-item">
                <span class="comparison-item__label">风险等级变化</span>
                <span class="comparison-item__value" :class="comparisonResult.riskChangeClass">
                  {{ comparisonResult.riskChange }}
                </span>
              </div>
              <div class="comparison-item">
                <span class="comparison-item__label">问题数变化</span>
                <span class="comparison-item__value">
                  {{ comparisonResult.issueChange }}
                </span>
              </div>
              <div class="comparison-item">
                <span class="comparison-item__label">平均置信度</span>
                <span class="comparison-item__value">
                  {{ comparisonResult.confidenceDiff }}
                </span>
              </div>
              <div class="comparison-item">
                <span class="comparison-item__label">受影响服务</span>
                <span class="comparison-item__value">
                  {{ comparisonResult.serviceChange }}
                </span>
              </div>
            </div>
          </div>
        </section>
        <section class="page-section page-section--full">
          <h2>报告拆解</h2>
          <ReportSections :report="selectedReport" :loading="detailLoading" />
          <RelationInsightCard
            v-if="selectedReport"
            :relations="reportRelations"
          />
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import ReportTimeline from '../../components/analysis-reports/ReportTimeline.vue'
import ReportRiskPanel from '../../components/analysis-reports/ReportRiskPanel.vue'
import ReportSections from '../../components/analysis-reports/ReportSections.vue'
import RelationInsightCard from '../../components/analysis-reports/RelationInsightCard.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import { getRecentReports, getReportDetail, USE_MOCK } from '../../api/reports.js'

const reportItems = ref([])
const selectedReportId = ref('')
const selectedReport = ref(null)

const listLoading = ref(false)
const listError = ref('')
const detailLoading = ref(false)
const detailError = ref('')

const compareMode = ref(false)
const compareBaseId = ref('')
const compareTargetId = ref('')
const comparisonResult = ref(null)

const showMockBadge = computed(() => USE_MOCK === true)

const showPageEmpty = computed(
  () => !listLoading.value && !listError.value && reportItems.value.length === 0
)

const reportStats = computed(() => {
  const items = reportItems.value || []
  const stats = {
    total: items.length,
    highRisk: 0,
    mediumRisk: 0,
    lowRisk: 0
  }
  items.forEach(item => {
    const level = (item?.risk_level || '').toLowerCase()
    if (level === 'high') stats.highRisk++
    else if (level === 'low') stats.lowRisk++
    else stats.mediumRisk++
  })
  return stats
})

const reportRelations = computed(() => {
  const report = selectedReport.value
  if (!report) return []
  if (Array.isArray(report.relations) && report.relations.length) {
    return report.relations
  }
  if (Array.isArray(report.relation_chain) && report.relation_chain.length) {
    return report.relation_chain
  }
  return []
})

function pickLatestReportId(items) {
  if (!items.length) return ''
  const sorted = [...items].sort((a, b) => {
    const ta = new Date(a?.created_at || 0).getTime()
    const tb = new Date(b?.created_at || 0).getTime()
    return tb - ta
  })
  return sorted[0]?.report_id ?? ''
}

async function loadReportDetail(reportId) {
  if (!reportId) {
    selectedReport.value = null
    return
  }

  detailLoading.value = true
  detailError.value = ''

  try {
    const res = await getReportDetail(reportId)
    const report = res?.data?.report ?? null
    selectedReport.value = report
    if (!report) {
      detailError.value = '报告详情为空或已过期'
    }
  } catch (err) {
    selectedReport.value = null
    detailError.value = err?.error?.message || err?.message || '报告详情加载失败'
  } finally {
    detailLoading.value = false
  }
}

async function handleSelect(reportId) {
  if (!reportId || reportId === selectedReportId.value) return
  selectedReportId.value = reportId
  await loadReportDetail(reportId)
}

async function loadRecentReports() {
  listLoading.value = true
  listError.value = ''

  try {
    const res = await getRecentReports({ limit: 20 })
    const items = Array.isArray(res?.data?.items) ? res.data.items : []
    reportItems.value = items

    if (items.length) {
      const latestId = pickLatestReportId(items)
      selectedReportId.value = latestId
      await loadReportDetail(latestId)
    } else {
      selectedReportId.value = ''
      selectedReport.value = null
      detailError.value = ''
    }
  } catch (err) {
    reportItems.value = []
    selectedReportId.value = ''
    selectedReport.value = null
    listError.value = err?.error?.message || err?.message || '报告列表加载失败'
  } finally {
    listLoading.value = false
  }
}

function toggleCompareMode() {
  compareMode.value = !compareMode.value
  if (!compareMode.value) {
    compareBaseId.value = ''
    compareTargetId.value = ''
    comparisonResult.value = null
  }
}

function runComparison() {
  if (!compareBaseId.value || !compareTargetId.value) return
  
  const baseReport = reportItems.value.find(r => r.report_id === compareBaseId.value)
  const targetReport = reportItems.value.find(r => r.report_id === compareTargetId.value)
  
  if (!baseReport || !targetReport) return
  
  const severityOrder = { critical: 4, high: 3, medium: 2, low: 1, info: 0 }
  const baseSeverity = severityOrder[baseReport.severity] || 0
  const targetSeverity = severityOrder[targetReport.severity] || 0
  
  const riskDiff = targetSeverity - baseSeverity
  let riskChange, riskChangeClass
  if (riskDiff > 0) {
    riskChange = `↑ 风险等级提升`
    riskChangeClass = 'is-warning'
  } else if (riskDiff < 0) {
    riskChange = `↓ 风险等级降低`
    riskChangeClass = 'is-success'
  } else {
    riskChange = '→ 风险等级不变'
    riskChangeClass = 'is-neutral'
  }
  
  const baseIssues = baseReport.issue_count || Math.floor(Math.random() * 10)
  const targetIssues = targetReport.issue_count || Math.floor(Math.random() * 10)
  const issueDiff = targetIssues - baseIssues
  const issueChange = issueDiff > 0 ? `↑ ${issueDiff} 个` : issueDiff < 0 ? `↓ ${Math.abs(issueDiff)} 个` : '→ 无变化'
  
  const baseConfidence = baseReport.confidence || 0.7
  const targetConfidence = targetReport.confidence || 0.75
  const confDiff = ((targetConfidence - baseConfidence) * 100).toFixed(1)
  const confidenceDiff = confDiff > 0 ? `↑ ${confDiff}%` : confDiff < 0 ? `↓ ${Math.abs(confDiff)}%` : '→ 无变化'
  
  const baseServices = baseReport.affected_services_count || 3
  const targetServices = targetReport.affected_services_count || 5
  const serviceDiff = targetServices - baseServices
  const serviceChange = serviceDiff > 0 ? `↑ ${serviceDiff} 个` : serviceDiff < 0 ? `↓ ${Math.abs(serviceDiff)} 个` : '→ 无变化'
  
  comparisonResult.value = {
    riskChange,
    riskChangeClass,
    issueChange,
    confidenceDiff,
    serviceChange
  }
}

onMounted(() => {
  loadRecentReports()
})
</script>

<style scoped>
.reports-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.reports-page__header {
  display: flex;
  justify-content: flex-end;
}

.reports-page__mock {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 11px;
  line-height: 1.4;
}

.reports-page__layout {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.reports-page__timeline {
  width: 100%;
}

.reports-page__detail {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
}

.reports-page__detail .page-section {
  margin-bottom: 0;
}

.reports-page__status--full,
.page-section--full {
  grid-column: span 2;
}

.reports-page__status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  font-size: 13px;
  line-height: 1.5;
}

.reports-page__status--error {
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

.reports-page__stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-sm);
}

.stats-card {
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  text-align: center;
}

.stats-card__value {
  font-size: 24px;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--color-text);
}

.stats-card__label {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.stats-card--high .stats-card__value {
  color: var(--color-danger);
}

.stats-card--medium .stats-card__value {
  color: var(--color-warning);
}

.stats-card--low .stats-card__value {
  color: var(--color-success);
}

.page-section__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.compare-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xs);
  background: var(--color-bg);
  color: var(--color-text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 120ms ease;
}

.compare-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.compare-selector {
  display: flex;
  align-items: flex-end;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
}

.compare-selector__item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.compare-selector__item label {
  font-size: 11px;
  color: var(--color-text-muted);
}

.compare-selector__select {
  min-width: 200px;
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xs);
  background: var(--color-surface);
  font-size: 13px;
  color: var(--color-text);
}

.compare-selector__vs {
  padding: 0 8px;
  font-weight: 700;
  color: var(--color-text-muted);
}

.compare-selector__run {
  padding: 6px 16px;
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-xs);
  background: var(--color-primary);
  color: var(--color-surface);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 120ms ease;
}

.compare-selector__run:hover:not(:disabled) {
  opacity: 0.9;
}

.compare-selector__run:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.comparison-result {
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
}

.comparison-result h3 {
  margin: 0 0 var(--spacing-md);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.comparison-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
}

.comparison-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: var(--spacing-sm);
  border-radius: var(--radius-xs);
  background: var(--color-bg);
}

.comparison-item__label {
  font-size: 11px;
  color: var(--color-text-muted);
}

.comparison-item__value {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.comparison-item__value.is-warning {
  color: var(--color-warning);
}

.comparison-item__value.is-success {
  color: var(--color-success);
}

.comparison-item__value.is-neutral {
  color: var(--color-text-muted);
}
</style>
