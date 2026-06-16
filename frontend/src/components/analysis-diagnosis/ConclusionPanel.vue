<template>
  <div class="page-grid page-grid-2">
    <GaugeChart placeholder="严重度仪表占位" />
    <GaugeChart placeholder="置信度仪表占位" />
    <EmptyState title="根因结论卡" description="结论一句话 + 推理依据要点列表（版式化渲染，非对话框）" class="span-2" />
  </div>
</template>

<script setup>
import GaugeChart from '../common/charts/GaugeChart.vue'
import EmptyState from '../common/EmptyState.vue'
</script>

<style scoped>
.span-2 { grid-column: span 2; }
</style>
