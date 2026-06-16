/** 时间/字节/百分比/耗时格式化工具 */

export function formatDateTime(value) {
  if (!value) return '-'
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleString('zh-CN', { hour12: false })
}

export function formatPercent(value, digits = 1) {
  if (value == null || Number.isNaN(Number(value))) return '-'
  return `${(Number(value) * 100).toFixed(digits)}%`
}

export function formatDurationMs(ms) {
  if (ms == null || Number.isNaN(Number(ms))) return '-'
  const n = Number(ms)
  if (n < 1000) return `${n}ms`
  if (n < 60000) return `${(n / 1000).toFixed(1)}s`
  return `${(n / 60000).toFixed(1)}min`
}

export function formatBytes(bytes) {
  if (bytes == null || Number.isNaN(Number(bytes))) return '-'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let n = Number(bytes)
  let i = 0
  while (n >= 1024 && i < units.length - 1) {
    n /= 1024
    i += 1
  }
  return `${n.toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

export function formatNumber(value) {
  if (value == null || Number.isNaN(Number(value))) return '-'
  return Number(value).toLocaleString('zh-CN')
}
