<template>
  <article class="stat-card">
    <p class="label">{{ label }}</p>
    <p class="value tabular-nums">{{ displayValue }}</p>
    <p v-if="hint" class="hint">{{ hint }}</p>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: null },
  hint: { type: String, default: '' }
})

const displayValue = computed(() => {
  if (props.value === null || props.value === undefined || props.value === '') {
    return '—'
  }
  return props.value
})
</script>

<style scoped>
.stat-card {
  position: relative;
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.18s ease-out, transform 0.18s ease-out;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  background: var(--color-primary);
  opacity: 0.35;
}

.stat-card:hover {
  box-shadow: var(--shadow-card);
  transform: translateY(-1px);
}

@media (prefers-reduced-motion: reduce) {
  .stat-card {
    transition: none;
  }
  .stat-card:hover {
    transform: none;
  }
}

.label {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.value {
  margin: var(--spacing-sm) 0 0;
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text);
}

.hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--color-text-muted);
}
</style>
