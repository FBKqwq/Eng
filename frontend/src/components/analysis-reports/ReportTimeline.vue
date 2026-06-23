<template>
  <section class="timeline-panel page-section" aria-label="报告时间轴" :aria-busy="loading">
    <header class="timeline-panel__header">
      <h2>报告时间轴</h2>
      <span v-if="items.length" class="timeline-panel__count tabular-nums">共 {{ items.length }} 份</span>
    </header>

    <EmptyState
      v-if="error && !loading"
      compact
      title="报告列表加载失败"
      :description="error"
    >
      <button type="button" class="timeline-panel__retry" @click="emit('retry')">重试</button>
    </EmptyState>

    <div v-else-if="loading && !items.length" class="timeline-panel__skeleton" aria-hidden="true">
      <div v-for="n in 4" :key="n" class="skeleton-item" />
    </div>

    <EmptyState
      v-else-if="!items.length"
      compact
      title="暂无报告"
      description="智能分析尚未产出周期或事件报告"
    />

    <ul v-else class="timeline-list" role="list">
      <li
        v-for="item in sortedItems"
        :key="item.report_id"
        class="timeline-entry"
        :class="{ 'is-selected': item.report_id === selectedId }"
        role="button"
        tabindex="0"
        @click="selectItem(item)"
        @keydown.enter="selectItem(item)"
      >
        <span class="axis-line" aria-hidden="true" />
        <span class="risk-dot" :class="riskToneClass(item.risk_level)" aria-hidden="true" />
        <div class="entry-body">
          <div class="entry-meta">
            <time class="entry-time tabular-nums">{{ formatTime(item.created_at) }}</time>
            <span class="entry-type">{{ formatReportType(item.report_type) }}</span>
          </div>
          <p class="entry-title">{{ item.title || '未命名报告' }}</p>
          <p v-if="item.summary" class="entry-summary">{{ item.summary }}</p>
        </div>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import EmptyState from '../common/EmptyState.vue'
import { formatTime } from '../../utils/format.js'

const props = defineProps({
  /** getRecentReports → data.items */
  items: { type: Array, default: () => [] },
  selectedId: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' }
})

const emit = defineEmits(['select', 'retry'])

const REPORT_TYPE_LABELS = {
  periodic: '周期体检',
  event: '事件诊断'
}

const sortedItems = computed(() => {
  return [...props.items].sort((a, b) => {
    const ta = new Date(a?.created_at || 0).getTime()
    const tb = new Date(b?.created_at || 0).getTime()
    return tb - ta
  })
})

function formatReportType(type) {
  return REPORT_TYPE_LABELS[type] || type || '分析报告'
}

function riskToneClass(level) {
  const key = String(level || 'medium').toLowerCase()
  if (key === 'high') return 'tone-high'
  if (key === 'low') return 'tone-low'
  return 'tone-medium'
}

function selectItem(item) {
  const id = item?.report_id
  if (id) emit('select', id)
}
</script>

<style scoped>
.timeline-panel {
  margin-bottom: 0;
}

.timeline-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.timeline-panel__header h2 {
  margin: 0;
}

.timeline-panel__count {
  font-size: 12px;
  color: var(--color-text-muted);
}

.timeline-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.timeline-entry {
  position: relative;
  display: grid;
  grid-template-columns: 14px 1fr;
  column-gap: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  margin-bottom: var(--spacing-xs);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}

.timeline-entry:hover,
.timeline-entry:focus-visible {
  background: var(--color-surface);
  border-color: var(--color-border);
  outline: none;
}

.timeline-entry.is-selected {
  background: var(--color-info-bg);
  border-color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

.axis-line {
  position: absolute;
  left: calc(var(--spacing-md) + 6px);
  top: 28px;
  bottom: -4px;
  width: 2px;
  background: var(--color-border);
}

.timeline-entry:last-child .axis-line {
  display: none;
}

.risk-dot {
  position: relative;
  z-index: 1;
  width: 12px;
  height: 12px;
  margin-top: 6px;
  border-radius: 50%;
  border: 2px solid var(--color-bg);
  box-shadow: 0 0 0 1px var(--color-border);
}

.risk-dot.tone-low {
  background: var(--color-success);
}

.risk-dot.tone-medium {
  background: var(--color-warning);
}

.risk-dot.tone-high {
  background: var(--color-danger);
}

.entry-body {
  min-width: 0;
}

.entry-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
}

.entry-time {
  font-size: 12px;
  color: var(--color-text-muted);
}

.entry-type {
  flex-shrink: 0;
  padding: 1px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  font-size: 11px;
  color: var(--color-text-secondary);
}

.entry-title {
  margin: 4px 0 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.35;
}

.entry-summary {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.timeline-panel__retry {
  margin-top: var(--spacing-xs);
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-size: 13px;
  cursor: pointer;
}

.timeline-panel__skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.skeleton-item {
  height: 72px;
  border-radius: var(--radius-md);
  background: linear-gradient(
    90deg,
    var(--color-bg) 25%,
    var(--color-border) 50%,
    var(--color-bg) 75%
  );
  background-size: 200% 100%;
  animation: timeline-shimmer 1.2s ease-in-out infinite;
}

@keyframes timeline-shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .timeline-entry {
    transition: none;
  }

  .skeleton-item {
    animation: none;
    background: var(--color-bg);
  }
}
</style>
