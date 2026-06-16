<template>
  <section class="page-section">
    <EmptyState title="活跃预警摘要" description="最近 5 条 active 预警紧凑列表，点击跳转预警中心" pending-api="GET /api/v1/alerts/active" compact />
  </section>
</template>

<script setup>
import EmptyState from '../common/EmptyState.vue'
</script>
