<template>
  <div class="time-axis">
    <EmptyState
      title="垂直时间轴占位"
      :description="description"
      compact
    />
  </div>
</template>

<script setup>
import EmptyState from './EmptyState.vue'

defineProps({
  description: {
    type: String,
    default: '用于证据链、报告时间轴等场景（F5/F6 阶段实现）'
  }
})
</script>
