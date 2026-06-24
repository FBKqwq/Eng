<template>
  <section class="horizontal-timeline">
    <header class="horizontal-timeline__header">
      <div>
        <h3>{{ title }}</h3>
        <p>{{ rangeLabel }}</p>
      </div>
      <div class="horizontal-timeline__zoom" role="group" aria-label="时间窗口缩放">
        <button
          v-for="option in zoomOptions"
          :key="option.value"
          type="button"
          :class="{ active: zoom === option.value }"
          @click="zoom = option.value"
        >
          {{ option.label }}
        </button>
      </div>
    </header>

    <div v-if="loading || error" class="horizontal-timeline__state" :class="{ error }">
      <span>{{ error || '正在加载周期报告分布' }}</span>
      <button v-if="error" type="button" class="ak-button" @click="$emit('retry')">重试</button>
    </div>

    <div v-else class="horizontal-timeline__track" :style="{ '--timeline-scale': zoomScale }">
      <button
        v-for="item in normalizedItems"
        :key="item.id"
        type="button"
        class="horizontal-timeline__item"
        :class="[`horizontal-timeline__item--${item.tone}`, { active: item.id === selectedId }]"
        :style="{ left: `${item.left}%` }"
        @click="$emit('select', item.id)"
      >
        <span class="horizontal-timeline__dot" />
        <strong>{{ item.timeLabel }}</strong>
        <small>{{ item.title }}</small>
      </button>
      <div v-if="!normalizedItems.length" class="horizontal-timeline__empty">暂无报告</div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  title: { type: String, default: '周期报告横向时间轴' },
  items: { type: Array, default: () => [] },
  selectedId: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' }
})

defineEmits(['select', 'retry'])

const zoom = ref('normal')
const zoomOptions = [
  { value: 'dense', label: '全局' },
  { value: 'normal', label: '标准' },
  { value: 'wide', label: '放大' }
]

const zoomScale = computed(() => ({ dense: 1, normal: 1.45, wide: 2.2 }[zoom.value] || 1.45))

const normalizedItems = computed(() => {
  const rows = props.items
    .map((item, index) => {
      const ts = Date.parse(item.created_at || item.updated_at || item.time || '')
      return {
        id: String(item.report_id || item.id || index),
        title: item.title || item.report_type || '周期报告',
        risk: String(item.risk_level || item.severity || '').toLowerCase(),
        ts: Number.isFinite(ts) ? ts : index,
        index
      }
    })
    .sort((a, b) => a.ts - b.ts || a.index - b.index)
  const min = rows[0]?.ts ?? 0
  const max = rows[rows.length - 1]?.ts ?? min
  return rows.map((item) => ({
    ...item,
    tone: resolveTone(item.risk),
    left: rows.length === 1 ? 50 : 4 + normalize(item.ts, min, max) * 92,
    timeLabel: new Date(item.ts).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false })
  }))
})

const rangeLabel = computed(() => {
  if (!normalizedItems.value.length) return '等待 LangGraph 周期子图产出'
  const first = normalizedItems.value[0]
  const last = normalizedItems.value[normalizedItems.value.length - 1]
  return `${first.timeLabel} - ${last.timeLabel} / ${normalizedItems.value.length} reports`
})

function normalize(value, min, max) {
  if (max === min) return 0.5
  return (value - min) / (max - min)
}

function resolveTone(risk) {
  if (['critical', 'high'].includes(risk)) return 'red'
  if (risk === 'medium') return 'amber'
  if (risk === 'low') return 'green'
  return 'blue'
}
</script>

<style scoped>
.horizontal-timeline {
  display: grid;
  gap: 10px;
}

.horizontal-timeline__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.horizontal-timeline__header h3 {
  margin: 0;
  color: #f2f5f7;
  font-size: 13px;
}

.horizontal-timeline__header p {
  margin: 3px 0 0;
  color: #8e9aa6;
  font-size: 11px;
}

.horizontal-timeline__zoom {
  display: flex;
  gap: 4px;
}

.horizontal-timeline__zoom button {
  padding: 5px 8px;
  color: #8e9aa6;
  background: rgba(7, 10, 14, 0.6);
  border: 1px solid rgba(185, 196, 207, 0.16);
  border-radius: 2px;
  font-size: 11px;
  font-weight: 900;
  cursor: pointer;
}

.horizontal-timeline__zoom button.active {
  color: #e6edf3;
  border-color: rgba(111, 158, 172, 0.55);
  background: rgba(111, 158, 172, 0.14);
}

.horizontal-timeline__track {
  position: relative;
  min-width: calc(100% * var(--timeline-scale));
  height: 136px;
  overflow-x: auto;
  background:
    linear-gradient(90deg, rgba(185, 196, 207, 0.12), rgba(185, 196, 207, 0.12)) 0 67px / 100% 1px no-repeat,
    rgba(7, 10, 14, 0.48);
  border: 1px solid rgba(185, 196, 207, 0.14);
  border-radius: 3px;
}

.horizontal-timeline__item {
  --time-accent: #6f9eac;
  position: absolute;
  top: 32px;
  width: 150px;
  min-height: 80px;
  padding: 31px 8px 8px;
  transform: translateX(-50%);
  color: #dce4eb;
  background: rgba(14, 18, 23, 0.88);
  border: 1px solid rgba(185, 196, 207, 0.16);
  border-top: 3px solid var(--time-accent);
  border-radius: 2px;
  text-align: left;
  cursor: pointer;
}

.horizontal-timeline__item--red {
  --time-accent: #b96a61;
}

.horizontal-timeline__item--amber {
  --time-accent: #b28b5a;
}

.horizontal-timeline__item--green {
  --time-accent: #6d9482;
}

.horizontal-timeline__item.active,
.horizontal-timeline__item:hover {
  border-color: color-mix(in srgb, var(--time-accent) 60%, rgba(185, 196, 207, 0.18));
}

.horizontal-timeline__dot {
  position: absolute;
  top: -15px;
  left: 50%;
  width: 12px;
  height: 12px;
  transform: translateX(-50%);
  background: var(--time-accent);
  border: 2px solid #0b0f14;
  box-shadow: 0 0 14px color-mix(in srgb, var(--time-accent) 45%, transparent);
}

.horizontal-timeline__item strong,
.horizontal-timeline__item small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.horizontal-timeline__item strong {
  color: var(--time-accent);
  font-size: 11px;
}

.horizontal-timeline__item small {
  margin-top: 5px;
  color: #aab4bf;
  font-size: 11px;
}

.horizontal-timeline__state,
.horizontal-timeline__empty {
  padding: 18px;
  color: #8e9aa6;
  background: rgba(7, 10, 14, 0.48);
  border: 1px dashed rgba(185, 196, 207, 0.22);
  border-radius: 3px;
}

.horizontal-timeline__state.error {
  color: #d4877c;
  border-color: rgba(185, 106, 97, 0.36);
}
</style>
