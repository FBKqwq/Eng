/** 时间/字节/百分比/耗时格式化工具（纯函数，边界安全） */

/**
 * 时间戳或 ISO 字符串 → 本地可读时间
 * @param {number|string|Date|null|undefined} ts
 */
export function formatTime(ts) {
  if (ts == null || ts === '') return '-'
  let date
  if (ts instanceof Date) {
    date = ts
  } else if (typeof ts === 'number') {
    // 秒级时间戳（< 1e12）自动转毫秒
    date = new Date(ts < 1e12 ? ts * 1000 : ts)
  } else {
    date = new Date(ts)
  }
  if (Number.isNaN(date.getTime())) return String(ts)
  return date.toLocaleString('zh-CN', { hour12: false })
}

/**
 * 字节数 → B/KB/MB/GB
 * @param {number|null|undefined} n
 */
export function formatBytes(n) {
  if (n == null || Number.isNaN(Number(n))) return '-'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let value = Number(n)
  let i = 0
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024
    i += 1
  }
  return `${value.toFixed(i === 0 ? 0 : 1)} ${units[i]}`
}

/**
 * 小数 → 百分比文本（0.125 → 12.5%）
 * @param {number|null|undefined} n
 * @param {number} [digits=1]
 */
export function formatPercent(n, digits = 1) {
  if (n == null || Number.isNaN(Number(n))) return '-'
  return `${(Number(n) * 100).toFixed(digits)}%`
}

/**
 * 毫秒耗时 → 可读时长
 * @param {number|null|undefined} ms
 */
export function formatDuration(ms) {
  if (ms == null || Number.isNaN(Number(ms))) return '-'
  const n = Number(ms)
  if (n < 0) return '-'
  if (n < 1000) return `${Math.round(n)}ms`
  if (n < 60_000) return `${(n / 1000).toFixed(1)}s`
  if (n < 3_600_000) return `${(n / 60_000).toFixed(1)}min`
  return `${(n / 3_600_000).toFixed(1)}h`
}

/** 千分位数字（表格计数等场景复用） */
export function formatNumber(value) {
  if (value == null || Number.isNaN(Number(value))) return '-'
  return Number(value).toLocaleString('zh-CN')
}
