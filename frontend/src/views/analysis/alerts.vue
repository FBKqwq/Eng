<template>
  <div class="alerts-page">
    <AlertBoard />
    <section class="page-section" style="margin-top: 16px;">
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
