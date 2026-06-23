<template>
  <section class="entry-panel page-section">
    <div class="entry-panel__header">
      <p class="entry-panel__eyebrow">LangGraph Context</p>
      <h2>智能推断源</h2>
      <p class="entry-panel__desc">
        基于活跃预警、路由上下文与全局时间窗自动取证，不再使用手工日志投喂。
      </p>
    </div>

    <div class="source-card" :class="`source-card--${sourceKind}`">
      <span class="source-card__dot" />
      <div>
        <p class="source-card__label">{{ sourceLabel }}</p>
        <p class="source-card__value">{{ sourceValue }}</p>
      </div>
    </div>

    <label class="field-label" for="diag-alert-select">活跃预警上下文</label>
    <select
      id="diag-alert-select"
      v-model="selectedAlertId"
      class="field-select"
      :disabled="loading || !alertOptions.length"
    >
      <option value="" disabled>暂无预警时使用全局时间窗</option>
      <option
        v-for="item in alertOptions"
        :key="item.alert_id"
        :value="item.alert_id"
      >
        {{ formatAlertOption(item) }}
      </option>
    </select>

    <div class="context-grid">
      <div>
        <span>服务</span>
        <strong>{{ contextService }}</strong>
      </div>
      <div>
        <span>严重度</span>
        <strong>{{ contextSeverity }}</strong>
      </div>
      <div>
        <span>时间窗</span>
        <strong>{{ timeRangeLabel }}</strong>
      </div>
    </div>

    <p class="time-window tabular-nums">{{ timeRangeSummary }}</p>

    <button
      type="button"
      class="submit-btn"
      :class="{ 'submit-btn--loading': loading }"
      :disabled="!canSubmit"
      @click="handleSubmit"
    >
      {{ loading ? '推断链路运行中…' : '运行智能推断' }}
    </button>

    <p v-if="validationMessage" class="validation-msg" role="alert">
      {{ validationMessage }}
    </p>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useTimeRange } from '../../composables/useTimeRange.js'
import { formatTime } from '../../utils/format.js'

const props = defineProps({
  loading: { type: Boolean, default: false },
  alerts: { type: Array, default: () => [] }
})

const emit = defineEmits(['submit', 'request-alerts'])

const route = useRoute()
const { presets, preset, range } = useTimeRange()

const selectedAlertId = ref('')
const routeServiceName = ref('')

const alertOptions = computed(() => props.alerts ?? [])

const selectedAlert = computed(() =>
  alertOptions.value.find((item) => item.alert_id === selectedAlertId.value) ?? null
)

const sourceKind = computed(() => {
  if (selectedAlert.value) return 'alert'
  if (routeServiceName.value) return 'service'
  return 'window'
})

const sourceLabel = computed(() => {
  if (sourceKind.value === 'alert') return '活跃预警驱动'
  if (sourceKind.value === 'service') return '服务上下文驱动'
  return '全局时间窗巡检'
})

const sourceValue = computed(() => {
  if (selectedAlert.value) {
    return selectedAlert.value.title || selectedAlert.value.alert_type || selectedAlert.value.alert_id
  }
  if (routeServiceName.value) return routeServiceName.value
  return '等待预警或使用当前窗口做健康推断'
})

const contextService = computed(() =>
  selectedAlert.value?.affected_service || routeServiceName.value || '全链路'
)

const contextSeverity = computed(() => selectedAlert.value?.severity || '动态评估')

const timeRangeLabel = computed(
  () => presets.find((p) => p.value === preset.value)?.label ?? preset.value
)

const timeRangeSummary = computed(() => {
  const { start, end } = range.value
  return `${formatTime(start)} — ${formatTime(end)}`
})

const validationMessage = computed(() => {
  if (props.loading) return ''
  if (!selectedAlert.value && !routeServiceName.value && !range.value?.start) {
    return '等待可用预警或全局时间窗'
  }
  return ''
})

const canSubmit = computed(() => !props.loading && !validationMessage.value)

function formatAlertOption(item) {
  const title = item.title || item.alert_type || item.alert_id
  const service = item.affected_service ? ` · ${item.affected_service}` : ''
  return `${title}${service}`
}

function generateRequestId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return `diag-${crypto.randomUUID()}`
  }
  return `diag-${Date.now()}`
}

function toIsoTime(ms) {
  return new Date(ms).toISOString()
}

function buildPayload() {
  const { start, end } = range.value
  const alert = selectedAlert.value
  return {
    request_id: generateRequestId(),
    service_name: alert?.affected_service || routeServiceName.value || undefined,
    keyword: alert?.title || alert?.alert_type || route.query.keyword || undefined,
    time_range_start: toIsoTime(start),
    time_range_end: toIsoTime(end),
    remark: alert?.alert_id
      ? `source:active_alert;alert_id:${alert.alert_id}`
      : `source:langgraph_window;window:${timeRangeLabel.value}`
  }
}

function handleSubmit() {
  if (!canSubmit.value) return
  emit('submit', buildPayload())
}

function applyRouteQuery(query) {
  if (!query || typeof query !== 'object') return
  if (query.alert_id) selectedAlertId.value = String(query.alert_id)
  if (query.service_name) routeServiceName.value = String(query.service_name)
}

function pickDefaultAlert(items) {
  if (selectedAlertId.value || !items?.length) return
  selectedAlertId.value = items[0].alert_id ?? ''
}

onMounted(() => {
  applyRouteQuery(route.query)
  emit('request-alerts')
})

watch(() => route.query, applyRouteQuery, { deep: true })

watch(
  () => props.alerts,
  (items) => {
    pickDefaultAlert(items)
    if (!selectedAlertId.value || !items?.length) return
    const exists = items.some((item) => item.alert_id === selectedAlertId.value)
    if (!exists) selectedAlertId.value = items[0]?.alert_id ?? ''
  },
  { immediate: true }
)
</script>

<style scoped>
.entry-panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: 0;
}

.entry-panel__eyebrow {
  margin: 0 0 2px;
  color: var(--color-primary);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

.entry-panel__header h2 {
  margin-bottom: 4px;
}

.entry-panel__desc {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.55;
}

.source-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
  border: 1px solid rgba(37, 99, 235, 0.2);
  border-radius: var(--radius-md);
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.92), rgba(255, 255, 255, 0.96));
}

.source-card__dot {
  width: 9px;
  height: 9px;
  margin-top: 6px;
  border-radius: 999px;
  background: var(--color-primary);
  box-shadow: 0 0 0 5px rgba(37, 99, 235, 0.12);
}

.source-card__label {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 11px;
  font-weight: 700;
}

.source-card__value {
  margin: 3px 0 0;
  color: var(--color-text);
  font-size: 13px;
  font-weight: 800;
  line-height: 1.35;
}

.field-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-secondary);
}

.field-select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: 12px;
  box-sizing: border-box;
}

.field-select:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.context-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.context-grid div {
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface-subtle);
}

.context-grid span {
  display: block;
  color: var(--color-text-muted);
  font-size: 10px;
}

.context-grid strong {
  display: block;
  margin-top: 2px;
  color: var(--color-text);
  font-size: 13px;
}

.time-window {
  margin: 0;
  padding: 8px 10px;
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  font-size: 11px;
  line-height: 1.4;
}

.validation-msg {
  margin: 0;
  font-size: 11px;
  color: var(--color-danger);
}

.submit-btn {
  padding: 9px 12px;
  border: none;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--color-primary), var(--color-cyan));
  color: #fff;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
  transition:
    opacity var(--transition-fast),
    transform var(--transition-fast),
    box-shadow var(--transition-fast);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 10px 26px rgba(37, 99, 235, 0.22);
}

.submit-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  transform: none;
}

.submit-btn--loading {
  opacity: 0.76;
}

@media (prefers-reduced-motion: reduce) {
  .submit-btn {
    transition: none;
  }

  .submit-btn:hover:not(:disabled) {
    transform: none;
  }
}
</style>
