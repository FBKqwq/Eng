<template>
  <section class="page-section traffic-error-panel">
    <header class="traffic-error-panel__header">
      <h2>流量与错误</h2>
      <span v-if="showMockBadge" class="traffic-error-panel__mock">演示数据</span>
    </header>

    <article class="traffic-error-panel__card">
      <h3 class="traffic-error-panel__subtitle">流量趋势</h3>
      <EmptyState
        v-if="trendError"
        compact
        title="趋势图加载失败"
        :description="trendError"
      >
        <button type="button" class="traffic-error-panel__retry" @click="retryTrend">重试</button>
      </EmptyState>
      <BaseChart
        v-else
        :option="trafficComboOption"
        :loading="trendLoading"
        height="280px"
        empty-text="流量趋势：暂无数据"
      />
    </article>

    <div class="traffic-error-panel__dist">
      <article class="traffic-error-panel__card">
        <h3 class="traffic-error-panel__subtitle">Top 错误服务</h3>
        <EmptyState
          v-if="distError"
          compact
          title="错误分布加载失败"
          :description="distError"
        >
          <button type="button" class="traffic-error-panel__retry" @click="retryDist">重试</button>
        </EmptyState>
        <BarChart
          v-else
          :categories="serviceBarCategories"
          :series="serviceBarSeries"
          horizontal
          :loading="distLoading"
          height="240px"
          placeholder="错误服务分布：暂无数据"
        />
      </article>

      <article class="traffic-error-panel__card">
        <h3 class="traffic-error-panel__subtitle">error_code 分布</h3>
        <EmptyState
          v-if="distError"
          compact
          title="错误分布加载失败"
          :description="distError"
        >
          <button type="button" class="traffic-error-panel__retry" @click="retryDist">重试</button>
        </EmptyState>
        <PieChart
          v-else
          :data="errorCodePieData"
          :loading="distLoading"
          height="240px"
          placeholder="error_code 分布：暂无数据"
        />
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import BaseChart from '../common/charts/BaseChart.vue'
import BarChart from '../common/charts/BarChart.vue'
import PieChart from '../common/charts/PieChart.vue'
import EmptyState from '../common/EmptyState.vue'
import { useMetrics } from '../../composables/useMetrics.js'

const CHART_COLORS = {
  primary: '#3b82f6',
  danger: '#dc2626',
  border: '#e5e7eb',
  textSecondary: '#6b7280'
}

const TOP_N = 10

const traffic = useMetrics({ template: 'traffic' })
const errorTrend = useMetrics({
  template: 'errors',
  extraFilters: { interval: '1m' }
})
const errorsDist = useMetrics({
  template: 'errors',
  extraFilters: { top_n: TOP_N }
})

const trendLoading = computed(() => traffic.loading.value || errorTrend.loading.value)

const distLoading = computed(() => errorsDist.loading.value)

const showMockBadge = computed(
  () => traffic.isMock.value || errorTrend.isMock.value || errorsDist.isMock.value
)

const trendError = computed(() => traffic.error.value || errorTrend.error.value || '')

const distError = computed(() => errorsDist.error.value || '')

function formatBucketLabel(key) {
  if (key == null || key === '') return '未知'
  const text = String(key)
  if (/^\d{4}-\d{2}/.test(text)) {
    const date = new Date(text)
    if (!Number.isNaN(date.getTime())) {
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      })
    }
  }
  return text
}

function bucketCount(bucket) {
  return Number(bucket?.count ?? 0)
}

function buildAlignedTimeSeries(trafficBuckets, errorBuckets) {
  const trafficList = Array.isArray(trafficBuckets) ? trafficBuckets : []
  const errorList = Array.isArray(errorBuckets) ? errorBuckets : []

  const keySet = new Set()
  for (const bucket of trafficList) keySet.add(String(bucket?.key ?? ''))
  for (const bucket of errorList) keySet.add(String(bucket?.key ?? ''))

  const keys = [...keySet].filter((key) => key !== '').sort()

  const trafficMap = new Map(trafficList.map((b) => [String(b?.key ?? ''), bucketCount(b)]))
  const errorMap = new Map(errorList.map((b) => [String(b?.key ?? ''), bucketCount(b)]))

  return {
    categories: keys.map(formatBucketLabel),
    requests: keys.map((key) => trafficMap.get(key) ?? 0),
    errors: keys.map((key) => errorMap.get(key) ?? 0)
  }
}

const trafficComboOption = computed(() => {
  const { categories, requests, errors } = buildAlignedTimeSeries(
    traffic.data.value?.buckets,
    errorTrend.data.value?.buckets
  )

  if (!categories.length) return null

  const hasValues = requests.some((v) => v > 0) || errors.some((v) => v > 0)
  if (!hasValues) return null

  return {
    color: [CHART_COLORS.primary, CHART_COLORS.danger],
    animation: true,
    animationDuration: 500,
    animationDurationUpdate: 500,
    tooltip: { trigger: 'axis' },
    legend: {
      bottom: 0,
      textStyle: { color: CHART_COLORS.textSecondary }
    },
    grid: {
      left: 48,
      right: 48,
      top: 24,
      bottom: 40,
      containLabel: false
    },
    xAxis: {
      type: 'category',
      data: categories,
      boundaryGap: true,
      axisLine: { lineStyle: { color: CHART_COLORS.border } },
      axisLabel: { color: CHART_COLORS.textSecondary, fontSize: 11 }
    },
    yAxis: [
      {
        type: 'value',
        name: '请求量',
        axisLabel: { color: CHART_COLORS.textSecondary, fontSize: 11 },
        splitLine: { lineStyle: { color: CHART_COLORS.border, type: 'dashed' } }
      },
      {
        type: 'value',
        name: '错误量',
        axisLabel: { color: CHART_COLORS.textSecondary, fontSize: 11 },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '请求量',
        type: 'line',
        smooth: true,
        showSymbol: false,
        yAxisIndex: 0,
        data: requests,
        lineStyle: { width: 2 },
        areaStyle: { opacity: 0.12 }
      },
      {
        name: '错误量',
        type: 'bar',
        yAxisIndex: 1,
        data: errors,
        barMaxWidth: 24
      }
    ]
  }
})

const serviceBarCategories = computed(() => {
  const buckets = errorsDist.data.value?.extra?.by_service ?? []
  return buckets.map((b) => formatBucketLabel(b.key))
})

const serviceBarSeries = computed(() => {
  const buckets = errorsDist.data.value?.extra?.by_service ?? []
  return [
    {
      name: '错误数',
      data: buckets.map((b) => bucketCount(b))
    }
  ]
})

const errorCodePieData = computed(() => {
  const buckets = errorsDist.data.value?.buckets ?? []
  return buckets.map((b) => ({
    name: formatBucketLabel(b.key),
    value: bucketCount(b)
  }))
})

function retryTrend() {
  traffic.refresh()
  errorTrend.refresh()
}

function retryDist() {
  errorsDist.refresh()
}
</script>

<style scoped>
.traffic-error-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.traffic-error-panel__header h2 {
  margin: 0;
}

.traffic-error-panel__mock {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 11px;
  line-height: 1.4;
}

.traffic-error-panel__card {
  padding: var(--spacing-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  transition:
    transform 180ms ease,
    box-shadow 180ms ease;
}

.traffic-error-panel__card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.traffic-error-panel__subtitle {
  margin: 0 0 var(--spacing-sm);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.traffic-error-panel__dist {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
}

.traffic-error-panel__retry {
  margin-top: var(--spacing-sm);
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-primary);
  font-size: 13px;
  cursor: pointer;
  transition: background 150ms ease;
}

.traffic-error-panel__retry:hover {
  background: var(--color-bg);
}

@media (max-width: 960px) {
  .traffic-error-panel__dist {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .traffic-error-panel__card {
    transition: none;
  }

  .traffic-error-panel__card:hover {
    transform: none;
  }
}
</style>
