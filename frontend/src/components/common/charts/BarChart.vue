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
import {
  categoryAxis,
  chartColors,
  chartGrid,
  legendStyle,
  tooltipStyle,
  valueAxis
} from '../../../utils/chartTheme.js'

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
  const catAxis = categoryAxis(props.categories)
  const valAxis = valueAxis()

  return {
    color: chartColors,
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...tooltipStyle() },
    legend: showLegend ? legendStyle() : undefined,
    grid: chartGrid({ legend: showLegend, horizontal: props.horizontal }),
    xAxis: props.horizontal ? valAxis : catAxis,
    yAxis: props.horizontal ? catAxis : valAxis,
    series: props.series.map((s, i) => ({
      name: s.name || `系列${i + 1}`,
      type: 'bar',
      data: s.data,
      barMaxWidth: 28,
      itemStyle: {
        borderRadius: props.horizontal ? [0, 6, 6, 0] : [6, 6, 0, 0],
        color: chartColors[i % chartColors.length]
      },
      emphasis: { focus: 'series' }
    }))
  }
})
</script>
