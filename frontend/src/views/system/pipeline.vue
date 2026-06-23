<template>
  <div class="pipeline-page">
    <PipelineGraph />
    <VerifyOutputPanel />
  </div>
</template>

<script setup>
import PipelineGraph from '../../components/system/PipelineGraph.vue'
import VerifyOutputPanel from '../../components/system/VerifyOutputPanel.vue'
</script>

<style scoped>
.pipeline-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}
</style>
