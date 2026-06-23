<template>
  <div class="components-page">
    <header class="page-toolbar">
      <p class="intro-desc">
        各基础设施组件运行状态矩阵，数据来自 <code>GET /system/status</code> 与 <code>GET /health</code>，60s 自动刷新。
      </p>
      <button type="button" class="refresh-btn" :disabled="loading" @click="loadStatus()">
        {{ loading ? '刷新中…' : '刷新状态' }}
      </button>
    </header>

    <div v-if="errorMessage" class="page-alert" role="alert">
      <span>{{ errorMessage }}</span>
      <button type="button" class="retry-btn" @click="loadStatus()">重试</button>
    </div>

    <section class="overview-strip" aria-label="组件状态概览">
      <div class="overview-item">
        <span class="metric-value tabular-nums">{{ healthyCount }}</span>
        <span class="metric-label">正常组件</span>
      </div>
      <div class="overview-item">
        <span class="metric-value tabular-nums">{{ attentionCount }}</span>
        <span class="metric-label">需关注组件</span>
      </div>
      <div class="overview-item">
        <span class="metric-value tabular-nums metric-value--time">{{ lastUpdatedText }}</span>
        <span class="metric-label">最近刷新</span>
      </div>
    </section>

    <div v-if="esFallbackActive" class="fallback-banner" role="status">
      Elasticsearch 集群健康为 <strong>unknown</strong>，当前按容器 running 态降级展示（DEV 兜底规则）。
    </div>

    <div class="page-grid page-grid-3">
      <StatusCard
        v-for="card in displayCards"
        :key="card.key"
        :title="card.label"
        :status="card.status"
        :detail="card.detail"
        :port="card.port"
        :container="card.container"
        :loading="initialLoading"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { getApiHealth, getSystemStatus } from '../../api/system'
import StatusCard from '../../components/common/StatusCard.vue'
import { normalizeComponents } from '../../utils/systemStatus'

const POLL_INTERVAL_MS = 60000

const COMPONENT_KEYS = ['backend', 'kafka', 'elasticsearch', 'logstash', 'kibana', 'llm']

const PLACEHOLDER_CARDS = COMPONENT_KEYS.map((key) => ({
  key,
  label: key.charAt(0).toUpperCase() + key.slice(1),
  status: 'unknown',
  detail: '',
  port: undefined,
  container: undefined
}))

const loading = ref(false)
const initialLoading = ref(true)
const errorMessage = ref('')
const fetchError = ref(null)
const apiHealth = ref(null)
const systemStatus = ref(null)
const lastUpdatedAt = ref(null)
let pollTimer = null

const cards = computed(() =>
  normalizeComponents(systemStatus.value, {
    apiHealth: apiHealth.value,
    frontendReady: true,
    error: fetchError.value
  })
)

const displayCards = computed(() => (cards.value.length ? cards.value : PLACEHOLDER_CARDS))

const healthyCount = computed(() => displayCards.value.filter((card) => card.status === 'healthy').length)

const attentionCount = computed(() =>
  displayCards.value.filter((card) => ['degraded', 'down', 'unknown', 'offline'].includes(card.status)).length
)

const lastUpdatedText = computed(() => {
  if (!lastUpdatedAt.value) return '—'
  return lastUpdatedAt.value.toLocaleTimeString()
})

const esFallbackActive = computed(() => {
  const esCard = cards.value.find((card) => card.key === 'elasticsearch')
  return Boolean(esCard?.detail?.includes('健康未知，按容器态展示'))
})

const loadStatus = async ({ silent = false } = {}) => {
  if (!silent) {
    loading.value = true
  }
  errorMessage.value = ''
  fetchError.value = null

  const [healthResult, systemResult] = await Promise.allSettled([getApiHealth(), getSystemStatus()])
  const systemStatusOk = systemResult.status === 'fulfilled'

  if (healthResult.status === 'fulfilled') {
    apiHealth.value = healthResult.value.data || { status: 'ok' }
  } else if (systemStatusOk) {
    apiHealth.value = { status: 'ok' }
  } else {
    apiHealth.value = { status: 'down' }
  }

  if (systemStatusOk) {
    systemStatus.value = {
      ...(systemResult.value.data || {}),
      backend_api_status: 'ok'
    }
  } else {
    systemStatus.value = null
    fetchError.value = systemResult.reason
    errorMessage.value =
      systemResult.reason?.message || '系统状态接口失败，请确认后端 /system/status 是否可用。'
  }

  lastUpdatedAt.value = new Date()
  initialLoading.value = false
  loading.value = false
}

onMounted(() => {
  loadStatus()
  pollTimer = setInterval(() => loadStatus({ silent: true }), POLL_INTERVAL_MS)
})

onUnmounted(() => {
  if (pollTimer != null) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})
</script>

<style scoped>
.components-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.page-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.intro-desc {
  margin: 0;
  flex: 1;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.intro-desc code {
  font-size: 12px;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--color-bg);
  color: var(--color-text);
}

.refresh-btn {
  flex-shrink: 0;
  padding: 8px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease-out, border-color 0.15s ease-out;
}

.refresh-btn:hover:not(:disabled) {
  background: var(--color-bg);
  border-color: var(--color-primary);
}

.refresh-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.page-alert {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-danger);
  background: var(--color-danger-bg);
  color: var(--color-danger);
  font-size: 13px;
  line-height: 1.5;
}

.retry-btn {
  flex-shrink: 0;
  padding: 4px 10px;
  border: 1px solid var(--color-danger);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-danger);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.retry-btn:hover {
  background: var(--color-danger-bg);
}

.overview-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-md);
}

.overview-item {
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.metric-value {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
}

.metric-value--time {
  font-size: 18px;
  font-weight: 600;
}

.metric-label {
  display: block;
  margin-top: 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.fallback-banner {
  padding: var(--spacing-sm) var(--spacing-md);
  border-left: 3px solid var(--color-warning);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  background: var(--color-warning-bg);
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.5;
}

.fallback-banner strong {
  color: var(--color-warning);
  font-weight: 600;
}

@media (max-width: 768px) {
  .page-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .overview-strip {
    grid-template-columns: 1fr;
  }

  .page-alert {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (prefers-reduced-motion: reduce) {
  .refresh-btn {
    transition: none;
  }
}
</style>
