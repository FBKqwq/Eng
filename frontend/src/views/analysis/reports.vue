<template>
  <div class="reports-page page-grid page-grid-2">
    <ReportTimeline />
    <div class="reports-page__detail">
      <section class="page-section">
        <h2>风险定级</h2>
        <ReportRiskPanel />
      </section>
      <section class="page-section">
        <h2>报告拆解</h2>
        <ReportSections />
        <RelationInsightCard />
      </section>
      <section class="page-section">
        <h2>生成质量</h2>
        <StageRing :stages="reportStages" />
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

const reportStages = [
  { name: '聚合', status: 'pending' },
  { name: '采样', status: 'pending' },
  { name: '压缩', status: 'pending' },
  { name: '分析', status: 'pending' },
  { name: '成文', status: 'pending' }
]
</script>

<style scoped>
.reports-page__detail {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.reports-page__detail .page-section {
  margin-bottom: 0;
}
</style>
