<template>
  <article class="chart-band-card">
    <header class="chart-band-card__header">
      <div class="chart-band-card__titles">
        <h3 class="chart-band-card__title">{{ config.title }}</h3>
        <p class="chart-band-card__caliber">{{ caliberText }}</p>
      </div>
      <div class="chart-band-card__meta">
        <span v-if="isMock" class="chart-band-card__mock">演示数据</span>
        <span v-if="unitText" class="chart-band-card__unit">单位：{{ unitText }}</span>
        <span class="chart-band-card__refresh">刷新：{{ refreshedLabel }}</span>
      </div>
    </header>

    <EmptyState
      v-if="error"
      compact
      title="图表加载失败"
      :description="error"
    >
      <button type="button" class="chart-band-card__retry" @click="refresh">重试</button>
    </EmptyState>

    <EmptyState
      v-else-if="!loading && isEmpty"
      compact
      title="暂无聚合数据"
      :description="config.description || '当前时间窗内无可用数据'"
    />

    <TrendChart
      v-else-if="config.chartType === 'trend'"
      v-bind="chartProps"
      :loading="loading"
      height="240px"
      :placeholder="config.title + '：暂无数据'"
    />

    <BarChart
      v-else-if="config.chartType === 'bar'"
      v-bind="chartProps"
      :horizontal="isBarHorizontal"
      :loading="loading"
      height="240px"
      :placeholder="config.title + '：暂无数据'"
    />

    <PieChart
      v-else-if="config.chartType === 'pie'"
      v-bind="chartProps"
      :loading="loading"
      height="240px"
      :placeholder="config.title + '：暂无数据'"
    />
  </article>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useMetrics } from '../../composables/useMetrics.js'
import { resolveChartData, buildMetricsPayload } from '../../utils/chartResolvers.js'
import TrendChart from '../common/charts/TrendChart.vue'
import BarChart from '../common/charts/BarChart.vue'
import PieChart from '../common/charts/PieChart.vue'
import EmptyState from '../common/EmptyState.vue'

const props = defineProps({
  config: { type: Object, required: true },
  logType: { type: String, default: '' }
})

const lastRefreshedAt = ref(null)

const { data, loading, error, refresh, isMock } = useMetrics({
  template: props.config.template,
  logType: props.logType || undefined,
  extraFilters: buildMetricsPayload(props.config, props.logType),
  immediate: true
})

watch(
  () => data.value,
  (val) => {
    if (val) lastRefreshedAt.value = Date.now()
  },
  { immediate: true }
)

const resolved = computed(() => resolveChartData(props.config, data.value))
const chartProps = computed(() => resolved.value.chartProps)
const isEmpty = computed(() => resolved.value.meta.empty)
const caliberText = computed(
  () => resolved.value.meta.caliber || props.config.description || '后端预置聚合模板'
)
const unitText = computed(() => resolved.value.meta.unit || '')

const isBarHorizontal = computed(
  () => props.config.chartType === 'bar' && props.config.template !== 'behavior_funnel'
)

const refreshedLabel = computed(() => {
  if (loading.value) return '加载中…'
  if (!lastRefreshedAt.value) return '—'
  return new Date(lastRefreshedAt.value).toLocaleTimeString('zh-CN', { hour12: false })
})
</script>

<style scoped>
.chart-band-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  min-width: 0;
  padding: var(--spacing-md);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.96));
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  transition:
    transform var(--transition-fast),
    box-shadow var(--transition-fast),
    border-color var(--transition-fast);
}

.chart-band-card:hover {
  transform: translateY(-2px);
  border-color: rgba(59, 130, 246, 0.34);
  box-shadow: var(--shadow-card-hover);
}

.chart-band-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-sm);
}

.chart-band-card__title {
  margin: 0 0 4px;
  color: var(--color-text);
  font-size: 15px;
  font-weight: 700;
}

.chart-band-card__caliber {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.45;
}

.chart-band-card__meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
  font-size: 11px;
  color: var(--color-text-muted);
}

.chart-band-card__mock {
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.chart-band-card__unit,
.chart-band-card__refresh {
  white-space: nowrap;
}

.chart-band-card__retry {
  margin-top: var(--spacing-sm);
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

@media (prefers-reduced-motion: reduce) {
  .chart-band-card {
    transition: none;
  }

  .chart-band-card:hover {
    transform: none;
  }
}
</style>
