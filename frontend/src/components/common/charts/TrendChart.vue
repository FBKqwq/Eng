<template>
  <BaseChart
    :option="chartOption"
    :loading="loading"
    :height="height"
    :empty-text="placeholder"
  />
</template>

<script setup>
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'

const CHART_COLORS = {
  primary: '#3b82f6',
  success: '#16a34a',
  warning: '#d97706',
  danger: '#dc2626',
  info: '#0284c7',
  border: '#e5e7eb',
  textSecondary: '#6b7280'
}

const SERIES_PALETTE = [
  CHART_COLORS.primary,
  CHART_COLORS.success,
  CHART_COLORS.warning,
  CHART_COLORS.danger,
  CHART_COLORS.info
]

const props = defineProps({
  /** X 轴类目（时间桶或标签） */
  categories: { type: Array, default: () => [] },
  /** 系列数据：[{ name, data, area? }] */
  series: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  height: { type: String, default: '280px' },
  placeholder: { type: String, default: '趋势图占位：等待聚合接口' }
})

const hasData = computed(() => {
  if (!props.categories?.length || !props.series?.length) return false
  return props.series.some((s) => Array.isArray(s.data) && s.data.length > 0)
})

const chartOption = computed(() => {
  if (!hasData.value) return null

  const showLegend = props.series.length > 1

  return {
    color: SERIES_PALETTE,
    tooltip: { trigger: 'axis' },
    legend: showLegend
      ? { bottom: 0, textStyle: { color: CHART_COLORS.textSecondary } }
      : undefined,
    grid: {
      left: 48,
      right: 24,
      top: 24,
      bottom: showLegend ? 40 : 24,
      containLabel: false
    },
    xAxis: {
      type: 'category',
      data: props.categories,
      boundaryGap: false,
      axisLine: { lineStyle: { color: CHART_COLORS.border } },
      axisLabel: { color: CHART_COLORS.textSecondary, fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: CHART_COLORS.textSecondary, fontSize: 11 },
      splitLine: { lineStyle: { color: CHART_COLORS.border, type: 'dashed' } }
    },
    series: props.series.map((s, i) => ({
      name: s.name || `系列${i + 1}`,
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: s.data,
      lineStyle: { width: 2 },
      areaStyle: s.area ? { opacity: 0.12 } : undefined
    }))
  }
})
</script>
