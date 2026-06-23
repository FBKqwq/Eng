<template>
  <div class="pipeline-page">
    <section class="graph-section" aria-label="链路健康图谱">
      <ParticleBackdrop
        class="graph-section__backdrop"
        variant="pipeline"
        :intensity="pipelineBackdropIntensity"
      />
      <div class="graph-section__content">
      <EmptyState
        v-if="statusError && !statusLoading"
        title="无法加载链路状态"
        :description="statusError"
        icon="!"
      >
        <button type="button" class="retry-btn" @click="loadStatus">重试</button>
      </EmptyState>
      <PipelineGraph
        v-else
        :nodes="pipelineNodes"
        :loading="statusLoading"
      />
      </div>
    </section>

    <VerifyOutputPanel
      :output="verifyOutput"
      :running="verifyRunning"
      :error="verifyError"
      @verify="handleVerify"
    />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import ParticleBackdrop from '../../components/common/ParticleBackdrop.vue'
import PipelineGraph from '../../components/system/PipelineGraph.vue'
import VerifyOutputPanel from '../../components/system/VerifyOutputPanel.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import { getSystemStatus, verifyPipeline } from '../../api/system.js'
import { getPipelineNodes } from '../../utils/systemStatus.js'
import { usePolling } from '../../composables/usePolling.js'

const systemStatus = ref(null)
const statusLoading = ref(false)
const statusError = ref('')

const verifyRunning = ref(false)
const verifyError = ref('')
const verifyOutput = ref(null)
const lastSuccessOutput = ref(null)

const pipelineNodes = computed(() => getPipelineNodes(systemStatus.value))

/** 验证进行中时背板强度 0.4→0.7（§9.11.7） */
const pipelineBackdropIntensity = computed(() => (verifyRunning.value ? 0.7 : 0.4))

async function loadStatus() {
  statusLoading.value = true
  statusError.value = ''
  try {
    const res = await getSystemStatus()
    systemStatus.value = {
      ...(res.data || {}),
      backend_api_status: 'ok'
    }
  } catch (err) {
    systemStatus.value = null
    statusError.value =
      err?.message || '系统状态接口失败，请确认后端 /system/status 是否可用。'
  } finally {
    statusLoading.value = false
  }
}

async function handleVerify({ workers }) {
  verifyRunning.value = true
  verifyError.value = ''

  try {
    const result = await verifyPipeline({ workers })
    verifyOutput.value = result.data

    if (result.data?.success) {
      lastSuccessOutput.value = result.data
    } else {
      verifyError.value = result.data?.error || '全链路验证未通过，请查看验证输出。'
    }

    await loadStatus()
  } catch (err) {
    const message =
      err?.response?.data?.detail || err?.message || '全链路验证请求失败。'
    verifyError.value = typeof message === 'string' ? message : JSON.stringify(message)

    if (lastSuccessOutput.value) {
      verifyOutput.value = lastSuccessOutput.value
    } else {
      verifyOutput.value = {
        success: false,
        exit_code: -1,
        duration_ms: 0,
        stdout: '',
        stderr: verifyError.value
      }
    }
  } finally {
    verifyRunning.value = false
  }
}

usePolling(loadStatus, 60000, true)
</script>

<style scoped>
.pipeline-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.graph-section {
  position: relative;
  min-height: 140px;
  border-radius: var(--radius-md);
  overflow: hidden;
}

.graph-section__backdrop {
  border-radius: var(--radius-md);
}

.graph-section__content {
  position: relative;
  z-index: 1;
}

.retry-btn {
  margin-top: 8px;
  padding: 6px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.retry-btn:hover {
  border-color: var(--color-primary);
  background: var(--color-bg);
}

@media (prefers-reduced-motion: reduce) {
  .retry-btn {
    transition: none;
  }
}
</style>
