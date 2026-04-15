<template>
  <div class="card" v-if="result">
    <h3>诊断结果</h3>
    <pre>{{ JSON.stringify(result, null, 2) }}</pre>
  </div>
</template>

<script setup>
defineProps({ result: { type: Object, default: null } })
</script>

<style scoped>
.card { margin-top: 16px; background: white; padding: 16px; border-radius: 8px; }
pre { white-space: pre-wrap; }
</style>
