import { formatDuration, formatNumber, formatTime } from './format.js'

/** HTTP 状态码语义色 */
export function httpStatusTone(code) {
  const n = Number(code)
  if (!Number.isFinite(n)) return 'muted'
  if (n >= 500) return 'danger'
  if (n >= 400) return 'warning'
  if (n >= 300) return 'info'
  if (n >= 200) return 'success'
  return 'muted'
}

export function getRowField(row, key) {
  if (!row || key == null) return undefined
  if (row[key] !== undefined && row[key] !== null && row[key] !== '') return row[key]
  const payload = row.payload
  if (payload && typeof payload === 'object' && payload[key] != null) return payload[key]
  return undefined
}

/**
 * @param {object} row
 * @param {{ key: string, renderType?: string, unit?: string }} col
 */
export function formatCellDisplay(row, col) {
  const value = getRowField(row, col.key)
  if (value == null || value === '') return '—'

  const renderType = col.renderType || 'text'

  if (renderType === 'timestamp') return formatTime(value)
  if (renderType === 'duration') {
    const ms = col.key === 'request_time' ? Number(value) * 1000 : Number(value)
    return formatDuration(ms)
  }
  if (renderType === 'metric') {
    const unit = row.metric_unit || col.unit
    if (unit && unit !== 'auto') return `${formatNumber(value)} ${unit}`
    return formatNumber(value)
  }
  if (renderType === 'change_summary') {
    return summarizeChange(row)
  }
  if (typeof value === 'object') {
    try {
      const text = JSON.stringify(value)
      return text.length > 80 ? `${text.slice(0, 80)}…` : text
    } catch {
      return String(value)
    }
  }
  return String(value)
}

function summarizeChange(row) {
  const summary = getRowField(row, 'change_summary')
  if (summary) return String(summary).slice(0, 120)
  const before = getRowField(row, 'before_value')
  const after = getRowField(row, 'after_value')
  if (before || after) {
    return `变更前 ${compactJson(before)} → 变更后 ${compactJson(after)}`
  }
  return '—'
}

function compactJson(value) {
  if (value == null) return '—'
  try {
    const text = typeof value === 'string' ? value : JSON.stringify(value)
    return text.length > 36 ? `${text.slice(0, 36)}…` : text
  } catch {
    return String(value)
  }
}

export async function copyText(text) {
  const value = String(text ?? '').trim()
  if (!value) return false
  try {
    await navigator.clipboard.writeText(value)
    return true
  } catch {
    return false
  }
}
