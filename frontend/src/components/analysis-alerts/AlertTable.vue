<template>
  <EmptyState title="预警列表占位" description="类型/severity/服务/时间/evidence_count 表格，active 行支持确认" pending-api="GET /api/v1/alerts/active" />
</template>

<script setup>
import EmptyState from '../common/EmptyState.vue'
</script>
