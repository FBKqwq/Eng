<template>
  <div class="log-table">
    <EmptyState
      title="日志明细表占位"
      :description="description"
      pending-api="POST /api/v1/logs/search"
      compact
    />
  </div>
</template>

<script setup>
import EmptyState from './EmptyState.vue'

defineProps({
  description: {
    type: String,
    default: '支持分页、排序、行展开与 trace_id 跳转链路追踪（F2 阶段实现）'
  }
})
</script>

<style scoped>
.log-table {
  margin-top: 12px;
}
</style>
