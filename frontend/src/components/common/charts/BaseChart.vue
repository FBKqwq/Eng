<template>
  <div class="base-chart" :style="{ height }">
    <div v-if="loading" class="chart-overlay">加载中...</div>
    <div v-else-if="isEmpty" class="chart-overlay">
      <slot name="empty">
        <span>{{ emptyText }}</span>
      </slot>
    </div>
    <div ref="chartRef" class="chart-canvas" :class="{ 'chart-canvas--hidden': loading || isEmpty }" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart, BarChart, PieChart, GaugeChart, FunnelChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  LineChart,
  BarChart,
  PieChart,
  GaugeChart,
  FunnelChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  CanvasRenderer
])

const props = defineProps({
  option: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  height: { type: String, default: '240px' },
  emptyText: { type: String, default: '等待数据' }
})

const chartRef = ref(null)
let chartInstance = null

const isEmpty = computed(() => !props.option || Object.keys(props.option).length === 0)

/** 合并动效默认项，供数据刷新时平滑过渡 */
function withAnimationDefaults(option) {
  return {
    animation: true,
    animationDuration: 500,
    animationDurationUpdate: 500,
    ...option
  }
}

function initChart() {
  if (!chartRef.value || props.loading || isEmpty.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  chartInstance.setOption(withAnimationDefaults(props.option), { notMerge: false })
}

function clearChart() {
  chartInstance?.clear()
}

function handleResize() {
  chartInstance?.resize()
}

async function refreshChart() {
  await nextTick()
  if (props.loading || isEmpty.value) {
    clearChart()
    return
  }
  initChart()
}

watch(() => props.option, refreshChart, { deep: true })
watch(() => props.loading, refreshChart)

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped>
.base-chart {
  position: relative;
  width: 100%;
}
.chart-canvas {
  width: 100%;
  height: 100%;
}
.chart-canvas--hidden {
  visibility: hidden;
}
.chart-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: 13px;
  z-index: 1;
}
</style>
