<template>
  <TimeAxis
    :items="timelineItems"
    :description="emptyDescription"
  />
</template>

<script setup>
import { computed } from 'vue'
import TimeAxis from '../common/TimeAxis.vue'
import { formatTime } from '../../utils/format.js'

const props = defineProps({
  /** evidence_logs：结构化对象或字符串摘要 */
  evidenceLogs: { type: Array, default: () => [] }
})

const emptyDescription =
  '证据时间轴：evidence_logs + 上下文日志，ERROR 节点红色高亮（等待诊断结果）'

const ERROR_LEVELS = new Set(['ERROR', 'FATAL', 'CRITICAL'])
const WARN_LEVELS = new Set(['WARN', 'WARNING'])

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
    tone: resolveTone(level)
  }
}

const timelineItems = computed(() => {
  if (!props.evidenceLogs?.length) return []

  return [...props.evidenceLogs]
    .map(normalizeLog)
    .sort((a, b) => a.sortKey - b.sortKey)
    .map(({ time, label, detail, tone }) => ({ time, label, detail, tone }))
})
</script>
