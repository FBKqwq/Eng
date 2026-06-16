<template>
  <span class="severity-badge" :class="`level-${level}`">{{ label || level }}</span>
</template>

<script setup>
defineProps({
  level: { type: String, default: 'info' },
  label: { type: String, default: '' }
})
</script>

<style scoped>
.severity-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}
.level-low, .level-info { background: #e0f2fe; color: #0369a1; }
.level-medium, .level-warning { background: #fef3c7; color: #b45309; }
.level-high, .level-error { background: #fee2e2; color: #b91c1c; }
.level-critical { background: #7f1d1d; color: #fff; }
</style>
