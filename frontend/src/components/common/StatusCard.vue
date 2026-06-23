<template>
  <article
    class="status-card"
    :class="[`tone-${resolvedTone}`, { 'is-loading': loading }]"
    :aria-busy="loading || undefined"
    :aria-label="loading ? `${title} 加载中` : undefined"
  >
    <div v-if="loading" class="status-skeleton" aria-hidden="true">
      <div class="skeleton-line skeleton-line--title" />
      <div class="skeleton-line skeleton-line--badge" />
      <div class="skeleton-line skeleton-line--detail" />
      <div class="skeleton-line skeleton-line--meta" />
    </div>

    <template v-else>
      <header class="status-header">
        <h3 class="status-title">{{ title }}</h3>
        <span class="status-badge">{{ resolvedLabel }}</span>
      </header>

      <p v-if="resolvedDetail" class="status-detail">{{ resolvedDetail }}</p>

      <dl v-if="hasMeta" class="status-meta">
        <div v-if="hasContainer">
          <dt>容器</dt>
          <dd>{{ container }}</dd>
        </div>
        <div v-if="hasPort">
          <dt>端口</dt>
          <dd class="tabular-nums">{{ port }}</dd>
        </div>
      </dl>

      <slot />
    </template>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  /** healthy | degraded | down | unknown | offline；兼容 running/ok/green 等别名 */
  status: { type: String, default: '' },
  /** 健康详情或副文案 */
  detail: { type: String, default: '' },
  /** F1 占位兼容：等同 detail */
  description: { type: String, default: '' },
  port: { type: [String, Number], default: '' },
  container: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  /** F1 占位兼容：无 status 时直接展示 */
  statusLabel: { type: String, default: '' },
  /** F1 占位兼容：success | warning | danger | neutral */
  tone: { type: String, default: '' }
})

const STATUS_LABELS = {
  healthy: '正常',
  degraded: '降级',
  down: '异常',
  unknown: '未知',
  offline: '离线'
}

const STATUS_TONES = {
  healthy: 'success',
  degraded: 'warning',
  down: 'danger',
  unknown: 'neutral',
  offline: 'offline'
}

function normalizeStatus(value) {
  const raw = String(value || '').toLowerCase()

  if (['healthy', 'ok', 'up', 'running', 'online', 'active', 'success', 'green'].includes(raw)) {
    return 'healthy'
  }
  if (['degraded', 'warning', 'yellow', 'pending'].includes(raw)) {
    return 'degraded'
  }
  if (['down', 'error', 'failed', 'unhealthy', 'danger', 'red', 'stopped'].includes(raw)) {
    return 'down'
  }
  if (raw === 'offline') {
    return 'offline'
  }
  if (!raw) {
    return ''
  }
  return 'unknown'
}

const normalizedStatus = computed(() => normalizeStatus(props.status))

const resolvedTone = computed(() => {
  if (props.tone && !props.status) {
    return props.tone
  }
  if (normalizedStatus.value) {
    return STATUS_TONES[normalizedStatus.value] || 'neutral'
  }
  return props.tone || 'neutral'
})

const resolvedLabel = computed(() => {
  if (props.statusLabel && !props.status) {
    return props.statusLabel
  }
  if (normalizedStatus.value) {
    return STATUS_LABELS[normalizedStatus.value] || '未知'
  }
  return props.statusLabel || '未知'
})

const resolvedDetail = computed(() => props.detail || props.description || '')

const hasContainer = computed(() => props.container !== null && props.container !== undefined && props.container !== '')
const hasPort = computed(() => props.port !== null && props.port !== undefined && props.port !== '')
const hasMeta = computed(() => hasContainer.value || hasPort.value)
</script>

<style scoped>
.status-card {
  position: relative;
  min-height: 174px;
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.18s ease-out, transform 0.18s ease-out;
}

.status-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  background: var(--status-accent, var(--color-border));
}

.status-card:hover:not(.is-loading) {
  box-shadow: var(--shadow-card);
  transform: translateY(-1px);
}

.tone-success {
  --status-accent: var(--color-success);
}

.tone-warning {
  --status-accent: var(--color-warning);
}

.tone-danger {
  --status-accent: var(--color-danger);
}

.tone-neutral {
  --status-accent: var(--color-text-muted);
}

.tone-offline {
  --status-accent: var(--color-info);
}

.status-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-sm);
}

.status-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.3;
}

.status-badge {
  flex-shrink: 0;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;
}

.tone-success .status-badge {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.tone-warning .status-badge {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.tone-danger .status-badge {
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.tone-neutral .status-badge {
  background: var(--color-bg);
  color: var(--color-text-secondary);
}

.tone-offline .status-badge {
  background: var(--color-info-bg);
  color: var(--color-info);
}

.status-detail {
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.status-meta {
  display: grid;
  gap: 12px;
  margin: 14px 0 0;
}

.status-meta dt {
  margin-bottom: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.status-meta dd {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: var(--color-text);
  overflow-wrap: anywhere;
}

.status-skeleton {
  display: grid;
  gap: 10px;
}

.skeleton-line {
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--color-bg) 25%, #e5e7eb 50%, var(--color-bg) 75%);
  background-size: 200% 100%;
  animation: status-skeleton-shimmer 1.2s ease-in-out infinite;
}

.skeleton-line--title {
  width: 42%;
  height: 20px;
}

.skeleton-line--badge {
  width: 56px;
  height: 22px;
  justify-self: end;
  margin-top: -30px;
}

.skeleton-line--detail {
  width: 88%;
  height: 14px;
}

.skeleton-line--meta {
  width: 64%;
  height: 14px;
}

@keyframes status-skeleton-shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .status-card {
    transition: none;
  }

  .status-card:hover:not(.is-loading) {
    transform: none;
  }

  .skeleton-line {
    animation: none;
    background: var(--color-bg);
  }
}
</style>
