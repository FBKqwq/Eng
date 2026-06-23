<template>
  <div class="chart-band" :class="{ 'chart-band--single': chartTemplates.length === 1 }">
    <EmptyState
      v-if="!chartTemplates.length"
      title="暂无图表配置"
      description="本日志类型暂未配置聚合图表模板"
      compact
    />
    <ChartBandItem
      v-for="tpl in chartTemplates"
      :key="tpl.id"
      :config="tpl"
      :log-type="logType"
      :class="{ 'chart-band__primary': isPrimary(tpl) }"
    />
  </div>
</template>

<script setup>
import EmptyState from '../common/EmptyState.vue'
import ChartBandItem from './ChartBandItem.vue'

const props = defineProps({
  chartTemplates: { type: Array, default: () => [] },
  logType: { type: String, default: '' },
  primaryChartId: { type: String, default: '' }
})

function isPrimary(tpl) {
  if (tpl.primary) return true
  if (props.primaryChartId && tpl.id === props.primaryChartId) return true
  return tpl.chartType === 'trend'
}
</script>

<style scoped>
.chart-band {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-md);
}

.chart-band--single {
  grid-template-columns: 1fr;
}

.chart-band__primary {
  grid-column: 1 / -1;
}

@media (max-width: 900px) {
  .chart-band {
    grid-template-columns: 1fr;
  }

  .chart-band__primary {
    grid-column: auto;
  }
}
</style>
