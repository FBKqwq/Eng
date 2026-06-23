<template>
  <div class="trace-waterfall">
    <div class="summary-bar">
      <div class="summary-item">
        <span class="summary-label">总耗时</span>
        <span class="summary-value tabular-nums">{{ summary.totalDuration }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">经过服务</span>
        <span class="summary-value tabular-nums">{{ summary.serviceCount }}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">断点位置</span>
        <span
          class="summary-value tabular-nums"
          :class="{ 'summary-value--danger': summary.breakpointLabel !== '—' }"
        >
          {{ summary.breakpointLabel }}
        </span>
      </div>
    </div>

    <EmptyState
      v-if="!sortedLogs.length"
      title="暂无链路日志"
      description="检索 trace_id 后，跨服务泳道瀑布图将在此展示"
      compact
    />

    <div v-else class="waterfall-panel">
      <div class="time-ruler" aria-hidden="true">
        <span class="ruler-label">{{ formatTime(summary.startMs) }}</span>
        <span class="ruler-label ruler-label--end">{{ formatTime(summary.endMs) }}</span>
      </div>

      <div class="lanes-wrap">
        <div
          v-if="breakpointMarker"
          class="breakpoint-marker"
          :style="{ left: `${breakpointMarker.leftPct}%` }"
          :title="breakpointMarker.label"
        >
          <span class="breakpoint-flag">断点</span>
        </div>

        <div
          v-for="lane in lanes"
          :key="lane.service"
          class="lane-row"
        >
          <div class="lane-label" :title="lane.service">{{ lane.service }}</div>
          <div class="lane-track">
            <button
              v-for="block in lane.blocks"
              :key="block.key"
              type="button"
              class="log-block"
              :class="{
                'log-block--error': block.isError,
                'log-block--expanded': expandedKey === block.key,
                'log-block--breakpoint': block.isBreakpoint
              }"
              :style="blockStyle(block)"
              :title="block.title"
              @click="toggleExpand(block.key)"
            >
              <span class="block-level">{{ block.levelLabel }}</span>
              <span class="block-message">{{ block.message }}</span>
            </button>
          </div>
        </div>
      </div>

      <div v-if="expandedLog" class="field-drawer">
        <div class="field-drawer__header">
          <span class="field-drawer__title">原始字段</span>
          <span class="field-drawer__meta">
            {{ expandedLog.service }} · {{ formatTime(expandedLog.timestampMs) }}
          </span>
          <button type="button" class="field-drawer__close" @click="expandedKey = null">收起</button>
        </div>
        <pre class="field-drawer__json">{{ formatRowJson(expandedLog.raw) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import EmptyState from '../common/EmptyState.vue'
import { formatDuration, formatTime } from '../../utils/format.js'

const props = defineProps({
  /** 同 trace 日志列表（由父级 searchByTraceId 传入，本组件不调 API） */
  logs: { type: Array, default: () => [] }
})

const ERROR_LEVELS = new Set(['ERROR', 'FATAL', 'CRITICAL'])
const TIMESTAMP_KEYS = ['@timestamp', 'timestamp', 'time', 'created_at']
const DURATION_KEYS = ['duration_ms', 'latency_ms', 'response_time', 'elapsed_ms', 'stay_duration']
const GAP_THRESHOLD_MS = 5000

const expandedKey = ref(null)

watch(
  () => props.logs,
  () => {
    expandedKey.value = null
  }
)

function toTimestampMs(value) {
  if (value == null || value === '') return Number.NaN
  if (typeof value === 'number') {
    return value < 1e12 ? value * 1000 : value
  }
  const date = new Date(value)
  return date.getTime()
}

function readTimestamp(log) {
  for (const key of TIMESTAMP_KEYS) {
    const ms = toTimestampMs(log?.[key])
    if (Number.isFinite(ms)) return ms
  }
  return Number.NaN
}

function readService(log) {
  const name = log?.service_name || log?.service || log?.host?.name || '未知服务'
  return String(name).trim() || '未知服务'
}

function readLevel(log) {
  return String(log?.log_level || log?.level || log?.severity || '').toUpperCase()
}

function isErrorLog(log) {
  return ERROR_LEVELS.has(readLevel(log))
}

function readDurationMs(log) {
  for (const key of DURATION_KEYS) {
    const value = log?.[key]
    if (value != null && !Number.isNaN(Number(value))) {
      return Math.max(0, Number(value))
    }
  }
  return null
}

function readMessage(log) {
  const parts = [log?.message, log?.event_type, log?.error_code ? `code=${log.error_code}` : '']
    .filter(Boolean)
    .map(String)
  return parts.join(' · ') || '—'
}

function formatRowJson(row) {
  try {
    return JSON.stringify(row, null, 2)
  } catch {
    return String(row)
  }
}

const sortedLogs = computed(() =>
  [...(props.logs || [])]
    .map((log, index) => ({
      raw: log,
      index,
      timestampMs: readTimestamp(log),
      service: readService(log),
      level: readLevel(log),
      isError: isErrorLog(log),
      durationMs: readDurationMs(log),
      message: readMessage(log)
    }))
    .filter((item) => Number.isFinite(item.timestampMs))
    .sort((a, b) => a.timestampMs - b.timestampMs || a.index - b.index)
)

const breakpoint = computed(() => {
  const items = sortedLogs.value
  if (items.length < 2) {
    const only = items[0]
    if (only?.isError) {
      return {
        type: 'error',
        timestampMs: only.timestampMs,
        label: `${only.service} · ERROR`,
        logKey: logKey(only, 0)
      }
    }
    return null
  }

  const errorItem = items.find((item) => item.isError)
  if (errorItem) {
    const idx = items.indexOf(errorItem)
    return {
      type: 'error',
      timestampMs: errorItem.timestampMs,
      label: `${errorItem.service} · ERROR`,
      logKey: logKey(errorItem, idx)
    }
  }

  let maxGap = 0
  let gapAfterIndex = -1
  const gaps = []
  for (let i = 1; i < items.length; i += 1) {
    const gap = items[i].timestampMs - items[i - 1].timestampMs
    gaps.push(gap)
    if (gap > maxGap) {
      maxGap = gap
      gapAfterIndex = i - 1
    }
  }

  const sortedGaps = [...gaps].sort((a, b) => a - b)
  const medianGap = sortedGaps[Math.floor(sortedGaps.length / 2)] || 0
  const isGapBreakpoint = maxGap >= GAP_THRESHOLD_MS || (medianGap > 0 && maxGap >= medianGap * 3)

  if (isGapBreakpoint && gapAfterIndex >= 0) {
    const after = items[gapAfterIndex]
    const before = items[gapAfterIndex + 1]
    return {
      type: 'gap',
      timestampMs: after.timestampMs + maxGap / 2,
      label: `${after.service} → ${before.service} · 间隔 ${formatDuration(maxGap)}`,
      logKey: logKey(before, gapAfterIndex + 1)
    }
  }

  return null
})

const summary = computed(() => {
  const items = sortedLogs.value
  if (!items.length) {
    return {
      totalDuration: '—',
      serviceCount: '—',
      breakpointLabel: '—',
      startMs: null,
      endMs: null
    }
  }

  const startMs = items[0].timestampMs
  const endMs = items[items.length - 1].timestampMs
  const spanMs = Math.max(endMs - startMs, 0)
  const services = new Set(items.map((item) => item.service))

  return {
    totalDuration: formatDuration(spanMs || readDurationMs(items[items.length - 1].raw) || 0),
    serviceCount: String(services.size),
    breakpointLabel: breakpoint.value?.label || '—',
    startMs,
    endMs
  }
})

const breakpointMarker = computed(() => {
  const bp = breakpoint.value
  const items = sortedLogs.value
  if (!bp || items.length < 2) return null

  const startMs = items[0].timestampMs
  const endMs = items[items.length - 1].timestampMs
  const span = Math.max(endMs - startMs, 1)
  const leftPct = Math.min(100, Math.max(0, ((bp.timestampMs - startMs) / span) * 100))

  return {
    leftPct,
    label: bp.label
  }
})

function logKey(item, index) {
  return item.raw?.id ?? item.raw?._id ?? `${item.service}-${item.timestampMs}-${index}`
}

const lanes = computed(() => {
  const items = sortedLogs.value
  if (!items.length) return []

  const startMs = items[0].timestampMs
  const endMs = items[items.length - 1].timestampMs
  const span = Math.max(endMs - startMs, 1)
  const bpKey = breakpoint.value?.logKey

  const serviceOrder = []
  const seen = new Set()
  for (const item of items) {
    if (!seen.has(item.service)) {
      seen.add(item.service)
      serviceOrder.push(item.service)
    }
  }

  const blocksByService = new Map(serviceOrder.map((service) => [service, []]))

  items.forEach((item, index) => {
    const next = items[index + 1]
    const durationMs =
      item.durationMs ??
      (next ? Math.max(next.timestampMs - item.timestampMs, 80) : Math.min(span * 0.08, 1200))

    const leftPct = ((item.timestampMs - startMs) / span) * 100
    const widthPct = Math.max((durationMs / span) * 100, 2.5)
    const key = logKey(item, index)

    blocksByService.get(item.service)?.push({
      key,
      leftPct,
      widthPct,
      isError: item.isError,
      isBreakpoint: key === bpKey,
      levelLabel: item.level || 'LOG',
      message: item.message,
      title: `${item.service} · ${formatTime(item.timestampMs)} · ${item.message}`,
      raw: item.raw,
      timestampMs: item.timestampMs,
      service: item.service
    })
  })

  return serviceOrder.map((service) => ({
    service,
    blocks: blocksByService.get(service) || []
  }))
})

const expandedLog = computed(() => {
  if (!expandedKey.value) return null
  for (const lane of lanes.value) {
    const block = lane.blocks.find((item) => item.key === expandedKey.value)
    if (block) return block
  }
  return null
})

function blockStyle(block) {
  return {
    left: `${block.leftPct}%`,
    width: `${block.widthPct}%`
  }
}

function toggleExpand(key) {
  expandedKey.value = expandedKey.value === key ? null : key
}
</script>

<style scoped>
.summary-bar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 96px;
}

.summary-label {
  font-size: 11px;
  color: var(--color-text-muted);
}

.summary-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  transition: color 300ms ease;
}

.summary-value--danger {
  color: var(--color-danger);
}

.waterfall-panel {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.time-ruler {
  display: flex;
  justify-content: space-between;
  padding: 6px 12px 6px 112px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
  font-size: 11px;
  color: var(--color-text-muted);
}

.lanes-wrap {
  position: relative;
  padding: var(--spacing-sm) 0;
}

.breakpoint-marker {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 0;
  border-left: 2px dashed var(--color-danger);
  pointer-events: none;
  z-index: 2;
  transform: translateX(-1px);
}

.breakpoint-flag {
  position: absolute;
  top: 4px;
  left: 4px;
  padding: 1px 6px;
  border-radius: 999px;
  background: var(--color-danger-bg);
  color: var(--color-danger);
  font-size: 10px;
  font-weight: 600;
  white-space: nowrap;
}

.lane-row {
  display: grid;
  grid-template-columns: 100px 1fr;
  gap: var(--spacing-sm);
  align-items: stretch;
  min-height: 44px;
  padding: 4px 12px;
}

.lane-row + .lane-row {
  border-top: 1px dashed var(--color-border);
}

.lane-label {
  display: flex;
  align-items: center;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lane-track {
  position: relative;
  min-height: 36px;
  border-radius: var(--radius-sm);
  background: linear-gradient(
    90deg,
    rgba(59, 130, 246, 0.04) 0%,
    rgba(59, 130, 246, 0.02) 50%,
    rgba(59, 130, 246, 0.04) 100%
  );
}

.log-block {
  position: absolute;
  top: 4px;
  bottom: 4px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 1px;
  min-width: 48px;
  padding: 2px 6px;
  border: 1px solid rgba(59, 130, 246, 0.35);
  border-radius: 4px;
  background: rgba(59, 130, 246, 0.12);
  color: var(--color-text);
  text-align: left;
  cursor: pointer;
  overflow: hidden;
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    border-color 180ms ease,
    background 180ms ease;
}

.log-block:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
  z-index: 1;
}

.log-block--error {
  border-color: rgba(220, 38, 38, 0.55);
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.log-block--breakpoint {
  box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.25);
}

.log-block--expanded {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
  z-index: 2;
}

.block-level {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.04em;
  opacity: 0.85;
}

.block-message {
  font-size: 10px;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.field-drawer {
  border-top: 1px solid var(--color-border);
  background: var(--color-bg);
  animation: drawer-in 280ms ease-out;
}

.field-drawer__header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-border);
}

.field-drawer__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
}

.field-drawer__meta {
  flex: 1;
  font-size: 12px;
  color: var(--color-text-muted);
}

.field-drawer__close {
  padding: 2px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-size: 12px;
  color: var(--color-text-secondary);
  cursor: pointer;
}

.field-drawer__json {
  margin: 0;
  padding: 12px;
  max-height: 240px;
  overflow: auto;
  font-size: 11px;
  line-height: 1.45;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  color: var(--color-text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}

@keyframes drawer-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .summary-value,
  .log-block,
  .field-drawer {
    transition: none;
    animation: none;
  }

  .log-block:hover {
    transform: none;
  }
}
</style>
