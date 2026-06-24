import { computed, onMounted, ref } from 'vue'
import { useMetrics } from '../../composables/useMetrics.js'
import { usePolling } from '../../composables/usePolling.js'
import { getActiveAlerts } from '../../api/alerts.js'
import { getRecentReports } from '../../api/reports.js'
import { getSystemStatus } from '../../api/system.js'
import { derivePipelineHealthTone } from '../../utils/systemStatus.js'

function sumBuckets(buckets) {
  return (buckets ?? []).reduce((sum, bucket) => sum + Number(bucket?.count ?? 0), 0)
}

function readPercentile(data, key) {
  const direct = data?.extra?.global_percentiles?.[key]
  if (direct != null && Number.isFinite(Number(direct))) return Number(direct)

  let weighted = 0
  let weight = 0
  for (const bucket of data?.buckets ?? []) {
    const value = Number(bucket?.extra?.[key])
    const count = Number(bucket?.count ?? 0)
    if (!Number.isFinite(value) || count <= 0) continue
    weighted += value * count
    weight += count
  }
  return weight ? weighted / weight : null
}

export function useDashboardData() {
  const traffic = useMetrics({ template: 'traffic' })
  const errorTrend = useMetrics({ template: 'errors', extraFilters: { interval: '1m' } })
  const errorDistribution = useMetrics({ template: 'errors', extraFilters: { top_n: 10 } })
  const latency = useMetrics({ template: 'latency' })
  const logSources = useMetrics({
    groupBy: 'log_type',
    extraFilters: { top_n: 10 }
  })

  const alerts = ref([])
  const alertTotal = ref(0)
  const latestReport = ref(null)
  const pipelineTone = ref('unknown')
  const supportLoading = ref(true)

  const totalLogs = computed(() => {
    const total = traffic.data.value?.extra?.total_count
    return Number.isFinite(Number(total)) ? Number(total) : sumBuckets(traffic.data.value?.buckets)
  })
  const errorLogs = computed(() => sumBuckets(errorTrend.data.value?.buckets))
  const errorRate = computed(() => (totalLogs.value ? errorLogs.value / totalLogs.value : 0))
  const averageLatency = computed(() => readPercentile(latency.data.value, 'p50'))
  const p95Latency = computed(() => readPercentile(latency.data.value, 'p95'))

  const healthScore = computed(() => {
    const errorScore = Math.max(0, 100 - Math.min(errorRate.value * 450, 100))
    const pipelineScore = { success: 100, warning: 65, danger: 20, unknown: 72 }[pipelineTone.value] ?? 72
    const alertScore = Math.max(0, 100 - alertTotal.value * 2.2)
    return Math.round(errorScore * 0.45 + pipelineScore * 0.3 + alertScore * 0.25)
  })

  const particleTelemetry = computed(() => {
    const bucketCount = traffic.data.value?.buckets?.length || 1
    const averageFlow = totalLogs.value / bucketCount
    return {
      intensity: Math.min(0.96, 0.5 + averageFlow / 240),
      flowRate: Math.min(1, averageFlow / 150),
      anomalyRate: Math.min(1, errorRate.value * 7),
      acceleration: Math.min(1, alertTotal.value / 20),
      healthScore: healthScore.value,
      accentColor: healthScore.value < 60 ? '#ef4444' : healthScore.value < 80 ? '#f59e0b' : '#38bdf8'
    }
  })

  const loading = computed(
    () =>
      traffic.loading.value ||
      errorTrend.loading.value ||
      errorDistribution.loading.value ||
      latency.loading.value ||
      logSources.loading.value ||
      supportLoading.value
  )

  async function loadSupportData() {
    supportLoading.value = true
    const [alertResult, reportResult, statusResult] = await Promise.allSettled([
      getActiveAlerts({ limit: 5 }),
      getRecentReports({ limit: 1 }),
      getSystemStatus()
    ])

    if (alertResult.status === 'fulfilled') {
      alerts.value = alertResult.value.data?.items ?? []
      alertTotal.value = alertResult.value.data?.total ?? alerts.value.length
    }
    if (reportResult.status === 'fulfilled') {
      latestReport.value = reportResult.value.data?.items?.[0] ?? null
    }
    if (statusResult.status === 'fulfilled') {
      pipelineTone.value = derivePipelineHealthTone(statusResult.value.data)
    }
    supportLoading.value = false
  }

  onMounted(loadSupportData)
  usePolling(loadSupportData, 30000, false)

  return {
    traffic,
    errorTrend,
    errorDistribution,
    latency,
    logSources,
    alerts,
    alertTotal,
    latestReport,
    pipelineTone,
    totalLogs,
    errorLogs,
    errorRate,
    averageLatency,
    p95Latency,
    healthScore,
    particleTelemetry,
    loading
  }
}
