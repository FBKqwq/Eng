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
  compact: { type: Boolean, default: false },
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
        center: ['50%', props.compact ? '50%' : '54%'],
        radius: props.compact ? '82%' : '86%',
        progress: { show: true, width: props.compact ? 9 : 12 },
        axisLine: {
          lineStyle: {
            width: props.compact ? 9 : 12,
            color: [
              [0.6, chartPalette.danger],
              [0.8, chartPalette.warning],
              [1, chartPalette.success]
            ]
          }
        },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: props.compact
          ? { show: false }
          : {
              distance: 10,
              color: chartPalette.label,
              fontSize: 10
            },
        pointer: {
          length: props.compact ? '43%' : '48%',
          width: props.compact ? 4 : 5,
          itemStyle: { color: chartPalette.primary }
        },
        title: {
          offsetCenter: [0, props.compact ? '26%' : '36%'],
          color: chartPalette.label,
          fontSize: props.compact ? 10 : 12,
          fontWeight: 600
        },
        detail: {
          valueAnimation: true,
          formatter: `{value}${props.unit}`,
          offsetCenter: [0, props.compact ? '52%' : '58%'],
          fontSize: props.compact ? 24 : 28,
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
