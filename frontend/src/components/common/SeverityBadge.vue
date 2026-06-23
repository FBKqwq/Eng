<template>
  <span class="severity-badge" :class="toneClass">{{ displayLabel }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** 级别键：low/info/medium/warning/high/error/critical 及日志级别 debug/warn */
  level: { type: String, default: 'info' },
  label: { type: String, default: '' }
})

/** 级别 → 语义色 tone（配色唯一出处，复用 index.css 令牌） */
const LEVEL_TONE_MAP = {
  debug: 'muted',
  low: 'info',
  info: 'info',
  medium: 'warning',
  warn: 'warning',
  warning: 'warning',
  high: 'danger',
  error: 'danger',
  critical: 'critical',
  success: 'success'
}

const toneClass = computed(() => `tone-${LEVEL_TONE_MAP[props.level?.toLowerCase()] ?? 'info'}`)

const displayLabel = computed(() => props.label || props.level)
</script>

<style scoped>
.severity-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  line-height: 1.2;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.tone-info {
  background: var(--color-info-bg);
  color: var(--color-info);
}

.tone-warning {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.tone-danger {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.tone-critical {
  background: var(--color-danger);
  color: var(--color-surface);
}

.tone-success {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.tone-muted {
  background: var(--color-bg);
  color: var(--color-text-muted);
}
</style>
