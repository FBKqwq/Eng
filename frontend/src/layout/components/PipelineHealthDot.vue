<template>
  <router-link
    to="/system/pipeline"
    class="pipeline-dot"
    :class="`tone-${tone}`"
    :title="title"
  >
    <span class="dot" aria-hidden="true" />
    <span class="label">链路健康</span>
  </router-link>
</template>

<script setup>
import { ref, computed } from 'vue'
import { getSystemStatus } from '../../api/system.js'
import { usePolling } from '../../composables/usePolling.js'

/** getSystemStatus 解包后的业务负载 */
const status = ref(null)

/** 读取关键容器运行态（containers / services 互备） */
function isContainerRunning(key) {
  const s = status.value
  if (!s) return false
  const container = s.containers?.[key] || s.services?.[key]
  return String(container?.status || '').toLowerCase() === 'running'
}

/**
 * 按嵌套字段折算链路健康四态（禁止读 overall / pipeline_healthy）
 * @returns {'success'|'warning'|'danger'|'unknown'}
 */
function derivePipelineHealthTone() {
  const s = status.value
  if (!s) return 'unknown'

  const kafkaAvailable = s.kafka?.available
  const esAvailable = s.elasticsearch?.available
  const esCluster = String(s.elasticsearch?.cluster_status || '').toLowerCase()
  const kafkaRunning = isContainerRunning('kafka')
  const esRunning = isContainerRunning('elasticsearch')

  // 红：专项 available===false 且关键容器非 running
  const kafkaRed = kafkaAvailable === false && !kafkaRunning
  const esRed = esAvailable === false && !esRunning
  if (kafkaRed || esRed || esCluster === 'red') {
    return 'danger'
  }

  // 黄：部分可用或 ES 集群 yellow
  if (esCluster === 'yellow') return 'warning'

  const kafkaHealthy = kafkaAvailable === true && kafkaRunning
  const esHealthy = esAvailable === true && esRunning
  if (kafkaHealthy && esHealthy) {
    return 'success'
  }

  if (
    kafkaAvailable === true ||
    esAvailable === true ||
    kafkaRunning ||
    esRunning
  ) {
    return 'warning'
  }

  return 'unknown'
}

const tone = computed(() => derivePipelineHealthTone())

const title = computed(() => {
  const map = {
    success: '链路正常',
    warning: '链路需关注',
    danger: '链路异常',
    unknown: '状态未知'
  }
  return map[tone.value]
})

/** 拉取系统快照；失败降级为 null（灰态），不向 UI 抛错 */
async function fetchStatus() {
  try {
    const res = await getSystemStatus()
    status.value = res?.data ?? null
  } catch {
    status.value = null
  }
}

usePolling(fetchStatus, 60000, true)
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
  text-decoration: none;
  transition: background 0.15s ease-out;
}

.pipeline-dot:hover {
  background: var(--color-sidebar-hover);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--color-sidebar-text-muted);
  transition: background 0.2s ease-out;
}

.tone-success .dot {
  background: var(--color-success);
}

.tone-warning .dot {
  background: var(--color-warning);
}

.tone-danger .dot {
  background: var(--color-danger);
}

.tone-unknown .dot {
  background: var(--color-sidebar-text-muted);
}

@media (prefers-reduced-motion: reduce) {
  .pipeline-dot,
  .dot {
    transition: none;
  }
}
</style>
