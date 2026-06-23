<template>
  <article class="stat-card" :class="{ 'is-loading': loading }">
    <div v-if="loading" class="stat-skeleton" aria-hidden="true">
      <div class="sk sk--label" />
      <div class="sk sk--value" />
      <div class="sk sk--hint" />
    </div>
    <template v-else>
      <p class="label">{{ label }}</p>
      <div class="value-row">
        <p class="value tabular-nums">{{ displayValue }}</p>
        <p
          v-if="showDelta"
          class="delta"
          :class="`delta--${deltaDirection}`"
          :aria-label="`环比${deltaAriaLabel}`"
        >
          <span class="delta-arrow" aria-hidden="true">{{ deltaArrow }}</span>
          <span class="delta-value tabular-nums">{{ formattedDelta }}</span>
        </p>
      </div>
      <p v-if="hint" class="hint">{{ hint }}</p>
    </template>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { formatNumber, formatPercent } from '../../utils/format.js'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: null },
  hint: { type: String, default: '' },
  /** 环比变化量；未传或无效时不展示箭头（默认隐藏） */
  delta: { type: [Number, String], default: null },
  /** 环比方向：up | down | flat */
  deltaDirection: {
    type: String,
    default: '',
    validator: (value) => !value || ['up', 'down', 'flat'].includes(value)
  },
  /**
   * 环比数值口径：
   * - points：百分点（如 12.5 表示 +12.5%），对齐 es_compare_time_windows.change_percent
   * - ratio：小数比率（0.125 → 12.5%）
   */
  deltaKind: {
    type: String,
    default: 'points',
    validator: (value) => ['points', 'ratio'].includes(value)
  },
  /** 加载中状态，显示骨架屏而非实际内容 */
  loading: { type: Boolean, default: false }
})

const displayValue = computed(() => {
  if (props.value === null || props.value === undefined || props.value === '') {
    return '—'
  }
  return props.value
})

const showDelta = computed(() => {
  if (props.delta == null || props.delta === '') return false
  if (!['up', 'down', 'flat'].includes(props.deltaDirection)) return false
  return !Number.isNaN(Number(props.delta))
})

const formattedDelta = computed(() => {
  if (!showDelta.value) return ''
  const n = Number(props.delta)

  if (props.deltaDirection === 'flat' || n === 0) {
    return props.deltaKind === 'ratio' ? formatPercent(0) : '0%'
  }

  if (props.deltaKind === 'ratio') {
    return formatPercent(n)
  }

  const sign = n > 0 ? '+' : '-'
  return `${sign}${formatNumber(Math.abs(n))}%`
})

const deltaArrow = computed(() => {
  if (props.deltaDirection === 'up') return '↑'
  if (props.deltaDirection === 'down') return '↓'
  return '→'
})

const deltaAriaLabel = computed(() => {
  if (props.deltaDirection === 'up') return `上升 ${formattedDelta.value}`
  if (props.deltaDirection === 'down') return `下降 ${formattedDelta.value}`
  return `持平 ${formattedDelta.value}`
})
</script>

<style scoped>
.stat-card {
  position: relative;
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.96));
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  transition:
    border-color var(--transition-fast),
    box-shadow var(--transition-fast),
    transform var(--transition-fast);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  background: linear-gradient(90deg, var(--color-primary), var(--color-cyan));
  opacity: 0.7;
}

.stat-card:hover:not(.is-loading) {
  border-color: rgba(37, 99, 235, 0.24);
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-1px);
}

@media (prefers-reduced-motion: reduce) {
  .stat-card {
    transition: none;
  }
  .stat-card:hover {
    transform: none;
  }
  .stat-skeleton {
    animation: none;
    background: var(--color-bg);
  }
}

/* Skeleton loading state */
.stat-skeleton {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sk {
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--color-bg) 25%, #e5e7eb 50%, var(--color-bg) 75%);
  background-size: 200% 100%;
  animation: stat-shimmer 1.4s ease-in-out infinite;
}

.sk--label { width: 48%; height: 13px; }
.sk--value { width: 70%; height: 28px; }
.sk--hint  { width: 36%; height: 12px; }

@keyframes stat-shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.label {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.value-row {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: var(--spacing-sm);
}

.value {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  color: var(--color-text);
}

.delta {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.2;
}

.delta--up {
  color: var(--color-success);
}

.delta--down {
  color: var(--color-danger);
}

.delta--flat {
  color: var(--color-text-muted);
}

.delta-arrow {
  font-size: 11px;
  line-height: 1;
}

.hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--color-text-muted);
}
</style>
