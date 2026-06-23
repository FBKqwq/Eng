<template>
  <Teleport to="body">
    <Transition name="drawer-fade">
      <div
        v-if="visible"
        class="alert-drawer-root"
        role="presentation"
        @click.self="emit('close')"
      >
        <aside
          class="alert-drawer"
          role="dialog"
          aria-modal="true"
          aria-label="预警详情"
        >
          <header class="alert-drawer__header">
            <div class="alert-drawer__title-block">
              <h3>{{ alert?.title || '预警详情' }}</h3>
              <div v-if="alert" class="alert-drawer__meta">
                <SeverityBadge
                  :level="alert.severity"
                  :label="formatSeverity(alert.severity)"
                />
                <span class="meta-service">{{ alert.affected_service || '未知服务' }}</span>
              </div>
            </div>
            <button type="button" class="alert-drawer__close" aria-label="关闭" @click="emit('close')">
              ×
            </button>
          </header>

          <div v-if="!alert" class="alert-drawer__empty">
            <EmptyState compact title="未选择预警" description="点击列表行查看详情" />
          </div>

          <template v-else>
            <div class="alert-drawer__sections">
              <section
                v-for="block in explanationSections"
                :key="block.title"
                class="detail-section"
              >
                <h4>{{ block.title }}</h4>
                <ul v-if="Array.isArray(block.content)" class="detail-list">
                  <li v-for="(line, idx) in block.content" :key="idx">{{ line }}</li>
                </ul>
                <p v-else>{{ block.content }}</p>
              </section>
            </div>

            <section class="evidence-section">
              <h4>关联证据</h4>
              <ul v-if="displayEvidences.length" class="evidence-list" role="list">
                <li v-for="item in displayEvidences" :key="item.id" class="evidence-item">
                  <span class="evidence-item__summary">{{ item.summary }}</span>
                  <time class="evidence-item__time tabular-nums">{{ formatTime(item.timestamp) }}</time>
                </li>
              </ul>
              <p v-else class="evidence-empty">
                暂无结构化证据条目（累计 {{ formatNumber(alert.evidence_count ?? 0) }} 条关联日志）
              </p>
            </section>

            <section v-if="reportLink" class="report-section">
              <h4>关联报告</h4>
              <router-link :to="reportPath" class="report-link">
                {{ reportLink.title || '查看周期体检报告' }}
              </router-link>
            </section>

            <footer class="alert-drawer__footer">
              <button type="button" class="diagnosis-btn" @click="handleDiagnose">
                发起深度诊断
              </button>
            </footer>
          </template>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import EmptyState from '../common/EmptyState.vue'
import SeverityBadge from '../common/SeverityBadge.vue'
import { formatTime, formatNumber } from '../../utils/format.js'

const props = defineProps({
  visible: { type: Boolean, default: false },
  alert: { type: Object, default: null },
  /** alert_chain 三段解释：{ phenomenon, impact, suggestion }；字符串或字符串数组 */
  explanation: { type: Object, default: () => ({}) },
  /** [{ id, summary, timestamp }] */
  evidences: { type: Array, default: () => [] },
  /** { reportId, title } */
  reportLink: { type: Object, default: null }
})

const emit = defineEmits(['close', 'diagnose'])

const SEVERITY_LABELS = {
  low: '低',
  medium: '中',
  high: '高',
  critical: '严重'
}

const ALERT_TYPE_LABELS = {
  error_rate_spike: '错误率异常',
  latency_degradation: '耗时升高',
  security_risk: '安全风险',
  infra_health: '基础设施异常',
  traffic_anomaly: '流量波动',
  pay_fail: '支付失败',
  error_spike: '错误激增',
  latency_spike: '延迟异常'
}

const explanationSections = computed(() => {
  const fallback = buildFallbackExplanation(props.alert)
  const src = props.explanation ?? {}

  return [
    {
      title: '现象',
      content: normalizeSection(src.phenomenon, fallback.phenomenon)
    },
    {
      title: '影响',
      content: normalizeSection(src.impact, fallback.impact)
    },
    {
      title: '建议',
      content: normalizeSection(src.suggestion, fallback.suggestion)
    }
  ]
})

const displayEvidences = computed(() =>
  Array.isArray(props.evidences) ? props.evidences : []
)

const reportPath = computed(() => {
  const id = props.reportLink?.reportId ?? props.reportLink?.report_id
  if (!id) return '/analysis/reports'
  return { path: '/analysis/reports', query: { report_id: id } }
})

function normalizeSection(value, fallback) {
  if (Array.isArray(value) && value.length) return value
  if (typeof value === 'string' && value.trim()) return value.trim()
  return fallback
}

function buildFallbackExplanation(alert) {
  if (!alert) {
    return {
      phenomenon: '—',
      impact: '—',
      suggestion: '—'
    }
  }

  const typeLabel =
    ALERT_TYPE_LABELS[alert.alert_type] ?? String(alert.alert_type || '未知类型').replace(/_/g, ' ')
  const service = alert.affected_service || '未知服务'
  const severityLabel = formatSeverity(alert.severity)
  const count = alert.evidence_count ?? 0

  const phenomenon =
    alert.title?.trim() ||
    `检测到「${typeLabel}」，影响服务 ${service}，严重等级 ${severityLabel}。`

  const impact = [
    `受影响服务：${service}`,
    `严重度：${severityLabel}（${alert.severity || 'medium'}）`,
    `已累计 ${count} 条关联证据日志`
  ]

  let suggestion = '建议纳入常规巡检跟进，关注异常是否持续。'
  const sev = String(alert.severity || '').toLowerCase()
  if (sev === 'high' || sev === 'critical') {
    suggestion = '建议立即排查相关服务依赖、近期变更与错误日志样本，必要时触发深度诊断。'
  } else if (sev === 'medium') {
    suggestion = '建议关注异常趋势，确认是否为偶发或持续恶化，并核对关联报告结论。'
  }

  return { phenomenon, impact, suggestion }
}

function formatSeverity(level) {
  if (!level) return '—'
  return SEVERITY_LABELS[level.toLowerCase()] ?? level
}

function handleDiagnose() {
  if (!props.alert?.alert_id) return
  emit('diagnose', props.alert.alert_id)
}
</script>

<style scoped>
.alert-drawer-root {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
  background: rgb(15 23 42 / 0.28);
}

.alert-drawer {
  display: flex;
  flex-direction: column;
  width: min(420px, 100vw);
  height: 100%;
  padding: var(--spacing-md);
  border-left: 1px solid var(--color-border);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
  overflow-y: auto;
  animation: drawer-slide-in 300ms ease-out;
}

.alert-drawer__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--color-border);
}

.alert-drawer__title-block h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
}

.alert-drawer__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.meta-service {
  font-size: 12px;
  color: var(--color-text-muted);
}

.alert-drawer__close {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text-secondary);
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
}

.alert-drawer__close:hover {
  background: var(--color-border);
}

.detail-section {
  margin-bottom: var(--spacing-md);
}

.detail-section h4,
.evidence-section h4,
.report-section h4 {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
}

.detail-section p,
.evidence-empty {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.55;
}

.detail-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.55;
}

.detail-list li + li {
  margin-top: 4px;
}

.evidence-section,
.report-section {
  margin-bottom: var(--spacing-md);
  padding-top: var(--spacing-sm);
  border-top: 1px dashed var(--color-border);
}

.evidence-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.evidence-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
}

.evidence-item__summary {
  font-size: 13px;
  color: var(--color-text);
  line-height: 1.45;
}

.evidence-item__time {
  font-size: 11px;
  color: var(--color-text-muted);
}

.report-link {
  font-size: 13px;
  color: var(--color-primary);
  text-decoration: none;
}

.report-link:hover {
  text-decoration: underline;
}

.alert-drawer__footer {
  margin-top: auto;
  padding-top: var(--spacing-md);
}

.diagnosis-btn {
  width: 100%;
  padding: 10px 16px;
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: var(--color-surface);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 150ms ease, transform 150ms ease;
}

.diagnosis-btn:hover {
  opacity: 0.92;
  transform: translateY(-1px);
}

.drawer-fade-enter-active,
.drawer-fade-leave-active {
  transition: opacity 250ms ease;
}

.drawer-fade-enter-from,
.drawer-fade-leave-to {
  opacity: 0;
}

@keyframes drawer-slide-in {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .alert-drawer {
    animation: none;
  }

  .drawer-fade-enter-active,
  .drawer-fade-leave-active {
    transition: none;
  }

  .diagnosis-btn {
    transition: none;
  }

  .diagnosis-btn:hover {
    transform: none;
  }
}
</style>
