<template>
  <div class="trace-waterfall">
    <div class="summary-bar">
      <div class="summary-item">
        <span class="summary-label">总耗时</span>
        <span class="summary-value tabular-nums">—</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">经过服务</span>
        <span class="summary-value tabular-nums">—</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">断点位置</span>
        <span class="summary-value summary-value--danger">—</span>
      </div>
    </div>
    <EmptyState
      title="链路瀑布图占位"
      description="跨服务泳道瀑布图，ERROR 块红色，点击展开原始字段"
      pending-api="logs/search + trace_id"
    />
  </div>
</template>

<script setup>
import EmptyState from '../common/EmptyState.vue'
</script>

<style scoped>
.summary-bar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.summary-label {
  font-size: 11px;
  color: var(--color-text-muted);
}

.summary-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.summary-value--danger {
  color: var(--color-danger);
}
</style>
