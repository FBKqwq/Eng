<template>
  <div class="pipeline-page">
    <PipelineGraph />
    <section class="page-section" style="margin-top: 16px;">
      <VerifyOutputPanel />
    </section>
  </div>
</template>

<script setup>
import PipelineGraph from '../../components/system/PipelineGraph.vue'
import VerifyOutputPanel from '../../components/system/VerifyOutputPanel.vue'
</script>
