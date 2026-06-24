<template>
  <section class="page-section latest-report-card">
    <header class="latest-report-card__header">
      <h2>最新体检结论</h2>
    </header>

    <EmptyState
      v-if="error"
      compact
      title="体检结论加载失败"
      :description="error"
    >
      <button type="button" class="latest-report-card__retry" @click="fetchReport">重试</button>
    </EmptyState>

    <div v-else-if="loading && !displayReport" class="latest-report-card__loading">
      <span class="latest-report-card__skeleton latest-report-card__skeleton--gauge" />
      <span class="latest-report-card__skeleton latest-report-card__skeleton--text" />
    </div>

    <EmptyState
      v-else-if="!displayReport"
      compact
      title="暂无周期报告"
      description="智能分析尚未产出体检报告"
    >
      <router-link to="/analysis/reports" class="latest-report-card__link">前往报告页</router-link>
    </EmptyState>

    <article
      v-else
      class="latest-report-card__body"
      role="button"
      tabindex="0"
      @click="goReports"
      @keydown.enter="goReports"
    >
      <div class="latest-report-card__risk">
        <div class="latest-report-card__risk-orbit" :class="riskToneClass" aria-hidden="true">
          <span class="latest-report-card__risk-code">RISK</span>
        </div>
        <div class="latest-report-card__risk-text">
          <span class="latest-report-card__risk-label">风险等级</span>
          <strong class="latest-report-card__risk-value tabular-nums">{{ riskLabel }}</strong>
        </div>
      </div>

      <p class="latest-report-card__summary">{{ displayReport.summary || '暂无摘要' }}</p>

      <footer class="latest-report-card__meta">
        <div>
          <span class="latest-report-card__type">{{ reportTypeLabel }}</span>
          <time class="latest-report-card__time tabular-nums">{{ formatTime(displayReport.created_at) }}</time>
        </div>
        <span class="latest-report-card__action">查看完整报告 →</span>
      </footer>
    </article>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import EmptyState from '../common/EmptyState.vue'
import { getRecentReports } from '../../api/reports.js'
import { formatTime } from '../../utils/format.js'

const router = useRouter()

const latestReport = ref(null)
const loading = ref(false)
const error = ref('')

const RISK_LABELS = {
  low: '低风险',
  medium: '中风险',
  high: '高风险'
}

const displayReport = computed(() => latestReport.value)

const riskLevel = computed(() => String(displayReport.value?.risk_level ?? 'medium').toLowerCase())

const riskLabel = computed(() => RISK_LABELS[riskLevel.value] ?? displayReport.value?.risk_level ?? '未知')

const riskToneClass = computed(() => {
  if (riskLevel.value === 'high') return 'tone-high'
  if (riskLevel.value === 'low') return 'tone-low'
  return 'tone-medium'
})

const reportTypeLabel = computed(() => {
  const type = displayReport.value?.report_type
  if (type === 'periodic') return '周期体检'
  if (type === 'event') return '事件诊断'
  return type || '分析报告'
})

function goReports() {
  router.push('/analysis/reports')
}

async function fetchReport() {
  loading.value = true
  error.value = ''
  try {
    const res = await getRecentReports({ limit: 1 })
    const list = Array.isArray(res?.data?.items) ? res.data.items : []
    latestReport.value = list[0] ?? null
  } catch (err) {
    latestReport.value = null
    error.value = err?.error?.message || err?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

fetchReport()
</script>

<style scoped>
.latest-report-card {
  padding: 14px;
  border: 1px solid rgba(125, 211, 252, 0.28);
  border-radius: 0;
  background: linear-gradient(135deg, rgba(4, 14, 27, 0.78), rgba(12, 31, 51, 0.7));
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.025);
}

.latest-report-card:hover {
  border-color: rgba(125, 211, 252, 0.5);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
  transform: none;
}

.latest-report-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: 8px;
}

.latest-report-card__header h2 {
  margin: 0;
  color: #f8fbff;
  font-size: 15px;
  letter-spacing: 0.05em;
}

.latest-report-card__header h2::before {
  display: inline-block;
  width: 4px;
  height: 14px;
  margin-right: 8px;
  background: #38bdf8;
  transform: skewX(-16deg);
  vertical-align: -2px;
  content: '';
}

.latest-report-card__body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 188px;
  padding: 14px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 0;
  background: rgba(5, 18, 32, 0.54);
  cursor: pointer;
  transition: box-shadow 180ms ease, transform 180ms ease;
}

.latest-report-card__body:hover,
.latest-report-card__body:focus-visible {
  border-color: rgba(125, 211, 252, 0.42);
  box-shadow: inset 4px 0 0 #38bdf8;
  transform: none;
  outline: none;
}

.latest-report-card__risk {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.latest-report-card__risk-orbit {
  flex-shrink: 0;
  display: grid;
  place-items: center;
  width: 66px;
  height: 66px;
  border-radius: 50%;
  border: 6px solid;
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.12em;
}

.latest-report-card__risk-orbit.tone-low {
  border-color: #22c55e;
  color: #86efac;
  box-shadow: 0 0 24px rgba(34, 197, 94, 0.16);
}

.latest-report-card__risk-orbit.tone-medium {
  border-color: #f59e0b;
  color: #fcd34d;
  box-shadow: 0 0 24px rgba(245, 158, 11, 0.16);
}

.latest-report-card__risk-orbit.tone-high {
  border-color: #ef4444;
  color: #fca5a5;
  box-shadow: 0 0 24px rgba(239, 68, 68, 0.18);
}

.latest-report-card__risk-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.latest-report-card__risk-label {
  font-size: 12px;
  color: #91a9bf;
}

.latest-report-card__risk-value {
  font-size: 25px;
  font-weight: 900;
  color: #f8fbff;
  line-height: 1.2;
}

.latest-report-card__summary {
  margin: 0;
  min-height: 46px;
  padding-left: 10px;
  border-left: 2px solid rgba(56, 189, 248, 0.52);
  font-size: 13px;
  line-height: 1.55;
  color: #c4d3df;
}

.latest-report-card__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  font-size: 11px;
  color: #91a9bf;
}

.latest-report-card__type {
  padding: 2px 8px;
  margin-right: 10px;
  border-radius: 0;
  background: rgba(56, 189, 248, 0.09);
  border: 1px solid rgba(56, 189, 248, 0.24);
}

.latest-report-card__action {
  color: #7dd3fc;
  font-weight: 800;
}

.latest-report-card__link {
  font-size: 13px;
  color: var(--color-primary);
  text-decoration: none;
}

.latest-report-card__link:hover {
  text-decoration: underline;
}

.latest-report-card__retry {
  margin-top: var(--spacing-xs);
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-size: 13px;
  cursor: pointer;
}

.latest-report-card__loading {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.latest-report-card__skeleton {
  display: block;
  border-radius: var(--radius-sm);
  background: linear-gradient(
    90deg,
    var(--color-bg) 25%,
    var(--color-border) 50%,
    var(--color-bg) 75%
  );
  background-size: 200% 100%;
  animation: latest-report-shimmer 1.2s ease-in-out infinite;
}

.latest-report-card__skeleton--gauge {
  height: 56px;
}

.latest-report-card__skeleton--text {
  height: 72px;
}

@keyframes latest-report-shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .latest-report-card__body {
    transition: none;
  }

  .latest-report-card__skeleton {
    animation: none;
    background: var(--color-bg);
  }
}
</style>
