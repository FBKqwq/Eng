<template>
  <div class="log-monitor-shell">
    <section class="page-section">
      <h2>筛选区</h2>
      <DynamicFilterBar :log-type="logType" />
    </section>
    <section class="page-section">
      <h2>图表带</h2>
      <ChartBand :chart-templates="chartTemplates" />
    </section>
    <section class="page-section log-monitor-shell__detail">
      <h2>明细区</h2>
      <LogTable :description="tableDescription" />
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import DynamicFilterBar from './DynamicFilterBar.vue'
import ChartBand from './ChartBand.vue'
import LogTable from '../common/LogTable.vue'

const props = defineProps({
  logType: { type: String, required: true },
  chartTemplates: { type: Array, default: () => [] },
  defaultColumns: { type: Array, default: () => [] }
})

const tableDescription = computed(() => {
  if (!props.defaultColumns.length) {
    return '默认列待配置（F2 阶段接入 logs/search）'
  }
  return `默认列：${props.defaultColumns.join('、')}`
})
</script>

<style scoped>
.log-monitor-shell {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.log-monitor-shell__detail {
  margin-bottom: 0;
}
</style>
