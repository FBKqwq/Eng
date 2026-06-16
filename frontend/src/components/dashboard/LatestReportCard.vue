<template>
  <section class="page-section">
    <EmptyState title="最新体检结论" description="最近周期报告 risk_level + 一句话摘要，点击跳转报告页" pending-api="GET /api/v1/reports/recent" compact />
  </section>
</template>

<script setup>
import EmptyState from '../common/EmptyState.vue'
</script>
