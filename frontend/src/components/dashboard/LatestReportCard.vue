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
        <span class="latest-report-card__dot" :class="riskToneClass" aria-hidden="true" />
        <div class="latest-report-card__risk-text">
          <span class="latest-report-card__risk-label">风险等级</span>
          <strong class="latest-report-card__risk-value tabular-nums">{{ riskLabel }}</strong>
        </div>
      </div>

      <p class="latest-report-card__summary">{{ displayReport.summary || '暂无摘要' }}</p>

      <footer class="latest-report-card__meta">
        <span class="latest-report-card__type">{{ reportTypeLabel }}</span>
        <time class="latest-report-card__time tabular-nums">{{ formatTime(displayReport.created_at) }}</time>
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
.latest-report-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.latest-report-card__header h2 {
  margin: 0;
}

.latest-report-card__body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
  cursor: pointer;
  transition: box-shadow 180ms ease, transform 180ms ease;
}

.latest-report-card__body:hover,
.latest-report-card__body:focus-visible {
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
  outline: none;
}

.latest-report-card__risk {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.latest-report-card__dot {
  flex-shrink: 0;
  width: 14px;
  height: 14px;
  border-radius: 50%;
}

.latest-report-card__dot.tone-low {
  background: var(--color-success);
  box-shadow: 0 0 0 4px var(--color-success-bg);
}

.latest-report-card__dot.tone-medium {
  background: var(--color-warning);
  box-shadow: 0 0 0 4px var(--color-warning-bg);
}

.latest-report-card__dot.tone-high {
  background: var(--color-danger);
  box-shadow: 0 0 0 4px var(--color-danger-bg);
}

.latest-report-card__risk-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.latest-report-card__risk-label {
  font-size: 12px;
  color: var(--color-text-muted);
}

.latest-report-card__risk-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
}

.latest-report-card__summary {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-secondary);
}

.latest-report-card__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  font-size: 12px;
  color: var(--color-text-muted);
}

.latest-report-card__type {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
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
