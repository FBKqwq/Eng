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
          compact
          height="176px"
          placeholder="健康分：等待流量/错误/耗时聚合"
        />
      </div>

      <div class="health-overview__stats">
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
import { computed, onMounted, ref, watch } from 'vue'
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
const emit = defineEmits(['telemetry-change'])

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

const telemetryState = computed(() => {
  const total = totalLogCount.value
  const bucketCount = traffic.data.value?.buckets?.length || 1
  const averagePerBucket = total / bucketCount
  const flowRate = Math.min(1, averagePerBucket / 160)
  const anomalyRate = Math.min(1, (errorRate.value ?? 0) * 12)
  const acceleration = Math.min(1, activeAlertCount.value / 12)
  const score = healthScore.value ?? 75

  return {
    intensity: Math.min(0.92, 0.46 + flowRate * 0.38),
    flowRate,
    anomalyRate,
    acceleration,
    healthScore: score,
    accentColor: score < 60 ? '#ef4444' : score < 80 ? '#f59e0b' : '#38bdf8'
  }
})

watch(
  telemetryState,
  (value) => emit('telemetry-change', value),
  { immediate: true }
)

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
.health-overview {
  padding: 14px;
  border: 1px solid rgba(125, 211, 252, 0.28);
  border-radius: 0;
  background: linear-gradient(135deg, rgba(4, 14, 27, 0.8), rgba(9, 27, 47, 0.7));
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.025);
}

.health-overview:hover {
  border-color: rgba(125, 211, 252, 0.5);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
  transform: none;
}

.health-overview__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: 8px;
}

.health-overview__header h2 {
  margin: 0;
  color: #f8fbff;
  font-size: 15px;
  letter-spacing: 0.05em;
}

.health-overview__header h2::before {
  display: inline-block;
  width: 4px;
  height: 14px;
  margin-right: 8px;
  background: #38bdf8;
  transform: skewX(-16deg);
  vertical-align: -2px;
  content: '';
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
  grid-template-columns: 174px minmax(0, 1fr);
  gap: 10px;
  align-items: stretch;
}

.health-overview__gauge {
  min-width: 0;
}

.health-overview__stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 7px;
}

.health-overview__stats :deep(.stat-card) {
  min-height: 74px;
  padding: 10px 11px;
  border: 1px solid rgba(125, 211, 252, 0.2);
  border-radius: 0;
  background: rgba(7, 20, 36, 0.62);
  box-shadow: none;
}

.health-overview__stats :deep(.stat-card:last-child) {
  grid-column: 1 / -1;
}

.health-overview__stats :deep(.stat-card::before) {
  right: auto;
  width: 4px;
  height: 100%;
  border-radius: 0;
  background: #38bdf8;
}

.health-overview__stats :deep(.label) {
  font-size: 10px;
  color: #91a9bf;
}

.health-overview__stats :deep(.value-row) {
  margin-top: 4px;
}

.health-overview__stats :deep(.value) {
  font-size: 20px;
  color: #f8fbff;
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
