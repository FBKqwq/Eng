<template>
  <div class="alerts-page">
    <section class="page-section">
      <h2>状态看板</h2>
      <AlertBoard />
    </section>
    <section class="page-section">
      <h2>预警列表</h2>
      <AlertTable />
    </section>
    <AlertDetailDrawer />
  </div>
</template>

<script setup>
import AlertBoard from '../../components/analysis-alerts/AlertBoard.vue'
import AlertTable from '../../components/analysis-alerts/AlertTable.vue'
import AlertDetailDrawer from '../../components/analysis-alerts/AlertDetailDrawer.vue'
</script>

<style scoped>
.alerts-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.alerts-page .page-section {
  margin-bottom: 0;
}
</style>
