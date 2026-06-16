<template>
  <article class="stat-card">
    <p class="label">{{ label }}</p>
    <p class="value">{{ value ?? '—' }}</p>
    <p v-if="hint" class="hint">{{ hint }}</p>
  </article>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: null },
  hint: { type: String, default: '数字指标卡占位' }
})
</script>

<style scoped>
.stat-card {
  padding: 16px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}
.label {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
}
.value {
  margin: 8px 0 0;
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
