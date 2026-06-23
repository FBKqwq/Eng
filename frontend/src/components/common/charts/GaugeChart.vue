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
import { chartPalette, tooltipStyle } from '../../../utils/chartTheme.js'

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
        startAngle: 205,
        endAngle: -25,
        center: ['50%', '54%'],
        radius: '86%',
        progress: { show: true, width: 12 },
        axisLine: {
          lineStyle: {
            width: 12,
            color: [
              [0.6, chartPalette.danger],
              [0.8, chartPalette.warning],
              [1, chartPalette.success]
            ]
          }
        },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: {
          distance: 10,
          color: chartPalette.label,
          fontSize: 10
        },
        pointer: {
          length: '48%',
          width: 5,
          itemStyle: { color: chartPalette.primary }
        },
        title: {
          offsetCenter: [0, '36%'],
          color: chartPalette.label,
          fontSize: 12,
          fontWeight: 600
        },
        detail: {
          valueAnimation: true,
          formatter: `{value}${props.unit}`,
          offsetCenter: [0, '58%'],
          fontSize: 28,
          fontWeight: 800,
          color: chartPalette.text
        },
        tooltip: tooltipStyle(),
        data: [{ value: props.value, name: props.title }]
      }
    ]
  }
})
</script>
