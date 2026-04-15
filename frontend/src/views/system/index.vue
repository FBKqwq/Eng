<template>
  <section>
    <h1>系统状态</h1>
    <button @click="load">获取状态</button>
    <pre v-if="result">{{ JSON.stringify(result, null, 2) }}</pre>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { getSystemStatus } from '../../api/system'

const result = ref(null)
const load = async () => {
  const { data } = await getSystemStatus()
  result.value = data
}
</script>
