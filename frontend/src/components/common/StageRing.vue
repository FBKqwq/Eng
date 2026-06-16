<template>
  <div class="stage-ring">
    <EmptyState
      title="分析阶段环占位"
      description="将 node_trace 翻译为业务阶段进度（取上下文 → 关联分析 → 根因推断 → 定级 → 成文）"
      compact
    />
  </div>
</template>

<script setup>
import EmptyState from './EmptyState.vue'

defineProps({
  stages: { type: Array, default: () => [] }
})
</script>
