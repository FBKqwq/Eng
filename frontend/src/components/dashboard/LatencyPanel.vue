<template>
  <section class="page-section latency-panel">
    <header class="latency-panel__header">
      <h2>耗时分布</h2>
      <span v-if="showMockBadge" class="latency-panel__mock">演示数据</span>
    </header>

    <article class="latency-panel__card">
      <h3 class="latency-panel__subtitle">响应耗时走势</h3>
      <EmptyState
        v-if="latency.error.value"
        compact
        title="耗时趋势加载失败"
        :description="latency.error.value"
      >
        <button type="button" class="latency-panel__retry" @click="latency.refresh">重试</button>
      </EmptyState>
      <TrendChart
        v-else
        :categories="latencyCategories"
        :series="latencySeries"
        :loading="latency.loading.value"
        height="280px"
        placeholder="耗时分布：avg / p95 / p99 暂无数据"
      />
    </article>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import TrendChart from '../common/charts/TrendChart.vue'
import EmptyState from '../common/EmptyState.vue'
import { useMetrics } from '../../composables/useMetrics.js'

const latency = useMetrics({ template: 'latency' })

const showMockBadge = computed(() => latency.isMock.value)

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

function readPercentile(bucket, key) {
  const value = bucket?.extra?.[key]
  if (value == null || Number.isNaN(Number(value))) return null
  return Number(value)
}

function isTimeSeriesBuckets(buckets) {
  if (!buckets?.length) return false
  return buckets.every((b) => /^\d{4}-\d{2}/.test(String(b?.key ?? '')))
}

/**
 * 从聚合负载解析耗时折线：时间桶含分位时按时间走势；否则按服务维度展示 avg/p95/p99。
 */
function resolveLatencyChart(buckets) {
  const list = Array.isArray(buckets) ? buckets : []
  if (!list.length) return { categories: [], series: [] }

  const percentileBuckets = list.filter(
    (b) =>
      readPercentile(b, 'p50') != null ||
      readPercentile(b, 'p95') != null ||
      readPercentile(b, 'p99') != null
  )

  if (!percentileBuckets.length) return { categories: [], series: [] }

  const ordered = isTimeSeriesBuckets(percentileBuckets)
    ? percentileBuckets
    : [...percentileBuckets].sort((a, b) => readPercentile(b, 'p95') - readPercentile(a, 'p95'))

  return {
    categories: ordered.map((b) => formatBucketLabel(b.key)),
    series: [
      {
        name: 'Avg',
        data: ordered.map((b) => readPercentile(b, 'p50') ?? readPercentile(b, 'avg') ?? 0)
      },
      {
        name: 'P95',
        data: ordered.map((b) => readPercentile(b, 'p95') ?? 0)
      },
      {
        name: 'P99',
        data: ordered.map((b) => readPercentile(b, 'p99') ?? 0)
      }
    ]
  }
}

const latencyChart = computed(() => resolveLatencyChart(latency.data.value?.buckets))

const latencyCategories = computed(() => latencyChart.value.categories)

const latencySeries = computed(() => latencyChart.value.series)
</script>

<style scoped>
.latency-panel {
  padding: 14px;
  border-radius: 2px;
  background:
    linear-gradient(90deg, rgba(15, 23, 42, 0.022) 1px, transparent 1px),
    #ffffff;
  background-size: 32px 32px;
}

.latency-panel:hover {
  transform: none;
}

.latency-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 2px solid #0f2438;
}

.latency-panel__header h2 {
  margin: 0;
  color: #0f2438;
  font-size: 15px;
  font-weight: 900;
  letter-spacing: 0.05em;
}

.latency-panel__header h2::before {
  display: inline-block;
  width: 5px;
  height: 15px;
  margin-right: 8px;
  background: #0f2438;
  transform: skewX(-16deg);
  vertical-align: -2px;
  content: '';
}

.latency-panel__mock {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 11px;
  line-height: 1.4;
}

.latency-panel__card {
  padding: 12px;
  background: var(--color-surface);
  border: 1px solid #c4d0dc;
  border-radius: 0;
  box-shadow: none;
  transition:
    transform 180ms ease,
    box-shadow 180ms ease;
}

.latency-panel__card:hover {
  border-color: #6e8295;
  transform: none;
  box-shadow: inset 3px 0 0 #0ea5e9;
}

.latency-panel__subtitle {
  margin: 0 0 var(--spacing-sm);
  padding-left: 9px;
  border-left: 3px solid #0ea5e9;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.04em;
  color: #24384b;
}

.latency-panel__retry {
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

.latency-panel__retry:hover {
  background: var(--color-bg);
}

@media (prefers-reduced-motion: reduce) {
  .latency-panel__card {
    transition: none;
  }

  .latency-panel__card:hover {
    transform: none;
  }
}
</style>
