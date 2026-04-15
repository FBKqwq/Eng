<template>
  <section>
    <h1>智能诊断</h1>
    <DiagnosisForm @submit="handleSubmit" />
    <p v-if="loading">诊断中...</p>
    <DiagnosisResultCard :result="result" />
  </section>
</template>

<script setup>
import { ref } from 'vue'
import DiagnosisForm from '../../components/diagnosis/DiagnosisForm.vue'
import DiagnosisResultCard from '../../components/diagnosis/DiagnosisResultCard.vue'
import { runDiagnosis } from '../../api/diagnosis'

const loading = ref(false)
const result = ref(null)

const handleSubmit = async (payload) => {
  loading.value = true
  try {
    const { data } = await runDiagnosis(payload)
    result.value = data
  } catch (error) {
    result.value = { error: error.message }
  } finally {
    loading.value = false
  }
}
</script>
