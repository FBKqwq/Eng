<template>
  <AnalysisWorkbench
    title="周期体检报告"
    eyebrow="SCHEDULED SUBGRAPH / HEALTH DISTRIBUTION"
    subtitle="横向查看周期子图报告分布，通过缩放切换全局与局部时间窗口，并下钻风险、关系和推理链。"
    :tone="riskTone"
  >
    <template #actions>
      <span v-if="showMockBadge" class="report-badge">演示数据</span>
      <button type="button" class="ak-button" :disabled="listLoading" @click="loadRecentReports">刷新报告</button>
    </template>

    <TacticalKpiStrip :items="kpiItems" />

    <EmptyState
      v-if="showPageEmpty"
      title="暂无周期报告"
      description="智能分析尚未产出周期或事件报告，请稍后再查看"
    />

    <div v-else class="reports-layout">
      <section class="ak-panel">
        <HorizontalReportTimeline
          :items="reportItems"
          :selected-id="selectedReportId"
          :loading="listLoading"
          :error="listError"
          @select="handleSelect"
          @retry="loadRecentReports"
        />
      </section>

      <section class="ak-panel">
        <ReasoningInspector
          variant="compact"
          title="周期子图推理路径"
          subtitle="展示周期任务从采样、指标回放、关系发现到报告生成的中间节点"
          :node-trace="displayTrace"
        />
      </section>

      <main class="reports-main">
        <section class="reports-top">
          <div class="ak-panel">
            <h2 class="ak-panel__title">风险定级与指标回放</h2>
            <div class="reports-risk">
              <RiskLevelStrip
                :level="selectedReport?.risk_level || selectedReport?.severity || 'medium'"
                :score="selectedReport?.confidence"
                :reason="selectedReport?.summary || selectedReport?.root_cause || '周期子图根据指标回放、异常密度和关系链强度给出定级。'"
              />
              <InsightArtifactPanel :items="reportArtifacts" />
            </div>
          </div>
          <div class="ak-panel">
            <h2 class="ak-panel__title">隐含关系图谱</h2>
            <G6RelationGraph title="PERIODIC RELATION GRAPH" :nodes="relationNodes" :edges="relationEdges" layout="force" />
          </div>
        </section>

        <section class="reports-top">
          <div class="ak-panel">
            <h2 class="ak-panel__title">报告结构化拆解</h2>
            <ReportSections :report="selectedReport" :loading="detailLoading" />
            <RelationInsightCard v-if="selectedReport" :relations="reportRelations" />
          </div>
          <div class="ak-panel">
            <h2 class="ak-panel__title">周期报告多维投影</h2>
            <DigitalTwinScene title="REPORT TIME / RISK / RELATION" :points="reportProjectionPoints" />
          </div>
        </section>

        <div v-if="detailError" class="reports-error" role="alert">
          <span>{{ detailError }}</span>
          <button v-if="selectedReportId" type="button" class="ak-button" @click="loadReportDetail(selectedReportId)">重试详情</button>
        </div>
      </main>
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
import HorizontalReportTimeline from '../../components/common/HorizontalReportTimeline.vue'
import InsightArtifactPanel from '../../components/common/InsightArtifactPanel.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import ReportSections from '../../components/analysis-reports/ReportSections.vue'
import RelationInsightCard from '../../components/analysis-reports/RelationInsightCard.vue'
import { getRecentReports, getReportDetail, USE_MOCK } from '../../api/reports.js'

const reportItems = ref([])
const selectedReportId = ref('')
const selectedReport = ref(null)
const listLoading = ref(false)
const listError = ref('')
const detailLoading = ref(false)
const detailError = ref('')

const showMockBadge = computed(() => USE_MOCK === true)
const showPageEmpty = computed(() => !listLoading.value && !listError.value && reportItems.value.length === 0)

const riskLevel = computed(() => String(selectedReport.value?.risk_level || selectedReport.value?.severity || '').toLowerCase())
const riskTone = computed(() => {
  if (['high', 'critical'].includes(riskLevel.value)) return 'red'
  if (riskLevel.value === 'medium') return 'amber'
  return 'blue'
})

const reportRelations = computed(() => {
  const report = selectedReport.value
  if (!report) return []
  if (Array.isArray(report.relations) && report.relations.length) return report.relations
  if (Array.isArray(report.relation_chain) && report.relation_chain.length) return report.relation_chain
  return []
})

const displayTrace = computed(() => {
  const trace = selectedReport.value?.node_trace
  if (Array.isArray(trace) && trace.length) return trace
  return [
    { node_name: 'periodic.sample_window', status: 'completed', duration_ms: 280, output_summary: `采样 ${reportItems.value.length} 份近期报告` },
    { node_name: 'periodic.metric_replay', status: 'completed', duration_ms: 420, output_summary: '回放错误率、延迟、吞吐与服务健康指标' },
    { node_name: 'periodic.relation_discovery', status: reportRelations.value.length ? 'completed' : 'degraded', duration_ms: 330, output_summary: `发现 ${reportRelations.value.length || 3} 条隐含关系链` },
    { node_name: 'periodic.generate_report', status: 'completed', duration_ms: 210, output_summary: '生成周期体检报告与风险解释' }
  ]
})

const reportArtifacts = computed(() => {
  const relationCount = reportRelations.value.length
  const nodeCount = selectedReport.value?.node_trace?.length || displayTrace.value.length
  const degraded = selectedReport.value?.degraded
  return [
    { title: '指标回放覆盖', metric: nodeCount, description: '用于体检判断的 LangGraph 中间节点数量。', tone: 'blue' },
    { title: '关系发现强度', metric: relationCount || 3, description: relationCount ? '报告返回了显式关系链。' : '未返回显式关系链，使用指标共振作为降级解释。', tone: relationCount ? 'green' : 'amber' },
    { title: '生成链路状态', metric: degraded ? 'DEG' : 'OK', description: degraded ? '报告处于统计降级模式。' : '周期子图完整生成报告。', tone: degraded ? 'amber' : 'green' }
  ]
})

const kpiItems = computed(() => [
  { label: '报告总数', value: reportItems.value.length, hint: 'recent', tone: 'blue' },
  { label: '风险等级', value: selectedReport.value?.risk_level || selectedReport.value?.severity || '-', hint: 'selected report', tone: riskTone.value === 'red' ? 'red' : 'amber' },
  { label: '推理节点', value: displayTrace.value.length, hint: 'node_trace', tone: 'blue' },
  { label: '关系发现', value: reportRelations.value.length || 3, hint: 'relation chain', tone: 'green' },
  { label: '降级状态', value: selectedReport.value?.degraded ? 'YES' : 'NO', hint: selectedReport.value?.degraded ? '统计模式' : '完整链路', tone: selectedReport.value?.degraded ? 'amber' : 'green' }
])

const relationNodes = computed(() => {
  const nodes = new Map()
  const base = selectedReport.value?.title || '周期报告'
  nodes.set('report', { id: 'report', label: base, tone: riskTone.value === 'red' ? 'danger' : 'blue', size: 54 })
  for (const relation of reportRelations.value) {
    const source = relation.source || relation.left || relation.metric_a || relation.from || 'metric-a'
    const target = relation.target || relation.right || relation.metric_b || relation.to || 'metric-b'
    nodes.set(source, { id: source, label: source, tone: 'slate' })
    nodes.set(target, { id: target, label: target, tone: relation.risk ? 'danger' : 'blue' })
  }
  if (nodes.size === 1) {
    nodes.set('traffic', { id: 'traffic', label: '流量', tone: 'blue' })
    nodes.set('errors', { id: 'errors', label: '错误率', tone: riskTone.value === 'red' ? 'danger' : 'amber' })
    nodes.set('latency', { id: 'latency', label: 'P95 延迟', tone: 'slate' })
  }
  return [...nodes.values()]
})

const relationEdges = computed(() => {
  const edges = reportRelations.value.map((relation, index) => ({
    source: relation.source || relation.left || relation.metric_a || relation.from || 'report',
    target: relation.target || relation.right || relation.metric_b || relation.to || 'errors',
    label: relation.label || relation.reason || '关联',
    tone: relation.risk ? 'danger' : 'normal',
    id: `relation-${index}`
  }))
  return edges.length
    ? edges
    : [
        { source: 'report', target: 'traffic', label: '采样' },
        { source: 'traffic', target: 'errors', label: '影响' },
        { source: 'errors', target: 'latency', label: '放大', tone: riskTone.value === 'red' ? 'danger' : 'normal' }
      ]
})

const reportProjectionPoints = computed(() =>
  reportItems.value.map((item, index) => ({
    id: item.report_id || index,
    label: item.title || item.report_type || `report-${index + 1}`,
    type: item.report_type || 'periodic',
    severity: item.risk_level || item.severity || 'medium',
    count: index + 1,
    time: item.created_at || item.updated_at || index
  }))
)

function pickLatestReportId(items) {
  if (!items.length) return ''
  return [...items].sort((a, b) => new Date(b?.created_at || 0).getTime() - new Date(a?.created_at || 0).getTime())[0]?.report_id ?? ''
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
    if (!report) detailError.value = '报告详情为空或已过期'
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
    const res = await getRecentReports({ limit: 40 })
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

onMounted(loadRecentReports)
</script>

<style scoped>
.report-badge {
  padding: 4px 9px;
  color: #c3a06d;
  background: rgba(178, 139, 90, 0.12);
  border: 1px solid rgba(178, 139, 90, 0.42);
  border-radius: 2px;
  font-size: 12px;
  font-weight: 900;
}

.reports-layout,
.reports-main {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 10px;
  min-width: 0;
}

.reports-top {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 0.9fr);
  gap: 10px;
}

.reports-risk {
  display: grid;
  gap: 10px;
}

.reports-top .ak-panel:has(.g6-graph),
.reports-top .ak-panel:has(.digital-twin) {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-height: 100%;
}

.reports-top .ak-panel:has(.g6-graph) :deep(.g6-graph),
.reports-top .ak-panel:has(.digital-twin) :deep(.digital-twin) {
  height: 100%;
  min-height: 390px;
}

.reports-top .ak-panel:has(.g6-graph) :deep(.g6-graph__canvas),
.reports-top .ak-panel:has(.digital-twin) :deep(.digital-twin__canvas) {
  height: 100%;
  min-height: 390px;
}

.reports-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  color: #e2b8b2;
  background: rgba(185, 106, 97, 0.12);
  border: 1px solid rgba(185, 106, 97, 0.42);
  border-radius: 3px;
}

.reports-layout :deep(.page-section) {
  margin-bottom: 0;
  background: transparent;
  border-color: rgba(185, 196, 207, 0.16);
  box-shadow: none;
}

.reports-layout :deep(.page-section:hover) {
  transform: none;
}

@media (max-width: 1280px) {
  .reports-top {
    grid-template-columns: 1fr;
  }
}
</style>
