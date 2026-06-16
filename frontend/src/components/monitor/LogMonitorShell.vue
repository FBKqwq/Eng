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
    <section class="page-section">
      <h2>明细区</h2>
      <LogTable :description="`默认列：${defaultColumns.join('、')}`" />
    </section>
  </div>
</template>

<script setup>
import DynamicFilterBar from './DynamicFilterBar.vue'
import ChartBand from './ChartBand.vue'
import LogTable from '../common/LogTable.vue'

defineProps({
  logType: { type: String, required: true },
  chartTemplates: { type: Array, default: () => [] },
  defaultColumns: { type: Array, default: () => [] }
})
</script>
