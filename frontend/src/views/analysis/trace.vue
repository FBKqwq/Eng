<template>
  <div class="trace-page">
    <section class="page-section">
      <h2>检索区</h2>
      <TraceSearchBar />
    </section>
    <section class="page-section">
      <h2>链路瀑布</h2>
      <TraceWaterfall />
    </section>
  </div>
</template>

<script setup>
import TraceSearchBar from '../../components/analysis-trace/TraceSearchBar.vue'
import TraceWaterfall from '../../components/analysis-trace/TraceWaterfall.vue'
</script>

<style scoped>
.trace-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.trace-page .page-section {
  margin-bottom: 0;
}
</style>
