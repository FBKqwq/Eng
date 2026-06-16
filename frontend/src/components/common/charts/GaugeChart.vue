<template>
  <BaseChart :option="option" :loading="loading" :height="height" :empty-text="placeholder" />
</template>

<script setup>
import BaseChart from './BaseChart.vue'

defineProps({
  option: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  height: { type: String, default: '240px' },
  placeholder: { type: String, default: '仪表盘占位：等待聚合接口 / 业务数据' }
})
</script>
