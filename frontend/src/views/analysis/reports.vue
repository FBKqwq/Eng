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

    <div v-else class="reports-page__grid page-grid page-grid-2">
      <ReportTimeline
        :items="reportItems"
        :selected-id="selectedReportId"
        :loading="listLoading"
        :error="listError"
        @select="handleSelect"
        @retry="loadRecentReports"
      />

      <div class="reports-page__detail">
        <div
          v-if="detailError"
          class="reports-page__status reports-page__status--error"
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

const showMockBadge = computed(() => USE_MOCK === true)

const showPageEmpty = computed(
  () => !listLoading.value && !listError.value && reportItems.value.length === 0
)

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

.reports-page__detail {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  min-width: 0;
}

.reports-page__detail .page-section {
  margin-bottom: 0;
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
</style>
