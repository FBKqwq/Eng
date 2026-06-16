<template>
  <div class="empty-state" :class="{ compact }">
    <div class="empty-icon">{{ icon }}</div>
    <h3 v-if="title">{{ title }}</h3>
    <p v-if="description">{{ description }}</p>
    <p v-if="pendingApi" class="pending-tag">待接入：{{ pendingApi }}</p>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '占位区域' },
  description: { type: String, default: '' },
  pendingApi: { type: String, default: '' },
  icon: { type: String, default: '◇' },
  compact: { type: Boolean, default: false }
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px 24px;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  text-align: center;
  min-height: 120px;
}
.empty-state.compact {
  min-height: 80px;
  padding: 16px;
}
.empty-icon {
  font-size: 24px;
  opacity: 0.5;
}
.empty-state h3 {
  margin: 0;
  font-size: 15px;
  color: var(--color-text);
}
.empty-state p {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  max-width: 480px;
}
.pending-tag {
  display: inline-block;
  margin-top: 4px;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 12px;
}
</style>
