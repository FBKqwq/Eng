<template>
  <div class="risk-panel" :aria-busy="loading">
    <div class="risk-panel__gauge">
      <GaugeChart
        :value="gaugeValue"
        :title="riskLabel"
        :loading="loading"
        height="200px"
        :placeholder="gaugePlaceholder"
      />
      <p v-if="reasonText" class="risk-panel__reason">{{ reasonText }}</p>
    </div>

    <section class="risk-panel__metrics" aria-label="窗口指标回放">
      <h3 class="risk-panel__metrics-title">窗口指标回放</h3>
      <div class="risk-panel__metrics-grid">
        <article
          v-for="metric in metricCharts"
          :key="metric.key"
          class="metric-card"
          :class="{ 'is-anomaly': metric.anomaly }"
        >
          <header class="metric-card__header">
            <span class="metric-card__label">{{ metric.label }}</span>
            <span v-if="metric.anomaly" class="metric-card__badge">异常区间</span>
          </header>
          <TrendChart
            :categories="metric.categories"
            :series="metric.series"
            :loading="loading"
            height="96px"
            :placeholder="metric.placeholder"
          />
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import GaugeChart from '../common/charts/GaugeChart.vue'
import TrendChart from '../common/charts/TrendChart.vue'

const props = defineProps({
  /** getReportDetail → data.report */
  report: { type: Object, default: null },
  loading: { type: Boolean, default: false }
})

const RISK_LABELS = {
  low: '低风险',
  medium: '中风险',
  high: '高风险'
}

const RISK_GAUGE_VALUES = {
  low: 85,
  medium: 55,
  high: 25
}

const DEFAULT_METRIC_DEFS = [
  { key: 'traffic', label: '流量', placeholder: '流量趋势：等待 metrics_snapshot' },
  { key: 'errors', label: '错误率', placeholder: '错误趋势：等待 metrics_snapshot' },
  { key: 'latency', label: '耗时', placeholder: '耗时趋势：等待 metrics_snapshot' }
]

const riskLevel = computed(() => String(props.report?.risk_level ?? '').toLowerCase())

const riskLabel = computed(() => RISK_LABELS[riskLevel.value] ?? '风险等级')

const gaugeValue = computed(() => {
  if (!props.report) return null
  return RISK_GAUGE_VALUES[riskLevel.value] ?? RISK_GAUGE_VALUES.medium
})

const gaugePlaceholder = computed(() =>
  props.report ? '风险仪表加载中' : '选中报告后展示风险定级仪表'
)

const reasonText = computed(() => {
  if (!props.report) return ''
  return (
    props.report.risk_reason ||
    props.report.summary ||
    ''
  )
})

const metricCharts = computed(() => {
  const snapshot = resolveMetricsSnapshot(props.report)
  return DEFAULT_METRIC_DEFS.map((def) => {
    const entry = snapshot[def.key] || {}
    const categories = Array.isArray(entry.categories) ? entry.categories : []
    const values = Array.isArray(entry.values)
      ? entry.values
      : Array.isArray(entry.data)
        ? entry.data
        : []
    const hasData = categories.length > 0 && values.length > 0
    return {
      key: def.key,
      label: entry.label || def.label,
      categories,
      series: hasData ? [{ name: entry.label || def.label, data: values, area: true }] : [],
      anomaly: Boolean(entry.anomaly),
      placeholder: def.placeholder
    }
  })
})

function resolveMetricsSnapshot(report) {
  if (!report) return {}

  const direct = report.metrics_snapshot
  if (direct && typeof direct === 'object' && !Array.isArray(direct)) {
    return direct
  }

  if (Array.isArray(direct)) {
    return direct.reduce((acc, item) => {
      const key = item?.key || item?.id
      if (key) acc[key] = item
      return acc
    }, {})
  }

  const metrics = report.metrics
  if (!metrics || typeof metrics !== 'object') return {}

  const normalized = {}
  for (const def of DEFAULT_METRIC_DEFS) {
    const raw = metrics[def.key] || metrics[`${def.key}_trend`]
    const parsed = parseAggregateBuckets(raw)
    if (parsed) normalized[def.key] = { ...parsed, label: def.label }
  }
  return normalized
}

function parseAggregateBuckets(raw) {
  if (!raw) return null

  if (Array.isArray(raw.categories) && (Array.isArray(raw.values) || Array.isArray(raw.data))) {
    return {
      categories: raw.categories,
      values: raw.values || raw.data,
      anomaly: Boolean(raw.anomaly)
    }
  }

  const buckets = raw.buckets || raw.series?.[0]?.data
  if (!Array.isArray(buckets) || !buckets.length) return null

  const categories = []
  const values = []
  for (const bucket of buckets) {
    const key = bucket.key_as_string ?? bucket.key ?? bucket.label
    const value = bucket.doc_count ?? bucket.value ?? bucket.count
    if (key == null || value == null) continue
    categories.push(String(key))
    values.push(Number(value))
  }

  if (!categories.length) return null
  return { categories, values, anomaly: Boolean(raw.anomaly) }
}
</script>

<style scoped>
.risk-panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.risk-panel__gauge {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
}

.risk-panel__reason {
  margin: var(--spacing-sm) 0 0;
  padding-top: var(--spacing-sm);
  border-top: 1px dashed var(--color-border);
  font-size: 13px;
  line-height: 1.55;
  color: var(--color-text-secondary);
}

.risk-panel__metrics-title {
  margin: 0 0 var(--spacing-sm);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
}

.risk-panel__metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-sm);
}

.metric-card {
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  transition: border-color 200ms ease, box-shadow 200ms ease;
}

.metric-card.is-anomaly {
  border-color: var(--color-danger);
  box-shadow: 0 0 0 1px var(--color-danger-bg);
}

.metric-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-xs);
  margin-bottom: 4px;
}

.metric-card__label {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.metric-card__badge {
  padding: 1px 6px;
  border-radius: 999px;
  background: var(--color-danger-bg);
  color: var(--color-danger);
  font-size: 10px;
  line-height: 1.4;
}

@media (max-width: 960px) {
  .risk-panel__metrics-grid {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .metric-card {
    transition: none;
  }
}
</style>
