<template>
  <div class="trace-page">
    <section class="page-section">
      <h2>检索区</h2>
      <TraceSearchBar
        :trace-id="routeTraceId"
        :loading="loading"
        @search="handleSearch"
      />
    </section>

    <div
      v-if="loading"
      class="trace-page__status trace-page__status--loading"
      role="status"
      aria-live="polite"
    >
      正在检索链路日志…
    </div>
    <div
      v-else-if="errorMessage"
      class="trace-page__status trace-page__status--error"
      role="alert"
    >
      <span>{{ errorMessage }}</span>
      <button
        v-if="lastTraceId"
        type="button"
        class="retry-btn"
        @click="handleSearch(lastTraceId)"
      >
        重试
      </button>
    </div>

    <section class="page-section">
      <h2>链路瀑布</h2>
      <TraceWaterfall :logs="displayLogs" />
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import TraceSearchBar from '../../components/analysis-trace/TraceSearchBar.vue'
import TraceWaterfall from '../../components/analysis-trace/TraceWaterfall.vue'
import { searchByTraceId } from '../../api/logs.js'

const route = useRoute()

const loading = ref(false)
const errorMessage = ref('')
const logs = ref([])
const lastTraceId = ref('')

const routeTraceId = computed(() => {
  const id = route.query.trace_id
  return id != null && id !== '' ? String(id) : ''
})

const displayLogs = computed(() => {
  if (loading.value || errorMessage.value) return []
  return logs.value
})

async function handleSearch(traceId) {
  const trimmed = String(traceId ?? '').trim()
  if (!trimmed || loading.value) return

  loading.value = true
  errorMessage.value = ''
  logs.value = []
  lastTraceId.value = trimmed

  try {
    const res = await searchByTraceId(trimmed)
    const items = res.data?.items ?? []

    if (!items.length) {
      errorMessage.value = `未找到 trace_id「${trimmed}」的链路日志，请检查 ID 是否正确`
      logs.value = []
      return
    }

    logs.value = items
  } catch (e) {
    logs.value = []
    const code = e.error?.code
    if (code === 'es_unavailable') {
      errorMessage.value =
        e.error?.message || 'Elasticsearch 暂不可用，链路检索无法完成，请稍后重试'
    } else {
      errorMessage.value = e.error?.message || e.message || '链路检索失败，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (routeTraceId.value) {
    handleSearch(routeTraceId.value)
  }
})

watch(routeTraceId, (nextId, prevId) => {
  if (!nextId || nextId === prevId || nextId === lastTraceId.value) return
  handleSearch(nextId)
})
</script>

<style scoped>
.trace-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.trace-page .page-section {
  margin-bottom: 0;
}

.trace-page__status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  font-size: 13px;
  line-height: 1.5;
}

.trace-page__status--loading {
  border: 1px solid var(--color-border);
  background: var(--color-info-bg, var(--color-bg));
  color: var(--color-text-secondary);
}

.trace-page__status--error {
  border: 1px solid var(--color-danger);
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.retry-btn {
  flex-shrink: 0;
  padding: 4px 10px;
  border: 1px solid currentColor;
  border-radius: var(--radius-sm);
  background: transparent;
  color: inherit;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.retry-btn:hover {
  opacity: 0.85;
}
</style>
