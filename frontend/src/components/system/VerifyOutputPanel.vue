<template>
  <section class="page-section verify-panel">
    <header class="panel-header">
      <div>
        <h2>链路验证</h2>
        <p class="panel-desc">一键触发全链路验证，检查多线程日志生产到 Elasticsearch 检索的完整传输链路</p>
      </div>
    </header>

    <div class="verify-toolbar">
      <label class="workers-field">
        <span>并发 workers</span>
        <input
          v-model.number="workersInput"
          type="number"
          min="1"
          max="8"
          step="1"
          class="workers-input"
          :disabled="running"
          @blur="normalizeWorkers"
        />
      </label>
      <button
        type="button"
        class="verify-btn"
        :class="{ 'is-loading': running }"
        :disabled="running"
        @click="handleVerify"
      >
        <span v-if="running" class="btn-spinner" aria-hidden="true" />
        {{ running ? '验证中…' : '一键验证' }}
      </button>
    </div>

    <div v-if="error" class="verify-error" role="alert">
      {{ error }}
    </div>

    <details class="output-fold" :open="outputOpen">
      <summary class="output-summary">
        <span>验证输出</span>
        <span class="summary-meta">{{ summaryText }}</span>
      </summary>

      <div v-if="stepNodes.length" class="steps-list" role="list" aria-label="验证步骤">
        <div
          v-for="(node, index) in stepNodes"
          :key="node.key || node.label || index"
          class="step-row"
          :class="`step-${stepTone(node.status)}`"
          role="listitem"
        >
          <span class="step-icon" :title="stepStatusLabel(node.status)" aria-hidden="true">
            {{ stepIcon(node.status, index) }}
          </span>
          <div class="step-copy">
            <strong>{{ node.label || `步骤 ${index + 1}` }}</strong>
            <span v-if="node.detail">{{ node.detail }}</span>
          </div>
        </div>
      </div>

      <pre class="output-terminal" aria-label="验证终端输出" aria-live="polite"><code>{{ terminalText }}</code></pre>
    </details>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'

const MIN_WORKERS = 1
const MAX_WORKERS = 8
const DEFAULT_WORKERS = 2

const props = defineProps({
  output: { type: [String, Array, Object], default: null },
  running: { type: Boolean, default: false },
  error: { type: String, default: '' }
})

const emit = defineEmits(['verify'])

const workersInput = ref(DEFAULT_WORKERS)

const outputOpen = computed(() => props.running || Boolean(props.output) || Boolean(props.error))

function clampWorkers(value) {
  const num = Number(value)
  if (!Number.isFinite(num)) return DEFAULT_WORKERS
  return Math.min(MAX_WORKERS, Math.max(MIN_WORKERS, Math.floor(num)))
}

function normalizeWorkers() {
  workersInput.value = clampWorkers(workersInput.value)
}

function handleVerify() {
  if (props.running) return
  normalizeWorkers()
  emit('verify', { workers: workersInput.value })
}

const resultObject = computed(() =>
  props.output && typeof props.output === 'object' && !Array.isArray(props.output) ? props.output : null
)

const stepNodes = computed(() => {
  if (Array.isArray(props.output)) {
    return props.output.map((item, index) => {
      if (typeof item === 'string') {
        return { key: `line-${index}`, label: item, status: 'pending', detail: '' }
      }
      return {
        key: item.key || `step-${index}`,
        label: item.label || item.name || `步骤 ${index + 1}`,
        status: item.status || 'pending',
        detail: item.detail || item.message || ''
      }
    })
  }

  const nodes = resultObject.value?.nodes
  return Array.isArray(nodes) ? nodes : []
})

const summaryText = computed(() => {
  if (props.running) {
    return '正在执行 verify_log_pipeline_full…'
  }

  if (!props.output && !props.error) {
    return '尚未执行'
  }

  if (resultObject.value) {
    const status = resultObject.value.success ? '通过' : '失败'
    const exitCode = resultObject.value.exit_code ?? '—'
    const duration = resultObject.value.duration_ms ?? '—'
    return `${status} / exit=${exitCode} / ${duration}ms`
  }

  if (props.error) {
    return '失败'
  }

  return '已完成'
})

const terminalText = computed(() => {
  if (props.running && !props.output) {
    return '正在启动全链路验证，请稍候…'
  }

  if (!props.output && !props.error) {
    return '点击「一键验证」后，这里会展示 verify_log_pipeline_full 的终端输出。'
  }

  if (typeof props.output === 'string') {
    return props.output.trim() || '验证命令未返回输出。'
  }

  if (Array.isArray(props.output)) {
    const lines = props.output.map((item) => {
      if (typeof item === 'string') return item
      const label = item.label || item.name || '步骤'
      const status = item.status ? `[${item.status}]` : ''
      const detail = item.detail || item.message || ''
      return [label, status, detail].filter(Boolean).join(' — ')
    })
    return lines.join('\n') || '验证命令未返回输出。'
  }

  const stdout = resultObject.value?.stdout || ''
  const stderr = resultObject.value?.stderr || ''
  const merged = [stdout.trim(), stderr.trim()].filter(Boolean).join('\n\n[stderr]\n')

  if (merged) return merged

  if (props.error) {
    return props.error
  }

  return resultObject.value?.error || '验证命令未返回输出。'
})

function stepTone(status) {
  const map = {
    success: 'success',
    healthy: 'success',
    failed: 'danger',
    down: 'danger',
    running: 'info',
    degraded: 'warning',
    warning: 'warning',
    pending: 'neutral',
    unknown: 'neutral'
  }
  return map[String(status || '').toLowerCase()] || 'neutral'
}

function stepStatusLabel(status) {
  const map = {
    success: '通过',
    healthy: '正常',
    failed: '失败',
    down: '异常',
    running: '检测中',
    degraded: '降级',
    warning: '警告',
    pending: '等待',
    unknown: '未知'
  }
  return map[String(status || '').toLowerCase()] || '未知'
}

function stepIcon(status, index) {
  const normalized = String(status || '').toLowerCase()
  const map = {
    success: '✓',
    healthy: '✓',
    failed: '!',
    down: '!',
    running: '…',
    degraded: '!',
    warning: '!',
    pending: String(index + 1)
  }
  return map[normalized] || String(index + 1)
}
</script>

<style scoped>
.verify-panel {
  margin-bottom: 0;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.panel-header h2 {
  margin: 0;
}

.panel-desc {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.verify-toolbar {
  display: flex;
  align-items: flex-end;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.workers-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.workers-input {
  width: 72px;
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-size: 14px;
  font-variant-numeric: tabular-nums;
  color: var(--color-text);
  transition: border-color 0.15s ease, opacity 0.15s ease;
}

.workers-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.workers-input:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}

.verify-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.verify-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.verify-btn:disabled {
  cursor: not-allowed;
  opacity: 0.75;
}

.verify-btn.is-loading {
  opacity: 0.9;
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .verify-btn {
    transition: none;
  }

  .verify-btn:hover:not(:disabled) {
    transform: none;
  }

  .btn-spinner {
    animation: none;
    border-top-color: rgba(255, 255, 255, 0.65);
  }
}

.verify-error {
  margin-bottom: var(--spacing-md);
  padding: 12px 14px;
  border: 1px solid #fecaca;
  border-radius: var(--radius-md);
  background: var(--color-danger-bg);
  color: #991b1b;
  font-size: 13px;
  line-height: 1.5;
}

.output-fold {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: #1a1d23;
  overflow: hidden;
}

.output-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  user-select: none;
  list-style: none;
}

.output-summary::-webkit-details-marker {
  display: none;
}

.summary-meta {
  font-size: 12px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  color: var(--color-text-muted);
}

.steps-list {
  display: grid;
  gap: 8px;
  padding: 12px 14px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.step-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 52px;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.step-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 30px;
  width: 30px;
  height: 30px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 700;
}

.step-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.step-copy strong {
  font-size: 13px;
  color: var(--color-text);
}

.step-copy span {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.35;
}

.step-success {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.step-success .step-icon {
  background: var(--color-success);
  color: #fff;
}

.step-danger {
  background: var(--color-danger-bg);
  border-color: #fecaca;
}

.step-danger .step-icon {
  background: var(--color-danger);
  color: #fff;
}

.step-info {
  background: var(--color-info-bg);
  border-color: #bae6fd;
}

.step-info .step-icon {
  background: var(--color-primary);
  color: #fff;
}

.step-warning {
  background: var(--color-warning-bg);
  border-color: #fde68a;
}

.step-warning .step-icon {
  background: var(--color-warning);
  color: #fff;
}

.step-neutral .step-icon {
  background: #f3f4f6;
  color: var(--color-text-secondary);
}

.output-terminal {
  margin: 0;
  padding: 14px 16px;
  font-family: ui-monospace, 'Cascadia Code', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #a8b3c5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 280px;
  overflow-y: auto;
}

.output-terminal code {
  font-family: inherit;
}
</style>
