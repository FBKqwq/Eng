<template>
  <DashboardFrame title="平台健康总览" subtitle="PLATFORM HEALTH">
    <div class="health-panel">
      <div class="health-panel__gauge">
        <BaseChart :option="gaugeOption" :loading="loading" height="130px" />
        <strong>{{ healthLabel }}</strong>
      </div>
      <div class="health-panel__metrics">
        <article v-for="metric in metrics" :key="metric.label">
          <span>{{ metric.label }}</span>
          <strong class="tabular-nums">{{ metric.value }}</strong>
          <small>{{ metric.hint }}</small>
        </article>
      </div>
    </div>
  </DashboardFrame>
</template>

<script setup>
import { computed } from 'vue'
import DashboardFrame from './DashboardFrame.vue'
import BaseChart from '../common/charts/BaseChart.vue'
import { formatDuration, formatNumber, formatPercent } from '../../utils/format.js'

const props = defineProps({
  healthScore: { type: Number, default: 0 },
  totalLogs: { type: Number, default: 0 },
  errorRate: { type: Number, default: 0 },
  averageLatency: { type: Number, default: null },
  p95Latency: { type: Number, default: null },
  alertTotal: { type: Number, default: 0 },
  loading: { type: Boolean, default: false }
})

const healthLabel = computed(() =>
  props.healthScore >= 85 ? '良好' : props.healthScore >= 65 ? '需关注' : '高风险'
)

const gaugeColor = computed(() =>
  props.healthScore >= 85 ? '#007aff' : props.healthScore >= 65 ? '#ff9f0a' : '#ff453a'
)

const metrics = computed(() => [
  { label: '日志总量', value: formatNumber(props.totalLogs), hint: '当前时间窗口' },
  { label: '错误率', value: formatPercent(props.errorRate), hint: '错误日志 / 总量' },
  { label: '平均响应', value: formatDuration(props.averageLatency), hint: 'P50 近似' },
  { label: 'P95 响应', value: formatDuration(props.p95Latency), hint: '全局耗时分位' },
  { label: '活跃预警数', value: formatNumber(props.alertTotal), hint: '待处理事件' }
])

const gaugeOption = computed(() => ({
  series: [{
    type: 'gauge',
    startAngle: 205,
    endAngle: -25,
    min: 0,
    max: 100,
    center: ['50%', '52%'],
    radius: '94%',
    axisLine: {
      lineStyle: {
        width: 12,
        color: [[1, '#e8edf3']]
      }
    },
    progress: {
      show: true,
      width: 12,
      roundCap: true,
      itemStyle: {
        color: gaugeColor.value,
        shadowBlur: 12,
        shadowColor: `${gaugeColor.value}55`
      }
    },
    axisTick: { show: false },
    splitLine: { show: false },
    axisLabel: { show: false },
    pointer: { show: false },
    anchor: { show: false },
    title: { offsetCenter: [0, '23%'], color: '#7b8798', fontSize: 10 },
    detail: {
      valueAnimation: true,
      offsetCenter: [0, '55%'],
      formatter: '{value}',
      color: '#172033',
      fontSize: 30,
      fontWeight: 750
    },
    data: [{ value: props.healthScore, name: '健康分' }]
  }]
}))
</script>

<style scoped>
.health-panel {
  display: grid;
  grid-template-columns: 150px minmax(0, 1fr);
  gap: 8px;
  height: 136px;
}
.health-panel__gauge {
  position: relative;
  min-width: 0;
}
.health-panel__gauge > strong {
  position: absolute;
  right: 0;
  bottom: 3px;
  left: 0;
  color: v-bind(gaugeColor);
  font-size: 12px;
  text-align: center;
}
.health-panel__metrics {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.42);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}
.health-panel__metrics article {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
  padding: 8px 9px;
  border-left: 1px solid rgba(148, 163, 184, 0.16);
}
.health-panel__metrics article:first-child { border-left: 0; }
.health-panel__metrics span {
  color: #52677b;
  font-size: 10px;
  white-space: nowrap;
}
.health-panel__metrics strong {
  margin-top: 5px;
  color: #102a43;
  font-size: 19px;
  line-height: 1;
  white-space: nowrap;
}
.health-panel__metrics small {
  margin-top: 7px;
  color: #8292a3;
  font-size: 8px;
  white-space: nowrap;
}
</style>
