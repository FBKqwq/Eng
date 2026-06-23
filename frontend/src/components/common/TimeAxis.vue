<template>
  <div class="time-axis" :class="{ 'is-placeholder': isPlaceholder }">
    <ul class="timeline" role="list">
      <li
        v-for="(item, index) in displayItems"
        :key="index"
        class="timeline-item"
      >
        <span class="axis-line" aria-hidden="true" />
        <span class="dot" :class="item.tone ? `tone-${item.tone}` : ''" aria-hidden="true" />
        <div class="content">
          <time v-if="item.time" class="time tabular-nums">{{ item.time }}</time>
          <p class="label">{{ item.label }}</p>
          <p v-if="item.detail" class="detail">{{ item.detail }}</p>
        </div>
      </li>
    </ul>
    <p v-if="isPlaceholder" class="placeholder-note">{{ description }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** 时间轴节点：{ time, label, detail?, tone? } */
  items: { type: Array, default: () => [] },
  description: {
    type: String,
    default: '用于证据链、报告时间轴等场景（F5/F6 阶段接入真实数据）'
  }
})

const PLACEHOLDER_ITEMS = [
  { time: '—', label: '时间点占位', detail: '等待后端时间戳字段' },
  { time: '—', label: '证据节点占位', detail: 'evidence_logs / 上下文日志' },
  { time: '—', label: '关联事件占位', detail: 'ERROR 节点将高亮显示' }
]

const isPlaceholder = computed(() => props.items.length === 0)

const displayItems = computed(() =>
  isPlaceholder.value ? PLACEHOLDER_ITEMS : props.items
)
</script>

<style scoped>
.time-axis {
  padding: var(--spacing-md);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.time-axis.is-placeholder .timeline-item {
  opacity: 0.72;
}

.timeline {
  list-style: none;
  margin: 0;
  padding: 0;
}

.timeline-item {
  position: relative;
  display: grid;
  grid-template-columns: 16px 1fr;
  column-gap: var(--spacing-md);
  padding-bottom: var(--spacing-md);
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.axis-line {
  position: absolute;
  left: 7px;
  top: 14px;
  bottom: 0;
  width: 2px;
  background: var(--color-border);
}

.timeline-item:last-child .axis-line {
  display: none;
}

.dot {
  position: relative;
  z-index: 1;
  width: 14px;
  height: 14px;
  margin-top: 2px;
  border-radius: 50%;
  background: var(--color-primary);
  border: 2px solid var(--color-surface);
  box-shadow: 0 0 0 1px var(--color-border);
}

.dot.tone-danger {
  background: var(--color-danger);
}

.dot.tone-warning {
  background: var(--color-warning);
}

.content {
  min-width: 0;
}

.time {
  display: block;
  font-size: 12px;
  color: var(--color-text-muted);
}

.label {
  margin: 2px 0 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
}

.detail {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.placeholder-note {
  margin: var(--spacing-md) 0 0;
  padding-top: var(--spacing-sm);
  border-top: 1px dashed var(--color-border);
  font-size: 12px;
  color: var(--color-text-muted);
  text-align: center;
}
</style>
