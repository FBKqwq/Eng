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
  categories: { type: Array, default: () => [] },
  /** 系列数据：[{ name, data }] */
  series: { type: Array, default: () => [] },
  /** 横向条形图 */
  horizontal: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  height: { type: String, default: '240px' },
  placeholder: { type: String, default: '柱状/条形图占位：等待聚合接口' }
})

const hasData = computed(() => {
  if (!props.categories?.length || !props.series?.length) return false
  return props.series.some((s) => Array.isArray(s.data) && s.data.length > 0)
})

const chartOption = computed(() => {
  if (!hasData.value) return null

  const showLegend = props.series.length > 1
  const categoryAxis = {
    type: 'category',
    data: props.categories,
    axisLine: { lineStyle: { color: CHART_COLORS.border } },
    axisLabel: { color: CHART_COLORS.textSecondary, fontSize: 11 }
  }
  const valueAxis = {
    type: 'value',
    axisLabel: { color: CHART_COLORS.textSecondary, fontSize: 11 },
    splitLine: { lineStyle: { color: CHART_COLORS.border, type: 'dashed' } }
  }

  return {
    color: SERIES_PALETTE,
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
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
    xAxis: props.horizontal ? valueAxis : categoryAxis,
    yAxis: props.horizontal ? categoryAxis : valueAxis,
    series: props.series.map((s, i) => ({
      name: s.name || `系列${i + 1}`,
      type: 'bar',
      data: s.data,
      barMaxWidth: 32
    }))
  }
})
</script>
