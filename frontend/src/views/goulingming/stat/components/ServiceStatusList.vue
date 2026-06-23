<template>
  <section class="svc-list">
    <div class="svc-list__header">
      <h3 class="svc-list__title">服务节点状态</h3>
      <span v-if="lastUpdated" class="svc-list__stamp">更新于 {{ lastUpdated }}</span>
    </div>

    <!-- 骨架屏加载态 -->
    <div v-if="loading" class="svc-list__grid">
      <div v-for="i in 6" :key="i" class="svc-card svc-card--skeleton" aria-hidden="true">
        <div class="sk sk--header" />
        <div class="sk sk--metric" />
        <div class="sk sk--metric" style="width: 68%" />
      </div>
    </div>

    <EmptyState
      v-else-if="!items.length"
      title="暂无服务数据"
      description="暂无在线服务节点"
    />

    <div v-else class="svc-list__grid">
      <article
        v-for="item in items"
        :key="item.name"
        class="svc-card"
        :class="`svc-card--${resolveStatus(item.status)}`"
      >
        <div class="svc-card__header">
          <span class="svc-card__dot" :class="`dot--${resolveStatus(item.status)}`" />
          <span class="svc-card__name">{{ item.name }}</span>
        </div>
        <div class="svc-card__metrics">
          <span>QPS: <em class="tabular-nums">{{ item.qps ?? '-' }}</em></span>
          <span>错误率: <em class="tabular-nums">{{ item.error_rate != null ? `${(item.error_rate * 100).toFixed(2)}%` : '-' }}</em></span>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import EmptyState from '../../../../components/common/EmptyState.vue'

defineProps({
  items: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  lastUpdated: {
    type: String,
    default: ''
  }
})

function resolveStatus(status) {
  const s = String(status).toLowerCase()
  if (s === 'healthy' || s === 'up') return 'healthy'
  if (s === 'degraded' || s === 'warning') return 'warning'
  if (s === 'down' || s === 'error') return 'error'
  return 'unknown'
}
</script>

<style scoped>
.svc-list {
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
}

.svc-list__title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.svc-list__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.svc-list__stamp {
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: var(--font-mono);
}

.svc-list__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--spacing-sm);
}

.svc-card {
  padding: var(--spacing-sm);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.svc-card:hover {
  border-color: rgba(37, 99, 235, 0.3);
  box-shadow: var(--shadow-card-hover);
}

.svc-card__header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.svc-card__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot--healthy { background: var(--color-success); }
.dot--warning { background: var(--color-warning); }
.dot--error { background: var(--color-danger); }
.dot--unknown { background: var(--color-text-muted); }

.svc-card__name {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.svc-card__metrics {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 11px;
  color: var(--color-text-muted);
}

.svc-card__metrics em {
  font-style: normal;
  color: var(--color-text-secondary);
}

/* Skeleton state */
.svc-card--skeleton {
  pointer-events: none;
}

.sk {
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--color-bg) 25%, #e5e7eb 50%, var(--color-bg) 75%);
  background-size: 200% 100%;
  animation: sk-shimmer 1.4s ease-in-out infinite;
}

.sk--header { width: 60%; height: 14px; margin-bottom: 8px; }
.sk--metric { width: 80%; height: 11px; margin-bottom: 4px; }

@keyframes sk-shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .sk { animation: none; background: var(--color-bg); }
}
</style>
