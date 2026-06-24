<template>
  <DashboardFrame title="响应耗时走势" subtitle="AVG / P95 / P99">
    <BaseChart :option="option" :loading="loading" height="137px" empty-text="暂无耗时数据" />
  </DashboardFrame>
</template>

<script setup>
import { computed } from 'vue'
import DashboardFrame from './DashboardFrame.vue'
import BaseChart from '../common/charts/BaseChart.vue'
const props = defineProps({ buckets: { type: Array, default: () => [] }, loading: { type: Boolean, default: false } })
const option = computed(() => {
  if (!props.buckets.length) return null
  const rows = [...props.buckets].sort((a, b) => Number(b.extra?.p95 || 0) - Number(a.extra?.p95 || 0))
  return {
    color: ['#2563eb', '#f59e0b', '#ef4444'],
    tooltip: { trigger: 'axis' },
    legend: { top: 0, left: 0, itemWidth: 10, itemHeight: 5, textStyle: { fontSize: 8, color: '#52677b' } },
    grid: { left: 38, right: 12, top: 28, bottom: 27 },
    xAxis: { type: 'category', data: rows.map((item) => item.key), axisLabel: { fontSize: 8, color: '#65788c', hideOverlap: true }, axisTick: { show: false }, axisLine: { lineStyle: { color: '#b8c6d4' } } },
    yAxis: { type: 'value', axisLabel: { fontSize: 8, color: '#65788c' }, splitLine: { lineStyle: { color: '#e4eaf0', type: 'dashed' } } },
    series: [
      { name: '平均响应', type: 'line', smooth: true, showSymbol: true, symbolSize: 3, data: rows.map((item) => Number(item.extra?.p50 || 0)) },
      { name: 'P95', type: 'line', smooth: true, showSymbol: true, symbolSize: 3, data: rows.map((item) => Number(item.extra?.p95 || 0)) },
      { name: 'P99', type: 'line', smooth: true, showSymbol: true, symbolSize: 3, data: rows.map((item) => Number(item.extra?.p99 || 0)) }
    ]
  }
})
</script>
