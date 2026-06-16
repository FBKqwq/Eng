<template>
  <div class="dashboard-page">
    <HealthOverview />
    <section class="page-section page-grid page-grid-2">
      <TrafficErrorPanel />
      <div class="page-grid">
        <BarChart />
        <PieChart />
      </div>
    </section>
    <LatencyPanel />
    <section class="page-section page-grid page-grid-2">
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
import BarChart from '../../components/common/charts/BarChart.vue'
import PieChart from '../../components/common/charts/PieChart.vue'
</script>
