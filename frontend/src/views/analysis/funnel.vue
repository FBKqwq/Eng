<template>
  <div class="funnel-page">
    <div v-if="compareTabReady" class="funnel-tabs" role="tablist" aria-label="漏斗视图切换">
      <button
        type="button"
        class="funnel-tab"
        :class="{ active: activeTab === 'main' }"
        role="tab"
        :aria-selected="activeTab === 'main'"
        @click="activeTab = 'main'"
      >
        主漏斗
      </button>
      <button
        type="button"
        class="funnel-tab"
        :class="{ active: activeTab === 'compare' }"
        role="tab"
        :aria-selected="activeTab === 'compare'"
        @click="activeTab = 'compare'"
      >
        时段对比
      </button>
    </div>

    <template v-if="activeTab === 'main' || !compareTabReady">
      <!-- 三维漏斗 + 分析洞察 -->
      <div class="funnel-page__layout">
        <!-- 三维漏斗可视化（左侧） -->
        <section class="page-section funnel-page__chart">
          <header class="funnel-chart-header">
            <h2>转化漏斗</h2>
            <span v-if="isMock" class="mock-badge">演示数据</span>
          </header>
          <Funnel3DSurface
            :data="funnelLayers"
            :loading="loading"
            height="300px"
          />
          <FunnelChart
            :data="funnelLayers"
            :loading="loading"
            height="0px"
            placeholder=""
            style="display:none"
          />
        </section>

        <!-- 分析洞察（右侧） -->
        <section class="page-section funnel-page__analysis">
          <FunnelAnalysisPanel
            :funnel-data="data"
            :loading="loading"
          />
        </section>
      </div>

      <!-- 步骤详情列表 -->
      <FunnelMain @select-step="selectedStep = $event" />
      <LossLocator :selected-step="selectedStep" />
    </template>

    <section v-else class="page-section funnel-compare">
      <header class="funnel-compare__header">
        <h2>时段对比</h2>
        <p class="funnel-compare__range tabular-nums">
          当前：{{ formatTime(range.start) }} — {{ formatTime(range.end) }}
          <span class="funnel-compare__sep">|</span>
          对比：{{ formatTime(baselineRange.start) }} — {{ formatTime(baselineRange.end) }}
        </p>
      </header>

      <EmptyState
        v-if="compareError"
        compact
        title="对比数据加载失败"
        :description="compareError"
      >
        <button type="button" class="funnel-compare__retry" @click="loadCompareData">重试</button>
      </EmptyState>

      <div v-else class="funnel-compare__grid">
        <div class="funnel-compare__panel">
          <h3>当前时段</h3>
          <FunnelChart
            :data="currentChartData"
            :loading="compareLoading"
            height="300px"
            placeholder="等待对比数据"
          />
        </div>
        <div class="funnel-compare__panel">
          <h3>对比时段（上一等长窗口）</h3>
          <FunnelChart
            :data="baselineChartData"
            :loading="compareLoading"
            height="300px"
            placeholder="等待对比数据"
          />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useTimeRange } from '../../composables/useTimeRange.js'
import { useMetrics } from '../../composables/useMetrics.js'
import { queryBehaviorFunnel } from '../../api/metrics.js'
import FunnelMain from '../../components/analysis-funnel/FunnelMain.vue'
import LossLocator from '../../components/analysis-funnel/LossLocator.vue'
import FunnelChart from '../../components/common/charts/FunnelChart.vue'
import Funnel3DSurface from '../../components/common/charts/Funnel3DSurface.vue'
import FunnelAnalysisPanel from '../../components/analysis-funnel/FunnelAnalysisPanel.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import { formatTime } from '../../utils/format.js'

const COMPARE_TAB_READY = false

const FUNNEL_STEPS = [
  { key: 'page_view', label: '页面浏览' },
  { key: 'product_click', label: '商品点击' },
  { key: 'add_to_cart', label: '加入购物车' },
  { key: 'checkout_click', label: '结算点击' },
  { key: 'pay_button_click', label: '支付点击' }
]

const DROPOUT_WARNING = 0.35
const DROPOUT_DANGER = 0.55

const { range } = useTimeRange()

const compareTabReady = COMPARE_TAB_READY
const activeTab = ref('main')
const selectedStep = ref('')

const { data, loading, isMock } = useMetrics({ template: 'behavior_funnel' })

const compareLoading = ref(false)
const compareError = ref(null)
const currentBuckets = ref(null)
const baselineBuckets = ref(null)

const baselineRange = computed(() => {
  const { start, end } = range.value
  const duration = Math.max(0, end - start)
  return { start: start - duration, end: start }
})

const funnelLayers = computed(() => {
  const buckets = new Map((data.value?.buckets ?? []).map((b) => [b.key, b]))
  return FUNNEL_STEPS.map((step, index) => {
    const bucket = buckets.get(step.key) ?? { count: 0 }
    const count = Number(bucket.count ?? 0)
    let conversionRate = null
    if (index > 0) {
      const prevCount = Number(buckets.get(FUNNEL_STEPS[index - 1].key)?.count ?? 0)
      if (prevCount > 0) conversionRate = `${((count / prevCount) * 100).toFixed(1)}%`
    }
    let dropoutRate = null
    let tone = 'normal'
    if (index > 0 && conversionRate) {
      const rate = parseFloat(conversionRate) / 100
      dropoutRate = `${((1 - rate) * 100).toFixed(1)}%`
      if (1 - rate >= DROPOUT_DANGER) tone = 'danger'
      else if (1 - rate >= DROPOUT_WARNING) tone = 'warning'
    }
    return { ...step, count, conversionRate, dropoutRate, tone }
  })
})

const currentChartData = computed(() =>
  funnelLayers.value.map((step) => ({
    name: step.label,
    value: step.count,
    itemStyle: {
      color: step.tone === 'danger' ? '#dc2626' : step.tone === 'warning' ? '#d97706' : '#3b82f6'
    }
  }))
)

const baselineChartData = computed(() => {
  if (!baselineBuckets.value) return []
  const bucketMap = new Map(baselineBuckets.value.map((b) => [b.key, b]))
  return FUNNEL_STEPS.map((step) => ({
    name: step.label,
    value: Number(bucketMap.get(step.key)?.count ?? 0)
  }))
})

async function loadCompareData() {
  if (!compareTabReady || activeTab.value !== 'compare') return
  compareLoading.value = true
  compareError.value = null
  try {
    const [currentRes, baselineRes] = await Promise.all([
      queryBehaviorFunnel({ start_time: new Date(range.value.start).toISOString(), end_time: new Date(range.value.end).toISOString() }),
      queryBehaviorFunnel({ start_time: new Date(baselineRange.value.start).toISOString(), end_time: new Date(baselineRange.value.end).toISOString() })
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

watch(
  [activeTab, range],
  () => { if (compareTabReady && activeTab.value === 'compare') loadCompareData() },
  { immediate: true }
)
</script>

<style scoped>
.funnel-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.funnel-page .page-section {
  margin-bottom: 0;
}

.funnel-page__layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: var(--spacing-md);
  align-items: start;
}

.funnel-page__chart {
  overflow: hidden;
}

.funnel-chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
}

.funnel-chart-header h2 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text);
}

.mock-badge {
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 11px;
  font-weight: 600;
}

.funnel-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.funnel-tab {
  flex: 0 1 auto;
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}

.funnel-tab.active {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-info-bg);
}

.funnel-compare__header {
  margin-bottom: var(--spacing-md);
}

.funnel-compare__header h2 {
  margin: 0 0 var(--spacing-xs);
}

.funnel-compare__range {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.funnel-compare__sep {
  margin: 0 6px;
  color: var(--color-text-muted);
}

.funnel-compare__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
}

.funnel-compare__panel h3 {
  margin: 0 0 var(--spacing-sm);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.funnel-compare__retry {
  margin-top: var(--spacing-sm);
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-primary);
  font-size: 13px;
  cursor: pointer;
}

@media (max-width: 960px) {
  .funnel-page__layout {
    grid-template-columns: 1fr;
  }

  .funnel-compare__grid {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .funnel-tab {
    transition: none;
  }
}
</style>
