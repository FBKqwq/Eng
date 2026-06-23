<template>
  <div class="dashboard-page">
    <HealthOverview />
    <TrafficErrorPanel />
    <LatencyPanel />
    <section class="page-grid page-grid-2">
      <AlertDigest />
      <LatestReportCard />
    </section>
  </div>
</template>

<script setup>
import HealthOverview from '../../components/dashboard/HealthOverview.vue'
import TrafficErrorPanel from '../../components/dashboard/TrafficErrorPanel.vue'
import LatencyPanel from '../../components/dashboard/LatencyPanel.vue'
import AlertDigest from '../../components/dashboard/AlertDigest.vue'
import LatestReportCard from '../../components/dashboard/LatestReportCard.vue'
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}
</style>
