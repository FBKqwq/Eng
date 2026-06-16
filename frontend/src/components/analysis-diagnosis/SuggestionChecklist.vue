<template>
  <div class="suggestion-panel">
    <EmptyState title="处理建议核对清单" description="suggestions 可勾选清单（前端演示态）" compact />
    <StageRing />
  </div>
</template>

<script setup>
import EmptyState from '../common/EmptyState.vue'
import StageRing from '../common/StageRing.vue'
</script>

<style scoped>
.suggestion-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
