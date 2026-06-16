<template>
  <EmptyState title="链路瀑布图占位" description="跨服务泳道瀑布图，ERROR 块红色，点击展开原始字段" pending-api="GET /api/v1/logs/trace/{trace_id}" />
</template>

<script setup>
import EmptyState from '../common/EmptyState.vue'
</script>
