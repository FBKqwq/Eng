<template>
  <section class="timeline-panel page-section">
    <h2>报告时间轴</h2>
    <TimeAxis description="按时间倒序的报告列表，含 risk_level 色点与报告类型（F6 阶段接入 GET /reports/recent）" />
  </section>
</template>

<script setup>
import TimeAxis from '../common/TimeAxis.vue'
</script>

<style scoped>
.timeline-panel {
  margin-bottom: 0;
}
</style>
