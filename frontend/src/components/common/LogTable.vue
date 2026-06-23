<template>
  <section class="log-table" aria-label="日志明细表">
    <header class="log-table-header">
      <h3>日志明细</h3>
      <span class="pending-tag">F2 阶段实现</span>
    </header>
    <EmptyState
      title="日志明细表占位"
      :description="description"
      pending-api="POST /api/v1/logs/search"
      compact
    />
  </section>
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
  margin-top: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  overflow: hidden;
}

.log-table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
}

.log-table-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.pending-tag {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
}
</style>
