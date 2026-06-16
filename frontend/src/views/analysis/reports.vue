<template>
  <div class="reports-page page-grid page-grid-2">
    <ReportTimeline />
    <div>
      <ReportRiskPanel />
      <section class="page-section" style="margin-top: 16px;">
        <ReportSections />
        <RelationInsightCard />
        <StageRing />
      </section>
    </div>
  </div>
</template>

<script setup>
import ReportTimeline from '../../components/analysis-reports/ReportTimeline.vue'
import ReportRiskPanel from '../../components/analysis-reports/ReportRiskPanel.vue'
import ReportSections from '../../components/analysis-reports/ReportSections.vue'
import RelationInsightCard from '../../components/analysis-reports/RelationInsightCard.vue'
import StageRing from '../../components/common/StageRing.vue'
</script>
