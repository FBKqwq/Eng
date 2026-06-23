<template>
  <section class="page-section pipeline-graph">
    <header class="graph-header">
      <h2>链路健康</h2>
      <span class="pending-tag">待接入：GET /system/status</span>
    </header>

    <div v-if="loading" class="graph-skeleton">
      <div v-for="n in 4" :key="n" class="skeleton-node" />
    </div>

    <div v-else class="graph-track" role="list" aria-label="日志链路四节点">
      <template v-for="(node, index) in displayNodes" :key="node.key">
        <div
          class="graph-node"
          role="listitem"
          :class="`tone-${toneOf(node.status)}`"
          :title="node.detail"
        >
          <span class="node-dot" aria-hidden="true" />
          <h3>{{ node.label }}</h3>
          <p class="node-status">{{ statusLabel(node.status) }}</p>
          <p v-if="node.detail" class="node-detail">{{ node.detail }}</p>
        </div>
        <div
          v-if="index < displayNodes.length - 1"
          class="graph-arrow"
          aria-hidden="true"
        >
          <span class="arrow-line" />
          <span class="arrow-head">›</span>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const PLACEHOLDER_NODES = [
  { key: 'producer', label: '日志生产', status: 'unknown', detail: 'F3 阶段接入容器/服务状态' },
  { key: 'kafka', label: 'Kafka', status: 'unknown', detail: 'F3 阶段接入容器/服务状态' },
  { key: 'logstash', label: 'Logstash', status: 'unknown', detail: 'F3 阶段接入容器/服务状态' },
  { key: 'es', label: 'Elasticsearch', status: 'unknown', detail: 'F3 阶段接入集群健康' }
]

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

const displayNodes = computed(() =>
  props.nodes.length > 0 ? props.nodes : PLACEHOLDER_NODES
)

function toneOf(status) {
  const map = {
    healthy: 'success',
    degraded: 'warning',
    down: 'danger',
    unknown: 'neutral',
    offline: 'neutral'
  }
  return map[status] || 'neutral'
}

function statusLabel(status) {
  const map = {
    healthy: '正常',
    degraded: '降级',
    down: '异常',
    unknown: '未知',
    offline: '离线'
  }
  return map[status] || '占位'
}
</script>

<style scoped>
.pipeline-graph {
  margin-bottom: 0;
}

.graph-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.graph-header h2 {
  margin: 0;
}

.pending-tag {
  flex-shrink: 0;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 12px;
  font-weight: 500;
}

.graph-track {
  display: flex;
  align-items: stretch;
  gap: 0;
  overflow-x: auto;
  padding-bottom: 4px;
}

.graph-node {
  flex: 1;
  min-width: 140px;
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  text-align: center;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.graph-node:hover {
  box-shadow: var(--shadow-sm);
}

.node-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-bottom: 8px;
  background: var(--color-text-secondary);
  transition: background-color 0.3s ease;
}

.tone-success .node-dot { background: var(--color-success); }
.tone-warning .node-dot { background: var(--color-warning); }
.tone-danger .node-dot { background: var(--color-danger); }
.tone-neutral .node-dot { background: var(--color-text-secondary); }

.graph-node h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.node-status {
  margin: 6px 0 0;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.tone-success .node-status { color: var(--color-success); }
.tone-warning .node-status { color: var(--color-warning); }
.tone-danger .node-status { color: var(--color-danger); }

.node-detail {
  margin: 6px 0 0;
  font-size: 11px;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.graph-arrow {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  width: 32px;
  color: var(--color-text-secondary);
  opacity: 0.6;
}

.arrow-line {
  flex: 1;
  height: 2px;
  background: var(--color-border);
}

.arrow-head {
  font-size: 18px;
  line-height: 1;
  margin-left: -2px;
}

.graph-skeleton {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
}

.skeleton-node {
  height: 100px;
  border-radius: var(--radius-md);
  background: linear-gradient(90deg, var(--color-bg) 25%, var(--color-border) 50%, var(--color-bg) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (max-width: 768px) {
  .graph-track {
    flex-direction: column;
    align-items: stretch;
  }

  .graph-arrow {
    width: auto;
    height: 24px;
    flex-direction: column;
    justify-content: center;
  }

  .arrow-line {
    width: 2px;
    height: 16px;
    flex: none;
  }

  .arrow-head {
    transform: rotate(90deg);
    margin: -4px 0 0;
  }

  .graph-skeleton {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton-node {
    animation: none;
    background: var(--color-bg);
  }

  .graph-node {
    transition: none;
  }
}
</style>
