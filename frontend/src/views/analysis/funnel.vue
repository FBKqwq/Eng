<template>
  <div class="funnel-page">
    <FunnelMain />
    <section class="page-section" style="margin-top: 16px;">
      <LossLocator />
    </section>
  </div>
</template>

<script setup>
import FunnelMain from '../../components/analysis-funnel/FunnelMain.vue'
import LossLocator from '../../components/analysis-funnel/LossLocator.vue'
</script>
