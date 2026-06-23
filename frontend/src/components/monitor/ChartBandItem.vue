<template>
  <article class="chart-band-card">
    <header class="chart-band-card__header">
      <div>
        <p class="chart-band-card__eyebrow">{{ chartKindLabel }}</p>
        <h3 class="chart-band-card__title">{{ config.title }}</h3>
      </div>
      <span v-if="isMock" class="chart-band-card__mock">演示数据</span>
    </header>

    <EmptyState
      v-if="error"
      compact
      title="图表加载失败"
      :description="error"
    >
      <button type="button" class="chart-band-card__retry" @click="refresh">重试</button>
    </EmptyState>

    <TrendChart
      v-else-if="config.chartType === 'trend'"
      v-bind="chartProps"
      :loading="loading"
      height="220px"
      :placeholder="config.title + '：暂无数据'"
    />

    <BarChart
      v-else-if="config.chartType === 'bar'"
      v-bind="chartProps"
      :horizontal="isBarHorizontal"
      :loading="loading"
      height="220px"
      :placeholder="config.title + '：暂无数据'"
    />

    <PieChart
      v-else-if="config.chartType === 'pie'"
      v-bind="chartProps"
      :loading="loading"
      height="220px"
      :placeholder="config.title + '：暂无数据'"
    />
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { useMetrics } from '../../composables/useMetrics.js'
import TrendChart from '../common/charts/TrendChart.vue'
import BarChart from '../common/charts/BarChart.vue'
import PieChart from '../common/charts/PieChart.vue'
import EmptyState from '../common/EmptyState.vue'

const props = defineProps({
  config: { type: Object, required: true },
  logType: { type: String, default: '' }
})

function buildExtraFilters(config) {
  const opts = config.options ?? {}
  const filters = {}

  if (opts.group_by) filters.group_by = opts.group_by
  if (opts.top_n != null) filters.top_n = opts.top_n
  if (opts.metric) filters.metric = opts.metric

  if (config.chartType === 'trend') {
    filters.interval = opts.interval ?? '1m'
  }

  return filters
}

function formatBucketKey(key) {
  if (key == null || key === '') return '未知'
  return String(key)
}

function pickBuckets(aggregateData, config) {
  if (!aggregateData) return []

  const buckets = aggregateData.buckets ?? []
  const extra = aggregateData.extra ?? {}
  const groupBy = config.options?.group_by

  if (groupBy === 'status_code' && extra.by_status_code?.length) {
    return extra.by_status_code
  }
  if (groupBy === 'client_ip' && extra.by_client_ip?.length) {
    return extra.by_client_ip
  }

  return buckets
}

function bucketCount(bucket) {
  return Number(bucket?.count ?? 0)
}

function bucketValue(bucket) {
  const value = bucket?.value
  if (value != null && !Number.isNaN(Number(value))) return Number(value)
  return bucketCount(bucket)
}

function resolveChartProps(config, aggregateData) {
  const buckets = pickBuckets(aggregateData, config)
  const chartType = config.chartType

  if (chartType === 'pie') {
    return {
      data: buckets.map((b) => ({
        name: formatBucketKey(b.key),
        value: bucketCount(b)
      }))
    }
  }

  if (chartType === 'bar') {
    if (config.template === 'latency') {
      return {
        categories: buckets.map((b) => formatBucketKey(b.key)),
        series: [
          {
            name: 'P95 (ms)',
            data: buckets.map((b) => Number(b.extra?.p95 ?? 0))
          }
        ]
      }
    }

    const useMetricValue = config.template === 'infra_health'
    return {
      categories: buckets.map((b) => formatBucketKey(b.key)),
      series: [
        {
          name: config.title,
          data: buckets.map((b) => (useMetricValue ? bucketValue(b) : bucketCount(b)))
        }
      ]
    }
  }

  if (chartType === 'trend') {
    const useMetricValue = config.template === 'infra_health'
    return {
      categories: buckets.map((b) => formatBucketKey(b.key)),
      series: [
        {
          name: config.title,
          data: buckets.map((b) => (useMetricValue ? bucketValue(b) : bucketCount(b))),
          area: true
        }
      ]
    }
  }

  return { categories: [], series: [], data: [] }
}

const extraFilters = buildExtraFilters(props.config)

const { data, loading, error, refresh, isMock } = useMetrics({
  template: props.config.template,
  logType: props.logType || undefined,
  extraFilters,
  immediate: true
})

const chartProps = computed(() => resolveChartProps(props.config, data.value))

const isBarHorizontal = computed(
  () => props.config.chartType === 'bar' && props.config.options?.top_n != null
)

const chartKindLabel = computed(() => {
  if (props.config.chartType === 'trend') return 'Trend'
  if (props.config.chartType === 'bar') return 'Ranking'
  if (props.config.chartType === 'pie') return 'Distribution'
  return 'Metric'
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
  min-height: 34px;
}

.chart-band-card__eyebrow {
  margin: 0 0 2px;
  color: var(--color-text-muted);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.chart-band-card__title {
  margin: 0;
  color: var(--color-text);
  font-size: 14px;
  font-weight: 700;
}

.chart-band-card__mock {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 11px;
  line-height: 1.4;
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
  transition:
    background var(--transition-fast),
    border-color var(--transition-fast);
}

.chart-band-card__retry:hover {
  border-color: rgba(59, 130, 246, 0.42);
  background: var(--color-primary-soft);
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
