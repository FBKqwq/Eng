<template>
  <div class="chart-band page-grid page-grid-3">
    <TrendChart v-for="tpl in chartTemplates" :key="tpl" :placeholder="`图表占位：${tpl} 聚合模板`" />
    <EmptyState v-if="!chartTemplates.length" title="图表带占位" pending-api="metrics 六类聚合接口" compact />
  </div>
</template>

<script setup>
import TrendChart from '../common/charts/TrendChart.vue'
import EmptyState from '../common/EmptyState.vue'

defineProps({
  chartTemplates: { type: Array, default: () => [] }
})
</script>
