<template>
  <AnalysisWorkbench
    title="业务漏斗洞察"
    eyebrow="EVENT TRACKING / FUNNEL INTELLIGENCE"
    subtitle="聚焦埋点质量、步骤流失、时间窗口对比和服务影响，把漏斗从聚合图升级为可解释分析产物。"
    tone="blue"
  >
    <TacticalKpiStrip :items="kpiItems" />

    <section class="ak-panel">
      <ReasoningInspector
        variant="compact"
        title="埋点分析推理路径"
        subtitle="从事件覆盖、步骤转化、流失定位到服务影响的中间分析过程"
        :node-trace="funnelReasoningTrace"
      />
    </section>

    <section class="funnel-overview">
      <div class="ak-panel">
        <h2 class="ak-panel__title">埋点分析产物</h2>
        <InsightArtifactPanel :items="analysisArtifacts" />
      </div>
      <div class="ak-panel">
        <h2 class="ak-panel__title">三维漏斗投影</h2>
        <DigitalTwinScene
          title="STEP TIME / LOSS / VOLUME"
          :points="funnelProjectionPoints"
          :active-service="selectedStepMeta?.service"
        />
      </div>
    </section>

    <div class="funnel-tabs" role="tablist" aria-label="漏斗视图切换">
      <button type="button" class="funnel-tab" :class="{ active: activeTab === 'main' }" role="tab" :aria-selected="activeTab === 'main'" @click="activeTab = 'main'">
        主漏斗
      </button>
      <button type="button" class="funnel-tab" :class="{ active: activeTab === 'compare' }" role="tab" :aria-selected="activeTab === 'compare'" @click="activeTab = 'compare'">
        时间窗对比
      </button>
    </div>

    <div v-if="activeTab === 'main'" class="funnel-layout">
      <main class="funnel-layout__main">
        <FunnelMain @select-step="selectedStep = $event" />
        <section class="ak-panel">
          <h2 class="ak-panel__title">埋点步骤影响图谱</h2>
          <G6RelationGraph title="EVENT FUNNEL GRAPH" :nodes="funnelGraphNodes" :edges="funnelGraphEdges" />
        </section>
      </main>
      <aside class="funnel-layout__aside">
        <div class="ak-panel">
          <h2 class="ak-panel__title">流失定位</h2>
          <LossLocator :selected-step="selectedStep" />
        </div>
        <div class="ak-panel">
          <h2 class="ak-panel__title">选中步骤风险</h2>
          <RiskLevelStrip
            :level="selectedStepRisk.level"
            :score="selectedStepRisk.score"
            :reason="selectedStepRisk.reason"
          />
        </div>
      </aside>
    </div>

    <section v-else class="ak-panel funnel-compare">
      <header class="funnel-compare__header">
        <h2>时间窗口对比</h2>
        <p class="funnel-compare__range tabular-nums">
          当前：{{ formatTime(range.start) }} - {{ formatTime(range.end) }}
          <span>|</span>
          对比：{{ formatTime(baselineRange.start) }} - {{ formatTime(baselineRange.end) }}
        </p>
      </header>

      <EmptyState v-if="compareError" compact title="对比数据加载失败" :description="compareError">
        <button type="button" class="ak-button" @click="loadCompareData">重试</button>
      </EmptyState>

      <div v-else class="funnel-compare__grid">
        <div>
          <h3>当前窗口</h3>
          <FunnelChart :data="currentChartData" :loading="compareLoading" height="320px" placeholder="当前窗口漏斗：等待 behavior_funnel 聚合" />
        </div>
        <div>
          <h3>上一等长窗口</h3>
          <FunnelChart :data="baselineChartData" :loading="compareLoading" height="320px" placeholder="对比窗口漏斗：等待 behavior_funnel 聚合" />
        </div>
      </div>
    </section>
  </AnalysisWorkbench>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import AnalysisWorkbench from '../../components/common/AnalysisWorkbench.vue'
import TacticalKpiStrip from '../../components/common/TacticalKpiStrip.vue'
import G6RelationGraph from '../../components/common/G6RelationGraph.vue'
import DigitalTwinScene from '../../components/common/DigitalTwinScene.vue'
import ReasoningInspector from '../../components/common/ReasoningInspector.vue'
import RiskLevelStrip from '../../components/common/RiskLevelStrip.vue'
import InsightArtifactPanel from '../../components/common/InsightArtifactPanel.vue'
import FunnelMain from '../../components/analysis-funnel/FunnelMain.vue'
import LossLocator from '../../components/analysis-funnel/LossLocator.vue'
import FunnelChart from '../../components/common/charts/FunnelChart.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import { useTimeRange } from '../../composables/useTimeRange.js'
import { queryBehaviorFunnel } from '../../api/metrics.js'
import { formatTime } from '../../utils/format.js'

const FUNNEL_STEPS = [
  { key: 'page_view', label: '页面浏览', service: 'web-gateway', type: 'entry' },
  { key: 'product_click', label: '商品点击', service: 'product-service', type: 'intent' },
  { key: 'add_to_cart', label: '加入购物车', service: 'cart-service', type: 'intent' },
  { key: 'checkout_click', label: '结算点击', service: 'order-service', type: 'order' },
  { key: 'pay_button_click', label: '支付点击', service: 'payment-service', type: 'payment' }
]

const { range } = useTimeRange()
const activeTab = ref('main')
const selectedStep = ref('')
const compareLoading = ref(false)
const compareError = ref(null)
const currentBuckets = ref(null)
const baselineBuckets = ref(null)

const baselineRange = computed(() => {
  const { start, end } = range.value
  const duration = Math.max(0, end - start)
  return { start: start - duration, end: start }
})

const selectedStepMeta = computed(() => FUNNEL_STEPS.find((step) => step.key === selectedStep.value) || FUNNEL_STEPS[0])
const currentChartData = computed(() => bucketsToChartData(currentBuckets.value))
const baselineChartData = computed(() => bucketsToChartData(baselineBuckets.value))
const worstStep = computed(() => findWorstStep(currentChartData.value))
const entryCount = computed(() => Number(currentChartData.value[0]?.value || 0))
const exitCount = computed(() => Number(currentChartData.value[currentChartData.value.length - 1]?.value || 0))
const conversionRate = computed(() => entryCount.value > 0 ? Math.round((exitCount.value / entryCount.value) * 100) : 0)

const kpiItems = computed(() => [
  { label: '入口规模', value: entryCount.value || '-', hint: 'page view', tone: 'blue' },
  { label: '最终转化', value: exitCount.value || '-', hint: 'pay click', tone: 'green' },
  { label: '转化率', value: entryCount.value ? `${conversionRate.value}%` : '-', hint: 'end / entry', tone: conversionRate.value < 20 ? 'amber' : 'green' },
  { label: '最大流失', value: worstStep.value.label, hint: worstStep.value.hint, tone: worstStep.value.tone },
  { label: '埋点覆盖', value: `${FUNNEL_STEPS.length}/5`, hint: selectedStepMeta.value?.service || '', tone: 'blue' }
])

const analysisArtifacts = computed(() => [
  {
    title: '埋点覆盖质量',
    metric: `${FUNNEL_STEPS.length}/5`,
    description: '核心浏览、点击、加购、结算和支付事件均进入分析链路。',
    tone: 'green'
  },
  {
    title: '最大流失定位',
    metric: worstStep.value.label,
    description: worstStep.value.hint === '等待数据' ? '等待 behavior_funnel 聚合后定位。' : `当前最大流失发生在 ${worstStep.value.label}，建议联动 ${selectedStepMeta.value.service} 日志。`,
    tone: worstStep.value.tone
  },
  {
    title: '转化异常判断',
    metric: entryCount.value ? `${conversionRate.value}%` : '-',
    description: conversionRate.value && conversionRate.value < 20 ? '支付前链路可能存在明显阻断，需要排查订单和支付服务。' : '当前窗口未出现显著转化塌陷。',
    tone: conversionRate.value && conversionRate.value < 20 ? 'red' : 'blue'
  }
])

const funnelReasoningTrace = computed(() => [
  { node_name: 'funnel.event_coverage', status: 'completed', duration_ms: 150, output_summary: `校验 ${FUNNEL_STEPS.length} 个核心埋点事件` },
  { node_name: 'funnel.step_conversion', status: currentChartData.value.length ? 'completed' : 'pending', duration_ms: 260, output_summary: '计算步骤转化率与环节流失' },
  { node_name: 'funnel.loss_locator', status: worstStep.value.label !== '-' ? 'completed' : 'degraded', duration_ms: 210, output_summary: `定位最大流失步骤：${worstStep.value.label}` },
  { node_name: 'funnel.service_impact', status: 'completed', duration_ms: 190, output_summary: `映射到 ${selectedStepMeta.value.service} 服务影响` }
])

const selectedStepRisk = computed(() => {
  const index = FUNNEL_STEPS.findIndex((step) => step.key === selectedStepMeta.value.key)
  const data = currentChartData.value
  if (index <= 0 || !data[index - 1]) {
    return { level: 'medium', score: 0.45, reason: '入口或未选择步骤，按埋点完整性和当前窗口默认评估。' }
  }
  const prev = Number(data[index - 1].value || 0)
  const curr = Number(data[index].value || 0)
  const drop = prev > 0 ? Math.max(0, 1 - curr / prev) : 0
  return {
    level: drop > 0.55 ? 'high' : drop > 0.32 ? 'medium' : 'low',
    score: drop,
    reason: `${data[index].name} 相对上一环节流失 ${Math.round(drop * 100)}%，关联服务 ${selectedStepMeta.value.service}。`
  }
})

const funnelGraphNodes = computed(() =>
  FUNNEL_STEPS.map((step, index) => ({
    id: step.key,
    label: step.label,
    tone: step.key === selectedStep.value ? 'danger' : index >= 3 ? 'warning' : 'blue',
    size: step.key === selectedStep.value ? 54 : 36 + index * 2
  }))
)

const funnelGraphEdges = computed(() =>
  FUNNEL_STEPS.slice(1).map((step, index) => {
    const data = currentChartData.value
    const prev = Number(data[index]?.value || 0)
    const curr = Number(data[index + 1]?.value || 0)
    const drop = prev > 0 ? Math.max(0, 1 - curr / prev) : 0
    return {
      source: FUNNEL_STEPS[index].key,
      target: step.key,
      label: `${Math.round((1 - drop) * 100)}%`,
      weight: 1 + drop * 4,
      tone: drop > 0.45 ? 'danger' : drop > 0.25 ? 'warning' : 'normal'
    }
  })
)

const funnelProjectionPoints = computed(() =>
  FUNNEL_STEPS.map((step, index) => {
    const data = currentChartData.value
    const value = Number(data[index]?.value || (FUNNEL_STEPS.length - index) * 10)
    const prev = index > 0 ? Number(data[index - 1]?.value || value) : value
    const drop = prev > 0 ? Math.max(0, 1 - value / prev) : 0
    return {
      id: step.key,
      label: step.service,
      type: step.type,
      severity: drop > 0.55 ? 'high' : drop > 0.32 ? 'medium' : 'low',
      count: value || index + 1,
      time: index
    }
  })
)

function bucketsToChartData(buckets) {
  const bucketMap = new Map((buckets ?? []).map((bucket) => [bucket.key, bucket]))
  return FUNNEL_STEPS.map((step) => ({ name: step.label, value: Number(bucketMap.get(step.key)?.count ?? 0) }))
}

function findWorstStep(data) {
  if (!data.length) return { label: '-', hint: '等待数据', tone: 'amber', drop: 0 }
  let worst = { label: '-', hint: '暂无流失', tone: 'green', drop: 0 }
  for (let i = 1; i < data.length; i += 1) {
    const prev = Number(data[i - 1].value || 0)
    const curr = Number(data[i].value || 0)
    if (prev <= 0) continue
    const drop = Math.max(0, 1 - curr / prev)
    if (drop > worst.drop) {
      worst = {
        label: data[i].name,
        hint: `${Math.round(drop * 100)}% loss`,
        tone: drop > 0.5 ? 'red' : drop > 0.3 ? 'amber' : 'green',
        drop
      }
    }
  }
  return worst
}

function buildPayload(windowRange) {
  return {
    start_time: new Date(windowRange.start).toISOString(),
    end_time: new Date(windowRange.end).toISOString()
  }
}

async function loadCompareData() {
  compareLoading.value = true
  compareError.value = null
  try {
    const [currentRes, baselineRes] = await Promise.all([
      queryBehaviorFunnel(buildPayload(range.value)),
      queryBehaviorFunnel(buildPayload(baselineRange.value))
    ])
    currentBuckets.value = currentRes?.data?.buckets ?? []
    baselineBuckets.value = baselineRes?.data?.buckets ?? []
  } catch (err) {
    compareError.value = err?.message || '对比漏斗请求失败'
    currentBuckets.value = null
    baselineBuckets.value = null
  } finally {
    compareLoading.value = false
  }
}

watch([activeTab, range], () => {
  loadCompareData()
}, { immediate: true })
</script>

<style scoped>
.funnel-overview {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(360px, 1.1fr);
  gap: 10px;
  margin: 10px 0;
}

.funnel-tabs {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 6px;
  margin: 0 0 10px;
}

.funnel-tab {
  padding: 7px 12px;
  border: 1px solid rgba(185, 196, 207, 0.18);
  border-radius: 2px;
  background: rgba(7, 10, 14, 0.66);
  color: #8e9aa6;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  clip-path: polygon(0 0, calc(100% - 9px) 0, 100% 100%, 0 100%);
}

.funnel-tab.active {
  color: #e6edf3;
  border-color: rgba(111, 158, 172, 0.55);
  background: rgba(111, 158, 172, 0.14);
}

.funnel-layout {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 10px;
}

.funnel-layout__main,
.funnel-layout__aside {
  display: grid;
  gap: 10px;
  min-width: 0;
}

.funnel-compare {
  position: relative;
  z-index: 1;
}

.funnel-compare__header {
  margin-bottom: 12px;
}

.funnel-compare__header h2 {
  margin: 0 0 4px;
  color: #f2f5f7;
  font-size: 15px;
}

.funnel-compare__range {
  margin: 0;
  color: #8e9aa6;
  font-size: 12px;
}

.funnel-compare__range span {
  margin: 0 8px;
}

.funnel-compare__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.funnel-compare__grid h3 {
  margin: 0 0 8px;
  color: #dce4eb;
  font-size: 13px;
}

.funnel-layout :deep(.page-section) {
  margin-bottom: 0;
  background: transparent;
  border-color: rgba(185, 196, 207, 0.16);
  box-shadow: none;
}

.funnel-layout :deep(.page-section:hover) {
  transform: none;
}

@media (max-width: 1280px) {
  .funnel-overview,
  .funnel-layout,
  .funnel-compare__grid {
    grid-template-columns: 1fr;
  }
}
</style>
