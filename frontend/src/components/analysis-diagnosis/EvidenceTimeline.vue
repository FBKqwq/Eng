<template>
  <section class="evidence-path" :class="{ 'is-placeholder': isPlaceholder }" :aria-label="emptyDescription">
    <div class="serpentine" role="list">
      <div
        v-for="row in serpentineRows"
        :key="row.index"
        class="serpentine-row"
        :class="[
          `serpentine-row--${row.direction}`,
          { 'is-last': row.index === serpentineRows.length - 1 }
        ]"
        role="presentation"
      >
        <span class="serpentine-row__line" aria-hidden="true" />
        <span
          v-if="row.index < serpentineRows.length - 1"
          class="serpentine-row__turn"
          aria-hidden="true"
        />
        <button
          v-for="point in row.points"
          :key="point.key"
          type="button"
          class="evidence-point"
          :class="[
            point.tone ? `evidence-point--${point.tone}` : '',
            point.edge ? `evidence-point--${point.edge}` : ''
          ]"
          :style="{ '--point-x': `${point.x}%` }"
          :title="point.detail"
          :aria-label="point.ariaLabel"
          role="listitem"
        >
          <span class="evidence-point__dot" aria-hidden="true" />
          <span v-if="point.detail" class="evidence-point__popover" role="tooltip">
            <time class="tabular-nums">{{ point.time }}</time>
            <strong>{{ point.label }}</strong>
            <small>{{ point.summary }}</small>
            <p>{{ point.detail }}</p>
          </span>
        </button>
      </div>
    </div>
    <p v-if="isPlaceholder" class="evidence-path__empty">{{ emptyDescription }}</p>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { formatTime } from '../../utils/format.js'

const props = defineProps({
  /** evidence_logs：结构化对象或字符串摘要 */
  evidenceLogs: { type: Array, default: () => [] }
})

const emptyDescription =
  '证据时间轴：evidence_logs + 上下文日志，ERROR 节点红色高亮（等待诊断结果）'

const ERROR_LEVELS = new Set(['ERROR', 'FATAL', 'CRITICAL'])
const WARN_LEVELS = new Set(['WARN', 'WARNING'])
const POINTS_PER_ROW = 12

function resolveTone(level) {
  const normalized = String(level || '').toUpperCase()
  if (ERROR_LEVELS.has(normalized)) return 'danger'
  if (WARN_LEVELS.has(normalized)) return 'warning'
  return undefined
}

function guessToneFromText(text) {
  const upper = String(text || '').toUpperCase()
  if (upper.includes('ERROR') || upper.includes('FAIL') || upper.includes('TIMEOUT')) {
    return 'danger'
  }
  if (upper.includes('WARN')) return 'warning'
  return undefined
}

function toTimestamp(value) {
  if (value == null || value === '') return Number.NaN
  const date = new Date(value)
  return date.getTime()
}

function normalizeLog(log, index) {
  if (typeof log === 'string') {
    return {
      sortKey: index,
      time: '—',
      label: '证据摘要',
      detail: log,
      summary: summarizeText(log),
      tone: guessToneFromText(log)
    }
  }

  const level = log.log_level || log.level || ''
  const label = log.service_name || log.service || '未知服务'
  const detailParts = [
    log.message,
    log.error_code ? `error_code=${log.error_code}` : '',
    log.event_type,
    log.trace_id ? `trace=${log.trace_id}` : ''
  ].filter(Boolean)

  return {
    sortKey: toTimestamp(log.timestamp) || index,
    time: formatTime(log.timestamp),
    label,
    detail: detailParts.join(' · ') || log.snippet || log.reason || '',
    summary: log.error_code || log.event_type || log.trace_id || '证据节点',
    tone: resolveTone(level)
  }
}

function summarizeText(value) {
  const text = String(value || '').trim()
  if (!text) return '证据节点'
  return text.length > 28 ? `${text.slice(0, 28)}...` : text
}

const timelineItems = computed(() => {
  if (!props.evidenceLogs?.length) return []

  return [...props.evidenceLogs]
    .map(normalizeLog)
    .sort((a, b) => a.sortKey - b.sortKey)
    .map(({ sortKey, time, label, detail, summary, tone }) => ({ sortKey, time, label, detail, summary, tone }))
})

const PLACEHOLDER_ITEMS = [
  { sortKey: 0, time: '—', label: '时间点', detail: '等待后端时间戳字段', summary: '待取证' },
  { sortKey: 1, time: '—', label: '证据节点', detail: 'evidence_logs / 上下文日志', summary: '待返回' },
  { sortKey: 2, time: '—', label: '关联事件', detail: 'ERROR 节点将高亮显示', summary: '待关联', tone: 'warning' }
]

const isPlaceholder = computed(() => timelineItems.value.length === 0)
const displayItems = computed(() => (isPlaceholder.value ? PLACEHOLDER_ITEMS : timelineItems.value))

function buildPoint(item, index, items) {
  const rowIndex = Math.floor(index / POINTS_PER_ROW)
  const rowStart = rowIndex * POINTS_PER_ROW
  const rowPointCount = Math.min(POINTS_PER_ROW, items.length - rowStart)
  const slotIndex = index - rowStart
  const offset = rowPointCount <= 1 ? 0.5 : (slotIndex + 0.5) / rowPointCount
  const x = rowIndex % 2 === 0 ? offset * 100 : (1 - offset) * 100
  const edge = x <= 12 ? 'start' : x >= 88 ? 'end' : ''
  const detail = item.detail || item.summary || item.label

  return {
    ...item,
    key: `${index}-${item.label}-${item.time}`,
    rowIndex,
    x,
    edge,
    detail,
    ariaLabel: `${item.time} ${item.label} ${item.summary}`
  }
}

const serpentineRows = computed(() => {
  const items = displayItems.value
  const rowCount = Math.max(1, Math.ceil(items.length / POINTS_PER_ROW))
  const rows = Array.from({ length: rowCount }, (_, index) => ({
    index,
    direction: index % 2 === 0 ? 'ltr' : 'rtl',
    points: []
  }))

  items.forEach((item, index) => {
    const point = buildPoint(item, index, items)
    rows[point.rowIndex].points.push(point)
  })

  return rows
})
</script>

<style scoped>
.evidence-path {
  min-height: 252px;
  padding: 12px 12px 10px;
}

.serpentine {
  position: relative;
  min-width: 520px;
  padding: 4px 16px 22px;
}

.serpentine-row {
  position: relative;
  height: 88px;
  overflow: visible;
}

.serpentine-row.is-last {
  height: 68px;
}

.serpentine-row__line {
  position: absolute;
  left: 0;
  right: 0;
  top: 40px;
  height: 3px;
  background:
    linear-gradient(90deg, rgba(111, 158, 172, 0.18), rgba(111, 158, 172, 0.9), rgba(111, 158, 172, 0.18));
  box-shadow: 0 0 18px rgba(111, 158, 172, 0.14);
}

.serpentine-row__turn {
  position: absolute;
  top: 40px;
  z-index: 1;
  width: 42px;
  height: 88px;
  border: 3px solid rgba(111, 158, 172, 0.78);
  box-shadow: 0 0 18px rgba(111, 158, 172, 0.12);
  pointer-events: none;
}

.serpentine-row--ltr .serpentine-row__turn {
  right: 0;
  border-left: 0;
  border-radius: 0 18px 18px 0;
}

.serpentine-row--rtl .serpentine-row__turn {
  left: 0;
  border-right: 0;
  border-radius: 18px 0 0 18px;
}

.evidence-point {
  --evidence-accent: #6f9eac;
  position: absolute;
  left: clamp(0px, var(--point-x), 100%);
  top: 40px;
  z-index: 4;
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  padding: 0;
  color: inherit;
  background: transparent;
  border: 0;
  outline: none;
  transform: translate(-50%, -50%);
  cursor: pointer;
}

.evidence-point--danger {
  --evidence-accent: #b96a61;
}

.evidence-point--warning {
  --evidence-accent: #b28b5a;
}

.evidence-point__dot {
  display: block;
  width: 13px;
  height: 13px;
  border: 2px solid rgba(7, 10, 14, 0.96);
  border-radius: 50%;
  background: var(--evidence-accent);
  box-shadow:
    0 0 0 3px rgba(7, 10, 14, 0.96),
    0 0 0 6px color-mix(in srgb, var(--evidence-accent) 22%, transparent),
    0 0 18px color-mix(in srgb, var(--evidence-accent) 38%, transparent);
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.evidence-point:hover,
.evidence-point:focus-visible {
  z-index: 20;
}

.evidence-point:hover .evidence-point__dot,
.evidence-point:focus-visible .evidence-point__dot {
  transform: scale(1.35);
  box-shadow:
    0 0 0 4px rgba(7, 10, 14, 0.98),
    0 0 0 8px color-mix(in srgb, var(--evidence-accent) 28%, transparent),
    0 0 24px color-mix(in srgb, var(--evidence-accent) 52%, transparent);
}

.evidence-point__popover {
  position: absolute;
  left: 50%;
  top: 30px;
  z-index: 30;
  display: none;
  width: min(300px, 46vw);
  padding: 10px 11px;
  color: #dce4eb;
  background: rgba(6, 9, 13, 0.97);
  border: 1px solid color-mix(in srgb, var(--evidence-accent) 46%, rgba(185, 196, 207, 0.16));
  border-radius: 4px;
  box-shadow: 0 18px 36px rgba(0, 0, 0, 0.34);
  text-align: left;
  transform: translateX(-50%);
}

.evidence-point--start .evidence-point__popover {
  left: 0;
  transform: none;
}

.evidence-point--end .evidence-point__popover {
  right: 0;
  left: auto;
  transform: none;
}

.evidence-point:hover .evidence-point__popover,
.evidence-point:focus-visible .evidence-point__popover {
  display: block;
}

.evidence-point__popover time {
  display: block;
  color: #8e9aa6;
  font-size: 10px;
  line-height: 1.2;
}

.evidence-point__popover strong {
  display: block;
  margin-top: 5px;
  color: #f2f5f7;
  font-size: 13px;
  line-height: 1.35;
}

.evidence-point__popover small {
  display: block;
  margin-top: 4px;
  color: var(--evidence-accent);
  font-size: 11px;
  font-weight: 800;
  line-height: 1.35;
}

.evidence-point__popover p {
  margin: 6px 0 0;
  color: #aab4bf;
  font-size: 12px;
  line-height: 1.5;
}

.evidence-path__empty {
  margin: 12px 0 0;
  color: #8e9aa6;
  font-size: 12px;
  text-align: center;
}

@media (max-width: 760px) {
  .evidence-path {
    padding-inline: 8px;
  }

  .serpentine {
    min-width: 460px;
    padding-inline: 12px;
  }

  .evidence-point__popover {
    width: 260px;
  }
}
</style>
