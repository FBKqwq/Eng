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
import { chartColors, chartPalette, tooltipStyle } from '../../../utils/chartTheme.js'

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
    color: chartColors,
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)', ...tooltipStyle() },
    legend: {
      orient: 'vertical',
      right: 8,
      top: 'center',
      itemWidth: 10,
      itemHeight: 6,
      textStyle: { color: chartPalette.label, fontSize: 11 }
    },
    series: [
      {
        type: 'pie',
        radius: props.donut ? ['48%', '72%'] : '70%',
        center: ['40%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 3 },
        label: { show: false },
        emphasis: {
          scaleSize: 6,
          label: { show: true, fontSize: 13, fontWeight: 'bold', color: chartPalette.text }
        },
        data: props.data
      }
    ]
  }
})
</script>
