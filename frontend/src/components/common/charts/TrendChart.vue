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
  softArea,
  tooltipStyle,
  valueAxis
} from '../../../utils/chartTheme.js'

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
    color: chartColors,
    tooltip: { trigger: 'axis', axisPointer: { type: 'line' }, ...tooltipStyle() },
    legend: showLegend ? legendStyle() : undefined,
    grid: chartGrid({ legend: showLegend }),
    xAxis: categoryAxis(props.categories, { boundaryGap: false }),
    yAxis: valueAxis(),
    series: props.series.map((s, i) => ({
      name: s.name || `系列${i + 1}`,
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: s.data,
      lineStyle: {
        width: 2.5,
        shadowBlur: 8,
        shadowColor: `${chartColors[i % chartColors.length]}33`
      },
      areaStyle: s.area ? softArea(chartColors[i % chartColors.length]) : undefined,
      emphasis: { focus: 'series' }
    }))
  }
})
</script>
