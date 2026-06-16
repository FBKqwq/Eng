<template>
  <router-link to="/system/pipeline" class="pipeline-dot" :class="`tone-${tone}`" :title="title">
    <span class="dot" />
    <span class="label">链路健康</span>
  </router-link>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getSystemStatus } from '../../api/system.js'

const status = ref(null)

const tone = computed(() => {
  const s = status.value
  if (!s) return 'unknown'
  if (s.overall === 'healthy' || s.pipeline_healthy) return 'success'
  if (s.overall === 'degraded') return 'warning'
  return 'danger'
})

const title = computed(() => {
  const map = {
    success: '链路正常',
    warning: '链路需关注',
    danger: '链路异常',
    unknown: '状态未知'
  }
  return map[tone.value]
})

async function fetchStatus() {
  try {
    const res = await getSystemStatus()
    status.value = res?.data ?? null
  } catch {
    status.value = null
  }
}

onMounted(() => {
  fetchStatus()
  setInterval(fetchStatus, 60000)
})
</script>

<style scoped>
.pipeline-dot {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  margin-top: auto;
  border-top: 1px solid var(--color-sidebar-border);
  color: var(--color-sidebar-text-muted);
  font-size: 12px;
}
.pipeline-dot:hover {
  background: var(--color-sidebar-hover);
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6b7280;
}
.tone-success .dot { background: #22c55e; }
.tone-warning .dot { background: #f59e0b; }
.tone-danger .dot { background: #ef4444; }
</style>
