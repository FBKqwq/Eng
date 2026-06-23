<template>
  <div class="funnel-page">
    <section class="page-section">
      <h2>主漏斗</h2>
      <FunnelMain />
    </section>
    <section class="page-section">
      <h2>流失定位</h2>
      <LossLocator />
    </section>
  </div>
</template>

<script setup>
import FunnelMain from '../../components/analysis-funnel/FunnelMain.vue'
import LossLocator from '../../components/analysis-funnel/LossLocator.vue'
</script>

<style scoped>
.funnel-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.funnel-page .page-section {
  margin-bottom: 0;
}
</style>
