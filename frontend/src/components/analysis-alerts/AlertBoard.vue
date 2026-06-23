<template>
  <div class="alert-board" :aria-busy="loading">
    <div class="page-grid page-grid-3">
      <StatCard
        label="活跃"
        :value="displayCounts.active"
        hint="active 预警"
        class="stat-card-active"
        :class="{ 'has-active': displayCounts.active > 0 }"
      />
      <StatCard label="已确认" :value="displayCounts.acknowledged" hint="acknowledged" />
      <StatCard label="已解决" :value="displayCounts.resolved" hint="resolved" />
    </div>

    <article class="trend-panel">
      <header class="trend-panel__header">
        <h3>24h 预警趋势</h3>
        <span v-if="displayMockBadge" class="trend-panel__mock">演示数据</span>
      </header>
      <TrendChart
        :categories="trendCategories"
        :series="trendSeriesData"
        :loading="loading"
        height="120px"
        placeholder="暂无 24h 趋势数据"
      />
    </article>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import StatCard from '../common/StatCard.vue'
import TrendChart from '../common/charts/TrendChart.vue'

const props = defineProps({
  /** { active, acknowledged, resolved } */
  counts: {
    type: Object,
    default: () => ({ active: 0, acknowledged: 0, resolved: 0 })
  },
  /** 24h 趋势 X 轴类目；未传时使用内置 mock 序列 */
  trendCategories: { type: Array, default: () => [] },
  /** 24h 趋势数值序列；与 trendCategories 对齐 */
  trendValues: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  /** 使用 mock 趋势时显示「演示数据」角标 */
  showMockBadge: { type: Boolean, default: false }
})

const MOCK_TREND = buildMockTrend24h()

const displayCounts = computed(() => ({
  active: props.counts?.active ?? 0,
  acknowledged: props.counts?.acknowledged ?? 0,
  resolved: props.counts?.resolved ?? 0
}))

const usingMockTrend = computed(
  () => !props.trendCategories?.length || !props.trendValues?.length
)

const trendCategories = computed(() =>
  usingMockTrend.value ? MOCK_TREND.categories : props.trendCategories
)

const trendSeriesData = computed(() => [
  {
    name: '预警数',
    data: usingMockTrend.value ? MOCK_TREND.values : props.trendValues,
    area: true
  }
])

const displayMockBadge = computed(() => props.showMockBadge || usingMockTrend.value)

function buildMockTrend24h() {
  const categories = []
  const values = []
  const now = Date.now()
  for (let i = 23; i >= 0; i -= 1) {
    const hour = new Date(now - i * 3_600_000)
    categories.push(
      hour.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
    )
    values.push(Math.max(0, Math.round(2 + Math.sin(i / 3) * 2 + (i % 5 === 0 ? 3 : 0))))
  }
  return { categories, values }
}
</script>

<style scoped>
.alert-board {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.stat-card-active.has-active {
  border-color: color-mix(in srgb, var(--color-danger) 35%, var(--color-border));
}

.stat-card-active.has-active::before {
  background: var(--color-danger);
  opacity: 0.65;
}

.trend-panel {
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.trend-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.trend-panel__header h3 {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.trend-panel__mock {
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 11px;
  line-height: 1.4;
}

</style>
