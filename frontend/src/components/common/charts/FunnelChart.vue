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
import { chartColors, chartPalette, legendStyle, tooltipStyle } from '../../../utils/chartTheme.js'

const props = defineProps({
  /** 漏斗阶段：[{ name, value }] */
  data: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  height: { type: String, default: '320px' },
  placeholder: { type: String, default: '漏斗图占位：等待 behavior_funnel 聚合接口' }
})

const hasData = computed(
  () => Array.isArray(props.data) && props.data.some((d) => d && d.value != null)
)

const chartOption = computed(() => {
  if (!hasData.value) return null

  return {
    color: chartColors,
    tooltip: { trigger: 'item', formatter: '{b}: {c}', ...tooltipStyle() },
    legend: legendStyle(),
    series: [
      {
        type: 'funnel',
        left: '10%',
        right: '10%',
        top: 16,
        bottom: 32,
        min: 0,
        max: Math.max(...props.data.map((d) => d.value ?? 0), 1),
        minSize: '20%',
        maxSize: '100%',
        sort: 'descending',
        gap: 4,
        label: {
          show: true,
          position: 'inside',
          color: '#fff',
          fontSize: 12,
          fontWeight: 700
        },
        itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 4 },
        emphasis: {
          label: { color: chartPalette.text }
        },
        data: props.data
      }
    ]
  }
})
</script>
