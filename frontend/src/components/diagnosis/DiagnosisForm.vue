<template>
  <form class="form" @submit.prevent="submit">
    <input v-model="form.service_name" placeholder="服务名，如 payment-service" />
    <input v-model="form.trace_id" placeholder="trace_id" />
    <input v-model="form.keyword" placeholder="关键字，如 timeout / pay" />
    <button type="submit">开始诊断</button>
  </form>
</template>

<script setup>
import { reactive } from 'vue'

const emit = defineEmits(['submit'])
const form = reactive({ service_name: '', trace_id: '', keyword: '' })

const submit = () => emit('submit', { ...form })
</script>

<style scoped>
.form { display: flex; gap: 12px; flex-wrap: wrap; }
input { padding: 8px 10px; min-width: 220px; }
button { padding: 8px 14px; }
</style>
