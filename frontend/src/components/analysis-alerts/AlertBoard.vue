<template>
  <div class="alert-board">
    <div class="page-grid page-grid-3">
      <StatCard label="活跃" hint="active 预警计数" />
      <StatCard label="已确认" hint="acknowledged 计数" />
      <StatCard label="已解决" hint="resolved 计数" />
    </div>
    <p class="trend-note">24h 预警数量趋势迷你图占位（F6 阶段接入）</p>
    <p class="pending-tag">待接入：GET /api/v1/alerts/active</p>
  </div>
</template>

<script setup>
import StatCard from '../common/StatCard.vue'
</script>

<style scoped>
.alert-board {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.trend-note {
  margin: 0;
  padding: var(--spacing-sm);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--color-text-muted);
  text-align: center;
}

.pending-tag {
  margin: 0;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 12px;
  text-align: center;
  align-self: flex-start;
}
</style>
