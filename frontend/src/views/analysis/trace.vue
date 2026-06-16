<template>
  <div class="trace-page">
    <TraceSearchBar />
    <section class="page-section" style="margin-top: 16px;">
      <TraceWaterfall />
    </section>
  </div>
</template>

<script setup>
import TraceSearchBar from '../../components/analysis-trace/TraceSearchBar.vue'
import TraceWaterfall from '../../components/analysis-trace/TraceWaterfall.vue'
</script>
