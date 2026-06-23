<template>
  <div class="chart-band">
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
    />
  </div>
</template>

<script setup>
import EmptyState from '../common/EmptyState.vue'
import ChartBandItem from './ChartBandItem.vue'

defineProps({
  chartTemplates: { type: Array, default: () => [] },
  logType: { type: String, default: '' }
})
</script>

<style scoped>
.chart-band {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-md);
}
</style>
