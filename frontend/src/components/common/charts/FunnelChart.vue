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
  CHART_COLORS.info,
  CHART_COLORS.success,
  CHART_COLORS.warning,
  CHART_COLORS.danger
]

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
    color: SERIES_PALETTE,
    tooltip: { trigger: 'item', formatter: '{b}: {c}' },
    legend: {
      bottom: 0,
      textStyle: { color: CHART_COLORS.textSecondary, fontSize: 11 }
    },
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
          fontSize: 12
        },
        itemStyle: { borderColor: '#fff', borderWidth: 1 },
        data: props.data
      }
    ]
  }
})
</script>
