<template>
  <DashboardFrame title="流量与错误" subtitle="REQUEST / ERROR / RATE">
    <template #actions>
      <span class="traffic-panel__unit">每分钟</span>
    </template>
    <BaseChart :option="chartOption" :loading="loading" height="188px" empty-text="暂无流量数据" />
  </DashboardFrame>
</template>

<script setup>
import { computed } from 'vue'
import DashboardFrame from './DashboardFrame.vue'
import BaseChart from '../common/charts/BaseChart.vue'

const props = defineProps({
  trafficBuckets: { type: Array, default: () => [] },
  errorBuckets: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

function label(key) {
  const date = new Date(key)
  return Number.isNaN(date.getTime())
    ? String(key)
    : date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
}

const chartOption = computed(() => {
  const keys = [...new Set([
    ...props.trafficBuckets.map((item) => String(item.key)),
    ...props.errorBuckets.map((item) => String(item.key))
  ])].sort()
  if (!keys.length) return null
  const trafficMap = new Map(props.trafficBuckets.map((item) => [String(item.key), Number(item.count || 0)]))
  const errorMap = new Map(props.errorBuckets.map((item) => [String(item.key), Number(item.count || 0)]))
  const requests = keys.map((key) => trafficMap.get(key) || 0)
  const errors = keys.map((key) => errorMap.get(key) || 0)
  const rates = requests.map((value, index) => value ? Number(((errors[index] / value) * 100).toFixed(2)) : 0)

  return {
    color: ['#2563eb', '#ef4444', '#f59e0b'],
    tooltip: { trigger: 'axis' },
    legend: { top: 0, left: 0, itemWidth: 12, itemHeight: 6, textStyle: { fontSize: 9, color: '#52677b' } },
    grid: { left: 38, right: 34, top: 30, bottom: 22 },
    xAxis: { type: 'category', data: keys.map(label), axisTick: { show: false }, axisLabel: { fontSize: 8, color: '#65788c', hideOverlap: true }, axisLine: { lineStyle: { color: '#b8c6d4' } } },
    yAxis: [
      { type: 'value', axisLabel: { fontSize: 8, color: '#65788c' }, splitLine: { lineStyle: { color: '#e4eaf0', type: 'dashed' } } },
      { type: 'value', axisLabel: { formatter: '{value}%', fontSize: 8, color: '#65788c' }, splitLine: { show: false } }
    ],
    series: [
      { name: '日志量', type: 'bar', data: requests, barMaxWidth: 14, itemStyle: { color: '#3b82f6' } },
      { name: '错误数', type: 'bar', data: errors, barMaxWidth: 7, itemStyle: { color: '#ef4444' } },
      { name: '错误率', type: 'line', yAxisIndex: 1, data: rates, smooth: true, showSymbol: false, lineStyle: { width: 2, color: '#f59e0b' } }
    ]
  }
})
</script>

<style scoped>
.traffic-panel__unit {
  padding: 3px 8px;
  border: 1px solid #9fb1c4;
  color: #52677b;
  font-family: var(--font-mono);
  font-size: 9px;
}
</style>
