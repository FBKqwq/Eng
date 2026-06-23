<template>
  <section class="page-section pipeline-graph" aria-label="日志链路健康">
    <header class="graph-header">
      <h2>链路健康</h2>
    </header>

    <div
      v-if="loading"
      class="graph-skeleton"
      aria-busy="true"
      aria-label="链路状态加载中"
    >
      <div v-for="n in 4" :key="n" class="skeleton-node">
        <div class="skeleton-line skeleton-line--title" />
        <div class="skeleton-line skeleton-line--badge" />
      </div>
    </div>

    <div v-else class="graph-track" role="list" aria-label="日志链路四节点">
      <template v-for="(node, index) in displayNodes" :key="node.key">
        <article
          class="graph-node"
          role="listitem"
          :class="[
            `tone-${toneOf(node.status)}`,
            { 'is-pulse': toneOf(node.status) === 'danger' }
          ]"
          :title="node.detail || undefined"
          :aria-label="`${node.label}：${statusLabel(node.status)}`"
        >
          <span class="node-dot" aria-hidden="true" />
          <h3 class="node-label">{{ node.label }}</h3>
          <span class="node-badge tabular-nums">{{ statusLabel(node.status) }}</span>
        </article>

        <div
          v-if="index < displayNodes.length - 1"
          class="graph-arrow"
          :class="`arrow-tone-${toneOf(displayNodes[index + 1].status)}`"
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

/** 与总体规划 §3.8 / getPipelineNodes 顺序一致 */
const PIPELINE_ORDER = ['producer', 'kafka', 'logstash', 'es']

const NODE_LABELS = {
  producer: '日志生产',
  kafka: 'Kafka',
  logstash: 'Logstash',
  es: 'Elasticsearch'
}

const FALLBACK_NODES = PIPELINE_ORDER.map((key) => ({
  key,
  label: NODE_LABELS[key],
  status: 'unknown',
  detail: '尚未获取系统状态'
}))

const props = defineProps({
  /** getPipelineNodes 输出：{ key, label, status, detail? } */
  nodes: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

const displayNodes = computed(() => {
  const source = props.nodes.length > 0 ? props.nodes : FALLBACK_NODES
  const byKey = Object.fromEntries(
    source.map((node, index) => [node.key || PIPELINE_ORDER[index], node])
  )

  return PIPELINE_ORDER.map((key) => {
    const node = byKey[key]
    return {
      key,
      label: node?.label || NODE_LABELS[key],
      status: node?.status || 'unknown',
      detail: node?.detail || ''
    }
  })
})

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
  return map[status] || '未知'
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
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.graph-track {
  display: flex;
  align-items: stretch;
  gap: 0;
  overflow-x: auto;
  padding-bottom: 4px;
}

.graph-node {
  position: relative;
  flex: 1;
  min-width: 140px;
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
  text-align: center;
  transition:
    border-color 0.3s ease,
    box-shadow 0.18s ease-out,
    transform 0.18s ease-out,
    background-color 0.3s ease;
}

.graph-node::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  background: var(--node-accent, var(--color-border));
  transition: background-color 0.3s ease;
}

.graph-node:hover {
  box-shadow: var(--shadow-card);
  transform: translateY(-1px);
}

.tone-success {
  --node-accent: var(--color-success);
}

.tone-warning {
  --node-accent: var(--color-warning);
}

.tone-danger {
  --node-accent: var(--color-danger);
}

.tone-neutral {
  --node-accent: var(--color-text-muted);
}

.node-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-bottom: 8px;
  background: var(--node-accent, var(--color-text-secondary));
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
}

.is-pulse .node-dot {
  animation: node-pulse 1.8s ease-in-out infinite;
}

@keyframes node-pulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.35);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(220, 38, 38, 0);
  }
}

.node-label {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.3;
}

.node-badge {
  display: inline-block;
  margin-top: 8px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.2;
}

.tone-success .node-badge {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.tone-warning .node-badge {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.tone-danger .node-badge {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.tone-neutral .node-badge {
  background: var(--color-bg);
  color: var(--color-text-secondary);
}

.graph-arrow {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  width: 36px;
  color: var(--color-text-muted);
  opacity: 0.7;
  transition: color 0.3s ease, opacity 0.3s ease;
}

.arrow-tone-success {
  color: var(--color-success);
  opacity: 0.85;
}

.arrow-tone-warning {
  color: var(--color-warning);
  opacity: 0.85;
}

.arrow-tone-danger {
  color: var(--color-danger);
  opacity: 0.85;
}

.arrow-line {
  flex: 1;
  height: 2px;
  background: currentColor;
  transition: background-color 0.3s ease;
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
  display: grid;
  gap: 10px;
  min-height: 100px;
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
}

.skeleton-line {
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--color-bg) 25%, #e5e7eb 50%, var(--color-bg) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.2s ease-in-out infinite;
}

.skeleton-line--title {
  width: 60%;
  height: 16px;
  justify-self: center;
}

.skeleton-line--badge {
  width: 48px;
  height: 22px;
  justify-self: center;
}

@keyframes skeleton-shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

@media (max-width: 768px) {
  .graph-track {
    flex-direction: column;
    align-items: stretch;
  }

  .graph-arrow {
    width: auto;
    height: 28px;
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
  .graph-node,
  .graph-arrow,
  .node-dot {
    transition: none;
  }

  .graph-node:hover {
    transform: none;
  }

  .is-pulse .node-dot {
    animation: none;
  }

  .skeleton-line {
    animation: none;
    background: var(--color-bg);
  }
}
</style>
