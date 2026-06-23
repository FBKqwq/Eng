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
  textSecondary: '#6b7280'
}

const SERIES_PALETTE = [
  CHART_COLORS.primary,
  CHART_COLORS.success,
  CHART_COLORS.warning,
  CHART_COLORS.danger,
  CHART_COLORS.info,
  '#8b5cf6',
  '#ec4899'
]

const props = defineProps({
  /** 扇区数据：[{ name, value }] */
  data: { type: Array, default: () => [] },
  /** 环形图（默认）或实心饼图 */
  donut: { type: Boolean, default: true },
  loading: { type: Boolean, default: false },
  height: { type: String, default: '240px' },
  placeholder: { type: String, default: '环形/饼图占位：等待聚合接口' }
})

const hasData = computed(
  () => Array.isArray(props.data) && props.data.some((d) => d && d.value != null)
)

const chartOption = computed(() => {
  if (!hasData.value) return null

  return {
    color: SERIES_PALETTE,
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      orient: 'vertical',
      right: 8,
      top: 'center',
      textStyle: { color: CHART_COLORS.textSecondary, fontSize: 11 }
    },
    series: [
      {
        type: 'pie',
        radius: props.donut ? ['42%', '68%'] : '68%',
        center: ['40%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        emphasis: {
          label: { show: true, fontSize: 13, fontWeight: 'bold' }
        },
        data: props.data
      }
    ]
  }
})
</script>
