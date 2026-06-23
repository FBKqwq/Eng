<template>
  <div class="topology-block">
    <div class="topology-graph">
      <div class="topology-nodes">
        <span v-for="node in nodes" :key="node" class="topology-node" :class="{ abnormal: node === 'order-svc' }">
          {{ node }}
        </span>
      </div>
      <p class="topology-note">affected_services 简化拓扑，异常服务红色脉冲（F5 阶段）</p>
    </div>
    <div class="similar-errors">
      <p class="similar-errors__label">同类错误频次</p>
      <BarChart
        horizontal
        height="120px"
        placeholder="get_similar_errors 迷你柱状图占位"
      />
    </div>
  </div>
</template>

<script setup>
import BarChart from '../common/charts/BarChart.vue'

const nodes = ['gateway', 'order-svc', 'payment-svc', 'inventory-svc']
</script>

<style scoped>
.topology-block {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.topology-graph {
  padding: var(--spacing-md);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.topology-nodes {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}

.topology-node {
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  font-size: 12px;
  color: var(--color-text-secondary);
}

.topology-node.abnormal {
  border-color: var(--color-danger);
  color: var(--color-danger);
  background: var(--color-danger-bg);
  animation: pulse-abnormal 2s ease-in-out infinite;
}

.topology-note {
  margin: var(--spacing-sm) 0 0;
  font-size: 11px;
  color: var(--color-text-muted);
  text-align: center;
}

.similar-errors__label {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

@keyframes pulse-abnormal {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

@media (prefers-reduced-motion: reduce) {
  .topology-node.abnormal {
    animation: none;
  }
}
</style>
