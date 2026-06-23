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

/** 与设计令牌 index.css 对齐的图表色 */
const CHART_COLORS = {
  success: '#16a34a',
  warning: '#d97706',
  danger: '#dc2626',
  textSecondary: '#6b7280'
}

const props = defineProps({
  /** 仪表当前值；null/undefined 时显示空态 */
  value: { type: Number, default: null },
  min: { type: Number, default: 0 },
  max: { type: Number, default: 100 },
  title: { type: String, default: '' },
  unit: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  height: { type: String, default: '240px' },
  placeholder: { type: String, default: '仪表盘占位：等待聚合接口' }
})

const hasData = computed(
  () => props.value !== null && props.value !== undefined && !Number.isNaN(props.value)
)

const chartOption = computed(() => {
  if (!hasData.value) return null

  return {
    series: [
      {
        type: 'gauge',
        min: props.min,
        max: props.max,
        progress: { show: true, width: 12 },
        axisLine: {
          lineStyle: {
            width: 12,
            color: [
              [0.6, CHART_COLORS.danger],
              [0.8, CHART_COLORS.warning],
              [1, CHART_COLORS.success]
            ]
          }
        },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { color: CHART_COLORS.textSecondary, fontSize: 11 },
        pointer: { width: 5 },
        detail: {
          valueAnimation: true,
          formatter: `{value}${props.unit}`,
          fontSize: 24,
          fontWeight: 'bold',
          color: CHART_COLORS.textSecondary
        },
        data: [{ value: props.value, name: props.title }]
      }
    ]
  }
})
</script>
