<template>
  <EmptyState
    title="动态筛选器占位"
    description="字段目录 GET /logs/fields（M1 已落地，F2 接入）"
    :pending-api="`GET /api/v1/logs/fields?log_type=${logType}`"
    compact
  />
</template>

<script setup>
import EmptyState from '../common/EmptyState.vue'

defineProps({
  logType: { type: String, required: true }
})
</script>
