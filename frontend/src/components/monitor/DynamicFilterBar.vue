<template>
  <EmptyState
    title="动态筛选器占位"
    description="字段来自 GET /logs/fields?log_type=xxx 动态渲染，接口未就绪前使用本地兜底"
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
