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
.latency-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.latency-panel__header h2 {
  margin: 0;
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
  padding: var(--spacing-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  transition:
    transform 180ms ease,
    box-shadow 180ms ease;
}

.latency-panel__card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.latency-panel__subtitle {
  margin: 0 0 var(--spacing-sm);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
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
