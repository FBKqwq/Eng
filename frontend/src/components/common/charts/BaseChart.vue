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
let needsFullReplace = true
let motionQuery = null

/** 图表数据刷新过渡时长（skill §9.3：300~500ms） */
const CHART_ANIMATION_MS = 400

function prefersReducedMotion() {
  return typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/** 合并动效默认项；reduce-motion 时关闭 ECharts 动画 */
function withAnimationDefaults(option) {
  if (prefersReducedMotion()) {
    return { ...option, animation: false }
  }
  return {
    ...option,
    animation: true,
    animationDuration: CHART_ANIMATION_MS,
    animationDurationUpdate: CHART_ANIMATION_MS,
    animationEasing: 'cubicOut',
    animationEasingUpdate: 'cubicOut'
  }
}

function initChart() {
  if (!chartRef.value || props.loading || isEmpty.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
    needsFullReplace = true
  }
  chartInstance.setOption(withAnimationDefaults(props.option), {
    notMerge: needsFullReplace,
    lazyUpdate: false
  })
  needsFullReplace = false
}

function clearChart() {
  chartInstance?.clear()
  needsFullReplace = true
}

function handleResize() {
  chartInstance?.resize()
}

function handleMotionPreferenceChange() {
  refreshChart()
}

async function refreshChart() {
  await nextTick()
  if (props.loading || isEmpty.value) {
    clearChart()
    return
  }
  initChart()
}

const isEmpty = computed(() => !props.option || Object.keys(props.option).length === 0)

watch(() => props.option, refreshChart, { deep: true })
watch(() => props.loading, refreshChart)

onMounted(() => {
  if (typeof window !== 'undefined') {
    motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    motionQuery.addEventListener('change', handleMotionPreferenceChange)
  }
  initChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  motionQuery?.removeEventListener('change', handleMotionPreferenceChange)
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
  opacity: 1;
  transition: opacity var(--transition-chart);
}
.chart-canvas--hidden {
  opacity: 0;
  pointer-events: none;
}
.chart-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    linear-gradient(180deg, rgba(248, 250, 252, 0.95), rgba(255, 255, 255, 0.95));
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: 13px;
  z-index: 1;
}
</style>
