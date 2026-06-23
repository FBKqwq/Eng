<template>
  <div class="dashboard-page">
    <div class="dashboard-page__hero">
      <ParticleBackdrop variant="dashboard" :intensity="0.55" />
      <div class="dashboard-page__hero-content">
        <HealthOverview />
      </div>
    </div>
    <TrafficErrorPanel />
    <LatencyPanel />
    <section class="dashboard-page__digest page-grid page-grid-2" aria-label="预警与体检摘要">
      <AlertDigest />
      <LatestReportCard />
    </section>
  </div>
</template>

<script setup>
import ParticleBackdrop from '../../components/common/ParticleBackdrop.vue'
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

.dashboard-page__hero {
  position: relative;
  min-height: 300px;
  border-radius: var(--radius-md);
  overflow: hidden;
}

.dashboard-page__hero-content {
  position: relative;
  z-index: 1;
}

.dashboard-page__digest {
  margin: 0;
}

.dashboard-page__digest > :deep(.page-section) {
  margin-bottom: 0;
  height: 100%;
}
</style>
