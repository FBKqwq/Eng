<template>
  <div class="chart-band">
    <EmptyState
      title="图表带占位"
      :description="templateHint"
      pending-api="POST /logs/aggregate（metrics.js 六模板）"
      compact
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import EmptyState from '../common/EmptyState.vue'

const props = defineProps({
  chartTemplates: { type: Array, default: () => [] }
})

const templateHint = computed(() => {
  if (!props.chartTemplates.length) {
    return '本日志类型暂未配置聚合图表模板'
  }
  return `已配置模板：${props.chartTemplates.join('、')}（F4 阶段接入聚合数据）`
})
</script>
