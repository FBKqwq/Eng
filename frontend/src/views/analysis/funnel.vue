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
            placeholder="当前窗口漏斗：等待 behavior_funnel 聚合"
          />
        </div>
        <div class="funnel-compare__panel">
          <h3>对比时段（上一等长窗口）</h3>
          <FunnelChart
            :data="baselineChartData"
            :loading="compareLoading"
            height="300px"
            placeholder="对比窗口漏斗：等待 behavior_funnel 聚合"
          />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useTimeRange } from '../../composables/useTimeRange.js'
import { queryBehaviorFunnel } from '../../api/metrics.js'
import FunnelMain from '../../components/analysis-funnel/FunnelMain.vue'
import LossLocator from '../../components/analysis-funnel/LossLocator.vue'
import FunnelChart from '../../components/common/charts/FunnelChart.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import { formatTime } from '../../utils/format.js'

/**
 * 双窗口对比 REST / es_compare_time_windows 前端封装未就绪前保持 false。
 * 就绪后改为 true，对比 tab 将展示双漏斗并排（当前窗 vs 上一等长窗口）。
 */
const COMPARE_TAB_READY = false

/** 五步漏斗顺序（对齐 FunnelMain / field_catalog.funnel_steps） */
const FUNNEL_STEPS = [
  { key: 'page_view', label: '页面浏览' },
  { key: 'product_click', label: '商品点击' },
  { key: 'add_to_cart', label: '加入购物车' },
  { key: 'checkout_click', label: '结算点击' },
  { key: 'pay_button_click', label: '支付点击' }
]

/** 注入全局时间窗，子组件 useMetrics 自动联动 */
const { range } = useTimeRange()

const compareTabReady = COMPARE_TAB_READY
const activeTab = ref('main')
const selectedStep = ref('')

const compareLoading = ref(false)
const compareError = ref(null)
const currentBuckets = ref(null)
const baselineBuckets = ref(null)

const baselineRange = computed(() => {
  const { start, end } = range.value
  const duration = Math.max(0, end - start)
  return {
    start: start - duration,
    end: start
  }
})

function bucketsToChartData(buckets) {
  const bucketMap = new Map((buckets ?? []).map((bucket) => [bucket.key, bucket]))
  return FUNNEL_STEPS.map((step) => ({
    name: step.label,
    value: Number(bucketMap.get(step.key)?.count ?? 0)
  }))
}

const currentChartData = computed(() => bucketsToChartData(currentBuckets.value))
const baselineChartData = computed(() => bucketsToChartData(baselineBuckets.value))

function buildPayload(windowRange) {
  return {
    start_time: new Date(windowRange.start).toISOString(),
    end_time: new Date(windowRange.end).toISOString()
  }
}

async function loadCompareData() {
  if (!compareTabReady || activeTab.value !== 'compare') return

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

watch(
  [activeTab, range],
  () => {
    if (compareTabReady && activeTab.value === 'compare') {
      loadCompareData()
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.funnel-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.funnel-page :deep(.page-section) {
  margin-bottom: 0;
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
  line-height: 1.3;
  cursor: pointer;
  transition:
    border-color 0.15s ease-out,
    color 0.15s ease-out,
    background 0.15s ease-out;
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
