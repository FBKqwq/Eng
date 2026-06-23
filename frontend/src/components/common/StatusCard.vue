<template>
  <article class="status-card" :class="`tone-${tone}`">
    <header>
      <h3>{{ title }}</h3>
      <span class="badge">{{ statusLabel }}</span>
    </header>
    <p class="desc">{{ description || '组件状态卡占位：等待 /system/status 数据' }}</p>
    <slot />
  </article>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  statusLabel: { type: String, default: '未知' },
  /** success | warning | danger | neutral */
  tone: { type: String, default: 'neutral' },
  description: { type: String, default: '' }
})
</script>

<style scoped>
.status-card {
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.status-card header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-sm);
}

.status-card h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
}

.badge {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.tone-neutral .badge {
  background: var(--color-bg);
  color: var(--color-text-secondary);
}

.tone-success .badge {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.tone-warning .badge {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.tone-danger .badge {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.desc {
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}
</style>
