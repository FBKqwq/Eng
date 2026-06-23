<template>
  <div class="trace-search">
    <div class="search-row">
      <input
        class="trace-input"
        type="text"
        placeholder="输入 trace_id（支持从监控/诊断页带参跳入）"
        disabled
      />
      <button type="button" class="search-btn" disabled>检索</button>
    </div>
    <div class="history-row">
      <span class="history-label">最近查询：</span>
      <span v-for="id in recentIds" :key="id" class="history-tag">{{ id }}</span>
    </div>
    <p class="pending-tag">待接入：POST /api/v1/logs/search（trace_id 筛选，F5 阶段）</p>
  </div>
</template>

<script setup>
const recentIds = ['trace-占位-001', 'trace-占位-002']
</script>

<style scoped>
.search-row {
  display: flex;
  gap: 8px;
}

.trace-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  font-size: 13px;
  color: var(--color-text-muted);
}

.search-btn {
  padding: 8px 20px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: #fff;
  font-size: 13px;
  opacity: 0.45;
  cursor: not-allowed;
}

.history-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: var(--spacing-sm);
}

.history-label {
  font-size: 12px;
  color: var(--color-text-muted);
}

.history-tag {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  font-size: 11px;
  color: var(--color-text-secondary);
  font-family: monospace;
}

.pending-tag {
  margin: var(--spacing-sm) 0 0;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 12px;
  display: inline-block;
}
</style>
