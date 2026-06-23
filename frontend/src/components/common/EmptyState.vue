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
  gap: var(--spacing-sm);
  padding: var(--spacing-lg) var(--spacing-md);
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-md);
  background:
    linear-gradient(180deg, rgba(248, 250, 252, 0.92), rgba(255, 255, 255, 0.92));
  color: var(--color-text-secondary);
  text-align: center;
  min-height: 120px;
}
.empty-state.compact {
  min-height: 80px;
  padding: 16px;
}
.empty-icon {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 999px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 18px;
  opacity: 1;
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
