<template>
  <section class="page-section health-overview">
    <header class="health-overview__header">
      <h2>平台健康总览</h2>
      <span v-if="showMockBadge" class="health-overview__mock">演示数据</span>
    </header>

    <div class="health-overview__body">
      <div class="health-overview__gauge">
        <GaugeChart
          :value="healthScore"
          :loading="loading"
          title="综合健康分"
          unit="分"
          height="220px"
          placeholder="健康分：等待流量/错误/耗时聚合"
        />
      </div>

      <div class="health-overview__stats page-grid page-grid-5">
        <StatCard label="日志总量" :value="totalLogsDisplay" />
        <StatCard label="错误率" :value="errorRateDisplay" />
        <StatCard label="平均响应" :value="avgLatencyDisplay" />
        <StatCard label="P95 响应" :value="p95LatencyDisplay" />
        <StatCard label="活跃预警数" :value="activeAlertsDisplay" />
      </div>
    </div>

    <p v-if="metricsError" class="health-overview__error">{{ metricsError }}</p>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import GaugeChart from '../common/charts/GaugeChart.vue'
import StatCard from '../common/StatCard.vue'
import { useMetrics } from '../../composables/useMetrics.js'
import { getActiveAlerts } from '../../api/alerts.js'
import { getSystemStatus } from '../../api/system.js'
import { derivePipelineHealthTone } from '../../utils/systemStatus.js'
import { formatDuration, formatNumber, formatPercent } from '../../utils/format.js'

const traffic = useMetrics({ template: 'traffic' })
const errors = useMetrics({ template: 'errors' })
const latency = useMetrics({ template: 'latency' })

const pipelineTone = ref('unknown')
const activeAlertCount = ref(0)

const loading = computed(
  () => traffic.loading.value || errors.loading.value || latency.loading.value
)

const showMockBadge = computed(
  () => traffic.isMock.value || errors.isMock.value || latency.isMock.value
)

const metricsError = computed(() => {
  const parts = [traffic.error.value, errors.error.value, latency.error.value].filter(Boolean)
  if (!parts.length) return ''
  return parts[0]
})

function sumBucketCounts(buckets) {
  if (!Array.isArray(buckets)) return 0
  return buckets.reduce((sum, bucket) => sum + Number(bucket?.count ?? 0), 0)
}

const totalLogCount = computed(() => {
  const extra = traffic.data.value?.extra
  if (extra?.total_count != null && !Number.isNaN(Number(extra.total_count))) {
    return Number(extra.total_count)
  }
  return sumBucketCounts(traffic.data.value?.buckets)
})

const errorLogCount = computed(() => sumBucketCounts(errors.data.value?.buckets))

const errorRate = computed(() => {
  const total = totalLogCount.value
  if (!total) return null
  return errorLogCount.value / total
})

function readGlobalPercentile(latencyData, key) {
  const value = latencyData?.extra?.global_percentiles?.[key]
  if (value == null || Number.isNaN(Number(value))) return null
  return Number(value)
}

function weightedPercentile(latencyData, key) {
  const direct = readGlobalPercentile(latencyData, key)
  if (direct != null) return direct

  const buckets = latencyData?.buckets ?? []
  let weighted = 0
  let weight = 0
  for (const bucket of buckets) {
    const pct = bucket?.extra?.[key]
    const count = Number(bucket?.count ?? 0)
    if (pct == null || Number.isNaN(Number(pct)) || count <= 0) continue
    weighted += Number(pct) * count
    weight += count
  }
  if (!weight) return null
  return weighted / weight
}

const avgLatencyMs = computed(() => weightedPercentile(latency.data.value, 'p50'))
const p95LatencyMs = computed(() => weightedPercentile(latency.data.value, 'p95'))

const totalLogsDisplay = computed(() => {
  if (loading.value && traffic.data.value == null) return null
  return formatNumber(totalLogCount.value)
})

const errorRateDisplay = computed(() => {
  if (loading.value && errors.data.value == null && traffic.data.value == null) return null
  if (errorRate.value == null) return '—'
  return formatPercent(errorRate.value)
})

const avgLatencyDisplay = computed(() => {
  if (loading.value && latency.data.value == null) return null
  if (avgLatencyMs.value == null) return '—'
  return formatDuration(avgLatencyMs.value)
})

const p95LatencyDisplay = computed(() => {
  if (loading.value && latency.data.value == null) return null
  if (p95LatencyMs.value == null) return '—'
  return formatDuration(p95LatencyMs.value)
})

const activeAlertsDisplay = computed(() => formatNumber(activeAlertCount.value))

/**
 * 综合健康分：错误率 40% + 链路状态 30% + 活跃预警 30%
 */
const healthScore = computed(() => {
  if (loading.value && !traffic.data.value && !errors.data.value && !latency.data.value) {
    return null
  }

  const rate = errorRate.value ?? 0
  const errorScore = Math.max(0, 100 - Math.min(rate * 1000, 100))

  const pipelineScoreMap = {
    success: 100,
    warning: 60,
    danger: 20,
    unknown: 75
  }
  const pipelineScore = pipelineScoreMap[pipelineTone.value] ?? 75

  const alertScore = Math.max(0, 100 - activeAlertCount.value * 15)

  return Math.round(errorScore * 0.4 + pipelineScore * 0.3 + alertScore * 0.3)
})

async function loadPipelineTone() {
  try {
    const res = await getSystemStatus()
    pipelineTone.value = derivePipelineHealthTone(res.data)
  } catch {
    pipelineTone.value = 'unknown'
  }
}

async function loadActiveAlerts() {
  try {
    const res = await getActiveAlerts({ limit: 1 })
    activeAlertCount.value = res.data?.total ?? res.data?.items?.length ?? 0
  } catch {
    activeAlertCount.value = 0
  }
}

onMounted(() => {
  loadPipelineTone()
  loadActiveAlerts()
})
</script>

<style scoped>
.health-overview__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.health-overview__header h2 {
  margin: 0;
}

.health-overview__mock {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 11px;
  line-height: 1.4;
}

.health-overview__body {
  display: grid;
  grid-template-columns: minmax(220px, 280px) 1fr;
  gap: var(--spacing-md);
  align-items: stretch;
}

.health-overview__gauge {
  min-width: 0;
}

.health-overview__stats {
  margin: 0;
}

.health-overview__error {
  margin: var(--spacing-sm) 0 0;
  font-size: 12px;
  color: var(--color-danger);
}

@media (max-width: 960px) {
  .health-overview__body {
    grid-template-columns: 1fr;
  }
}
</style>
