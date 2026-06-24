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
  padding: var(--industrial-panel-padding);
  border: var(--industrial-border-width) solid var(--industrial-border-color);
  border-radius: 0;
  background: var(--industrial-white);
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
  width: 1px;
  background: var(--industrial-border-color);
}

.timeline-item:last-child .axis-line {
  display: none;
}

.dot {
  position: relative;
  z-index: 1;
  width: 12px;
  height: 12px;
  margin-top: 2px;
  border-radius: 50%;
  background: var(--industrial-medium-gray);
  border: 2px solid var(--industrial-white);
  box-shadow: 0 0 0 1px var(--industrial-border-color);
}

.dot.tone-danger {
  background: var(--industrial-red);
  box-shadow: var(--industrial-status-glow-red);
}

.dot.tone-warning {
  background: var(--industrial-orange);
  box-shadow: var(--industrial-status-glow-orange);
}

.dot.tone-info {
  background: var(--industrial-blue-cyan);
  box-shadow: var(--industrial-status-glow-blue);
}

.content {
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid var(--industrial-border-color);
  border-radius: 0;
  background: var(--industrial-white);
  position: relative;
  clip-path: polygon(
    0 0,
    calc(100% - var(--industrial-cut-size)) 0,
    100% var(--industrial-cut-size),
    100% 100%,
    0 100%
  );
  transition: border-color var(--transition-fast);
}

.content:hover {
  border-color: var(--industrial-blue-cyan);
}

.time {
  display: block;
  font-size: 12px;
  color: var(--industrial-medium-gray);
  font-family: var(--font-mono);
}

.label {
  margin: 2px 0 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--industrial-dark-gray);
  line-height: 1.4;
}

.detail {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--industrial-medium-gray);
  line-height: var(--industrial-line-height);
}

.placeholder-note {
  margin: var(--spacing-md) 0 0;
  padding-top: var(--spacing-sm);
  border-top: 1px dashed var(--industrial-border-color);
  font-size: 12px;
  color: var(--industrial-medium-gray);
  text-align: center;
}
</style>
