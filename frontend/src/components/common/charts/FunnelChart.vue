<template>
  <BaseChart :option="option" :loading="loading" :height="height" :empty-text="placeholder" />
</template>

<script setup>
import BaseChart from './BaseChart.vue'

defineProps({
  option: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  height: { type: String, default: '320px' },
  placeholder: { type: String, default: '漏斗图占位：等待 behavior_funnel 聚合接口' }
})
</script>
