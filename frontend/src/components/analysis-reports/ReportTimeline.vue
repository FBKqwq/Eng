<template>
  <section class="timeline-panel page-section" aria-label="报告时间轴" :aria-busy="loading">
    <header class="timeline-panel__header">
      <div class="timeline-panel__title-group">
        <h2>周期体检报告</h2>
        <span v-if="items.length" class="timeline-panel__count tabular-nums">共 {{ items.length }} 份</span>
      </div>
      <div class="timeline-panel__controls">
        <button
          type="button"
          class="timeline-panel__zoom-btn"
          :class="{ 'is-active': zoomLevel > 1 }"
          @click="zoomOut"
          title="缩小"
        >
          -
        </button>
        <span class="timeline-panel__zoom-label">{{ Math.round(zoomLevel * 100) }}%</span>
        <button
          type="button"
          class="timeline-panel__zoom-btn"
          :class="{ 'is-active': zoomLevel < 3 }"
          @click="zoomIn"
          title="放大"
        >
          +
        </button>
      </div>
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
      <div class="skeleton-track">
        <div v-for="n in 6" :key="n" class="skeleton-item" />
      </div>
    </div>

    <EmptyState
      v-else-if="!items.length"
      compact
      title="暂无报告"
      description="智能分析尚未产出周期或事件报告"
    />

    <div v-else class="timeline-container">
      <div class="timeline-view" ref="timelineViewRef" @scroll="handleScroll">
        <div class="timeline-track" :style="{ width: trackWidth + 'px' }">
          <div class="timeline-axis">
            <div
              v-for="(mark, index) in axisMarks"
              :key="index"
              class="axis-mark"
              :style="{ left: mark.position + '%' }"
            >
              <span class="axis-line" />
              <span class="axis-label">{{ mark.label }}</span>
            </div>
          </div>
          <div class="timeline-events">
            <div
              v-for="item in sortedItems"
              :key="item.report_id"
              class="timeline-event"
              :class="{ 'is-selected': item.report_id === selectedId }"
              :style="{ left: getEventPosition(item) + '%' }"
              role="button"
              tabindex="0"
              @click="selectItem(item)"
              @keydown.enter="selectItem(item)"
            >
              <div class="event-dot" :class="riskToneClass(item.risk_level)" />
              <div class="event-card">
                <time class="event-time tabular-nums">{{ formatTime(item.created_at) }}</time>
                <p class="event-title">{{ item.title || '未命名报告' }}</p>
                <span class="event-type">{{ formatReportType(item.report_type) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="timeline-controls">
        <div class="timeline-controls__zoom">
          <button
            type="button"
            class="timeline-controls__btn"
            :disabled="zoomLevel <= 1"
            @click="zoomOut"
            title="缩小"
          >
            -
          </button>
          <span class="timeline-controls__label">{{ Math.round(zoomLevel * 100) }}%</span>
          <button
            type="button"
            class="timeline-controls__btn"
            :disabled="zoomLevel >= 3"
            @click="zoomIn"
            title="放大"
          >
            +
          </button>
        </div>
        <div class="timeline-controls__nav">
          <button
            type="button"
            class="timeline-controls__btn"
            :disabled="!canScrollLeft"
            @click="scrollLeft"
            title="向左滚动"
          >
            ‹
          </button>
          <span class="timeline-controls__hint">{{ visibleRangeText }}</span>
          <button
            type="button"
            class="timeline-controls__btn"
            :disabled="!canScrollRight"
            @click="scrollRight"
            title="向右滚动"
          >
            ›
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>import { computed, ref, nextTick } from 'vue';
import EmptyState from '../common/EmptyState.vue';
import { formatTime } from '../../utils/format.js';
const props = defineProps({
 /** getRecentReports → data.items */
 items: { type: Array, default: () => [] },
 selectedId: { type: String, default: '' },
 loading: { type: Boolean, default: false },
 error: { type: String, default: '' }
});
const emit = defineEmits(['select', 'retry']);
const zoomLevel = ref(1);
const scrollPosition = ref(0);
const timelineViewRef = ref(null);

const REPORT_TYPE_LABELS = {
  periodic: '周期体检',
  event: '事件诊断'
}

const sortedItems = computed(() => {
  return [...props.items].sort((a, b) => {
    const ta = new Date(a?.created_at || 0).getTime()
    const tb = new Date(b?.created_at || 0).getTime()
    return ta - tb
  })
})

const timeRange = computed(() => {
  if (!sortedItems.value.length) return { min: 0, max: 100 }
  const times = sortedItems.value.map(item => new Date(item?.created_at || 0).getTime())
  return {
    min: Math.min(...times),
    max: Math.max(...times)
  }
})

const axisMarks = computed(() => {
  if (!sortedItems.value.length) return []
  const marks = []
  const { min, max } = timeRange.value
  const range = max - min || 3600000
  const step = range / 5
  for (let i = 0; i <= 5; i++) {
    const time = new Date(min + i * step)
    marks.push({
      position: (i * step / range) * 100,
      label: `${time.getHours().toString().padStart(2, '0')}:${time.getMinutes().toString().padStart(2, '0')}`
    })
  }
  return marks
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

function getEventPosition(item) {
  const { min, max } = timeRange.value
  const itemTime = new Date(item?.created_at || 0).getTime()
  const range = max - min || 1
  return ((itemTime - min) / range) * 100
}

function selectItem(item) {
  const id = item?.report_id
  if (id) emit('select', id)
}

const trackWidth = computed(() => {
  const baseWidth = 800
  return baseWidth * zoomLevel.value
})

const canScrollLeft = computed(() => scrollPosition.value > 0)

const canScrollRight = computed(() => {
  if (!timelineViewRef.value) return false
  const viewWidth = timelineViewRef.value.clientWidth
  return scrollPosition.value < trackWidth.value - viewWidth
})

const visibleRangeText = computed(() => {
  if (!sortedItems.value.length) return ''
  const { min, max } = timeRange.value
  const start = new Date(min)
  const end = new Date(max)
  return `${start.getHours().toString().padStart(2, '0')}:${start.getMinutes().toString().padStart(2, '0')} - ${end.getHours().toString().padStart(2, '0')}:${end.getMinutes().toString().padStart(2, '0')}`
})

function zoomIn() {
  if (zoomLevel.value < 3) {
    zoomLevel.value = Math.min(3, zoomLevel.value + 0.25)
    nextTick(() => {
      if (timelineViewRef.value) {
        timelineViewRef.value.scrollLeft = scrollPosition.value
      }
    })
  }
}

function zoomOut() {
  if (zoomLevel.value > 1) {
    zoomLevel.value = Math.max(1, zoomLevel.value - 0.25)
    nextTick(() => {
      if (timelineViewRef.value) {
        const maxScroll = trackWidth.value - timelineViewRef.value.clientWidth
        timelineViewRef.value.scrollLeft = Math.min(scrollPosition.value, maxScroll)
      }
    })
  }
}

function scrollLeft() {
  if (timelineViewRef.value) {
    const scrollAmount = timelineViewRef.value.clientWidth / 2
    timelineViewRef.value.scrollBy({ left: -scrollAmount, behavior: 'smooth' })
  }
}

function scrollRight() {
  if (timelineViewRef.value) {
    const scrollAmount = timelineViewRef.value.clientWidth / 2
    timelineViewRef.value.scrollBy({ left: scrollAmount, behavior: 'smooth' })
  }
}

function handleScroll() {
  if (timelineViewRef.value) {
    scrollPosition.value = timelineViewRef.value.scrollLeft
  }
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
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.timeline-panel__title-group {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-sm);
}

.timeline-panel__title-group h2 {
  margin: 0;
}

.timeline-panel__count {
  font-size: 12px;
  color: var(--color-text-muted);
}

.timeline-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.timeline-view {
  position: relative;
  overflow-x: auto;
  overflow-y: hidden;
  max-width: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
}

.timeline-track {
  position: relative;
  min-height: 140px;
  padding: var(--spacing-md) 0;
}

.timeline-axis {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 40px;
  padding-top: var(--spacing-sm);
  border-bottom: 2px solid var(--color-border);
}

.axis-mark {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  transform: translateX(-50%);
}

.axis-mark .axis-line {
  width: 2px;
  height: 8px;
  background: var(--color-border);
  margin-bottom: 4px;
}

.axis-label {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--color-text-muted);
  white-space: nowrap;
}

.timeline-events {
  position: relative;
  height: 100px;
  margin-top: 40px;
  padding: 0 var(--spacing-sm);
}

.timeline-event {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: opacity 120ms ease;
  z-index: 1;
}

.timeline-event:hover {
  z-index: 10;
}

.timeline-event:hover .event-card {
  opacity: 1;
  transform: translateY(0) scale(1);
}

.event-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 3px solid var(--color-bg);
  box-shadow: 0 0 0 2px var(--color-border);
  transition: transform 120ms ease, box-shadow 120ms ease;
}

.timeline-event:hover .event-dot,
.timeline-event.is-selected .event-dot {
  transform: scale(1.2);
}

.event-dot.tone-low {
  background: var(--color-success);
}

.event-dot.tone-medium {
  background: var(--color-warning);
}

.event-dot.tone-high {
  background: var(--color-danger);
}

.timeline-event.is-selected .event-dot {
  box-shadow: 0 0 0 3px var(--color-primary);
}

.event-card {
  position: absolute;
  top: 22px;
  left: 50%;
  transform: translateX(-50%) translateY(8px) scale(0.95);
  min-width: 160px;
  max-width: 220px;
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  box-shadow: var(--shadow-md);
  opacity: 0;
  visibility: hidden;
  transition: all 180ms ease;
}

.timeline-event:hover .event-card,
.timeline-event.is-selected .event-card {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(0) scale(1);
}

.timeline-event.is-selected .event-card {
  border-color: var(--color-primary);
  background: var(--color-info-bg);
}

.event-time {
  display: block;
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--color-text-muted);
  margin-bottom: 4px;
}

.event-title {
  margin: 0 0 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.event-type {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-xs);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  font-size: 10px;
  color: var(--color-text-secondary);
}

.timeline-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-xs) var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
}

.timeline-controls__zoom {
  display: flex;
  align-items: center;
  gap: 4px;
}

.timeline-controls__nav {
  display: flex;
  align-items: center;
  gap: 8px;
}

.timeline-controls__btn {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: var(--radius-xs);
  background: transparent;
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 120ms ease;
}

.timeline-controls__btn:hover:not(:disabled) {
  background: var(--color-border);
  color: var(--color-text);
}

.timeline-controls__btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.timeline-controls__label {
  min-width: 50px;
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--color-text-muted);
  text-align: center;
}

.timeline-controls__hint {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--color-text-muted);
  white-space: nowrap;
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
  padding-bottom: var(--spacing-sm);
}

.skeleton-track {
  display: flex;
  justify-content: space-between;
  height: 80px;
}

.skeleton-item {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-border);
  margin-top: var(--spacing-md);
}

@media (prefers-reduced-motion: reduce) {
  .timeline-event,
  .event-card {
    transition: none;
  }
}
</style>
