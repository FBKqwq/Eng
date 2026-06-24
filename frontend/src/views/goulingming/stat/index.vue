<template>
  <div class="stat-page">
    <!-- 时间范围联动提示条 -->
    <p class="stat-page__time-note">
      数据时间范围：
      <span class="mono">{{ formatTime(range.start) }}</span>
      &nbsp;–&nbsp;
      <span class="mono">{{ formatTime(range.end) }}</span>
    </p>

    <!-- 数字指标卡片区 -->
    <section class="stat-page__kpi" aria-label="核心指标">
      <StatCard
        v-for="card in kpiCards"
        :key="card.label"
        v-bind="card"
        :loading="loading"
      />
    </section>

    <!-- 图表区 -->
    <section class="stat-page__charts" aria-label="趋势图表">
      <TrafficTrendChart
        :categories="trafficCategories"
        :series="trafficSeries"
        :loading="chartsLoading"
        title="请求量趋势"
        :is-demo="USE_MOCK"
      />
      <ErrorTrendChart
        :categories="errorCategories"
        :series="errorSeries"
        :loading="chartsLoading"
        title="错误率趋势"
        :is-demo="USE_MOCK"
      />
      <LatencyChart
        :categories="latencyCategories"
        :series="latencySeries"
        :loading="chartsLoading"
        title="延迟分布"
        :is-demo="USE_MOCK"
      />
    </section>

    <!-- 底部状态列表 -->
    <section class="stat-page__list" aria-label="各服务状态">
      <ServiceStatusList :items="serviceItems" :loading="loading" :last-updated="lastUpdated" />
    </section>

    <!-- 请求失败提示 -->
    <EmptyState
      v-if="fetchError"
      class="stat-page__error"
      title="加载失败"
      :description="fetchError"
      icon="⚠"
    />
  </div>
</template>

<script setup>
import { ref, inject, onMounted, onUnmounted, watch } from 'vue'
import StatCard from '../../../components/common/StatCard.vue'
import EmptyState from '../../../components/common/EmptyState.vue'
import ServiceStatusList from './components/ServiceStatusList.vue'
import TrafficTrendChart from './components/TrafficTrendChart.vue'
import ErrorTrendChart from './components/ErrorTrendChart.vue'
import LatencyChart from './components/LatencyChart.vue'
import { getGoulingmingStats, getServiceStatus, getTrafficTrend, getErrorTrend, getLatencyDistribution, USE_MOCK } from '../../../api/goulingming.js'
import { formatTime } from '../../../utils/format.js'

const range = inject('timeRange', { start: Date.now() - 3600_000, end: Date.now() })

const loading = ref(false)
const chartsLoading = ref(false)
const fetchError = ref('')
const kpiCards = ref([
  { label: '总请求量', value: null, hint: '最近 1 小时', delta: null, deltaDirection: '' },
  { label: '错误率', value: null, hint: '最近 1 小时', delta: null, deltaDirection: '' },
  { label: '平均耗时', value: null, hint: '最近 1 小时', delta: null, deltaDirection: '' },
  { label: '活跃服务', value: null, hint: '在线节点', delta: null, deltaDirection: '' }
])
const serviceItems = ref([])

// 图表数据
const trafficCategories = ref([])
const trafficSeries = ref([])
const errorCategories = ref([])
const errorSeries = ref([])
const latencyCategories = ref([])
const latencySeries = ref([])

/** 仅拉取 stats（含 KPI 指标），随 timeRange 联动 */
async function fetchStats() {
  loading.value = true
  try {
    const statsRes = await getGoulingmingStats({ start_time: range.start, end_time: range.end })
    const s = statsRes.data ?? {}

    kpiCards.value = [
      {
        label: '总请求量',
        value: s.total_requests ?? '-',
        hint: '最近 1 小时',
        delta: s.total_requests_delta ?? null,
        deltaDirection: s.total_requests_delta > 0 ? 'up' : s.total_requests_delta < 0 ? 'down' : 'flat'
      },
      {
        label: '错误率',
        value: s.error_rate != null ? `${(s.error_rate * 100).toFixed(2)}%` : '-',
        hint: '最近 1 小时',
        delta: s.error_rate_delta ?? null,
        deltaDirection: s.error_rate_delta > 0 ? 'down' : s.error_rate_delta < 0 ? 'up' : 'flat'
      },
      {
        label: '平均耗时',
        value: s.avg_latency != null ? `${s.avg_latency}ms` : '-',
        hint: '最近 1 小时',
        delta: s.avg_latency_delta ?? null,
        deltaDirection: s.avg_latency_delta > 0 ? 'down' : s.avg_latency_delta < 0 ? 'up' : 'flat'
      },
      {
        label: '活跃服务',
        value: s.active_services ?? '-',
        hint: '在线节点',
        delta: null,
        deltaDirection: ''
      }
    ]
    fetchError.value = ''
  } catch (e) {
    console.warn('[goulingming/stat] fetch stats failed:', e.message)
    fetchError.value = e.message || '数据加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

/** 仅拉取服务状态，高频轮询更新 */
async function pollServices() {
  try {
    const svcRes = await getServiceStatus()
    serviceItems.value = (svcRes.data?.services ?? []).map((svc) => ({
      name: svc.name,
      status: svc.status ?? 'unknown',
      qps: svc.qps,
      error_rate: svc.error_rate
    }))
    const now = new Date()
    lastUpdated.value = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
  } catch (e) {
    console.warn('[goulingming/stat] poll services failed:', e.message)
  }
}

async function fetchCharts() {
  chartsLoading.value = true
  const payload = { start_time: range.start, end_time: range.end }
  try {
    const [tr, er, ld] = await Promise.all([
      getTrafficTrend(payload),
      getErrorTrend(payload),
      getLatencyDistribution(payload)
    ])

    const trData = tr.data ?? {}
    trafficCategories.value = trData.categories ?? []
    trafficSeries.value = trData.series ?? []

    const erData = er.data ?? {}
    errorCategories.value = erData.categories ?? []
    errorSeries.value = erData.series ?? []

    const ldData = ld.data ?? {}
    latencyCategories.value = ldData.categories ?? []
    latencySeries.value = ldData.series ?? []
  } catch (e) {
    console.warn('[goulingming/stat] fetch charts failed:', e.message)
  } finally {
    chartsLoading.value = false
  }
}

const SERVICE_POLL_INTERVAL = 15_000 // 15 秒轮询服务状态
let pollTimer = null
const lastUpdated = ref('')

function startPolling() {
  stopPolling()
  pollTimer = setInterval(pollServices, SERVICE_POLL_INTERVAL)
}

function stopPolling() {
  if (pollTimer !== null) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onMounted(() => {
  fetchStats()
  fetchCharts()
  pollServices()
  startPolling()
})

onUnmounted(stopPolling)

watch(range, () => { fetchStats(); fetchCharts() }, { deep: true })
</script>

<style scoped>
.stat-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.stat-page__time-note {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-muted);
}

.mono {
  font-family: var(--font-mono);
  font-size: 11px;
}

.stat-page__kpi {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

.stat-page__list {
  margin-top: var(--spacing-sm);
}

.stat-page__charts {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: var(--spacing-md);
}

.stat-page__error {
  margin-top: var(--spacing-sm);
}
</style>
