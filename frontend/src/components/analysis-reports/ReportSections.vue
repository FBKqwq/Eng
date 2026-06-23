<template>
  <div class="report-sections" :aria-busy="loading">
    <header v-if="report" class="report-sections__header">
      <span v-if="degraded" class="degraded-badge">统计模式</span>
    </header>

    <div v-if="loading && !report" class="report-sections__skeleton" aria-hidden="true">
      <div v-for="n in 3" :key="n" class="skeleton-card" />
    </div>

    <EmptyState
      v-else-if="!report"
      compact
      title="暂无报告拆解"
      description="从左侧时间轴选择一份报告查看结构化结论"
    />

    <template v-else>
      <article v-for="section in displaySections" :key="section.title" class="section-card">
        <h3>{{ section.title }}</h3>
        <ul v-if="section.points.length">
          <li v-for="(point, idx) in section.points" :key="`${section.title}-${idx}`">{{ point }}</li>
        </ul>
        <p v-else class="section-empty">本节暂无要点</p>
      </article>

      <footer class="report-sections__footer">
        <h4 class="footer-title">生成质量</h4>
        <div class="footer-stage-ring">
          <DiagnosisStageRing :node-trace="nodeTrace" :degraded="degraded" />
        </div>
      </footer>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import EmptyState from '../common/EmptyState.vue'
import DiagnosisStageRing from '../analysis-diagnosis/DiagnosisStageRing.vue'

const props = defineProps({
  /** getReportDetail → data.report */
  report: { type: Object, default: null },
  loading: { type: Boolean, default: false }
})

const SECTION_TITLES = ['总体结论', '异常发现', '业务洞察']

const degraded = computed(() => Boolean(props.report?.degraded))

const nodeTrace = computed(() => {
  const trace = props.report?.node_trace
  return Array.isArray(trace) ? trace : []
})

const displaySections = computed(() => {
  if (!props.report) return []

  const structured = props.report.sections
  if (Array.isArray(structured) && structured.length) {
    return structured.map((section) => ({
      title: section.title || '未命名章节',
      points: normalizePoints(section.points ?? section.items ?? section.content)
    }))
  }

  const summaryPoints = normalizePoints(props.report.summary)
  const findingPoints = normalizePoints(props.report.key_findings)
  const insightPoints = normalizePoints(props.report.recommendations)

  return [
    { title: SECTION_TITLES[0], points: summaryPoints },
    { title: SECTION_TITLES[1], points: findingPoints },
    { title: SECTION_TITLES[2], points: insightPoints }
  ]
})

function normalizePoints(value) {
  if (value == null || value === '') return []
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (typeof item === 'string') return item.trim()
        if (item && typeof item === 'object') {
          return item.text || item.summary || item.message || JSON.stringify(item)
        }
        return String(item)
      })
      .filter(Boolean)
  }
  if (typeof value === 'string') return [value.trim()].filter(Boolean)
  return [String(value)]
}
</script>

<style scoped>
.report-sections {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.report-sections__header {
  display: flex;
  justify-content: flex-end;
}

.degraded-badge {
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--color-text-muted);
  color: var(--color-bg);
  font-size: 11px;
  line-height: 1.5;
}

.section-card {
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
  transition: box-shadow 180ms ease;
}

.section-card:hover {
  box-shadow: var(--shadow-sm);
}

.section-card h3 {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.section-card ul {
  margin: 0;
  padding-left: 1.2em;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.55;
}

.section-empty {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-muted);
}

.report-sections__footer {
  margin-top: var(--spacing-sm);
  padding: var(--spacing-md);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.footer-title {
  margin: 0 0 var(--spacing-sm);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: none;
}

.footer-stage-ring :deep(.stage-ring) {
  padding: var(--spacing-sm);
  border-style: solid;
  background: transparent;
}

.footer-stage-ring :deep(.step) {
  min-width: 56px;
  padding: 0 4px;
}

.footer-stage-ring :deep(.ring) {
  width: 26px;
  height: 26px;
}

.footer-stage-ring :deep(.name) {
  font-size: 11px;
  max-width: 64px;
}

.footer-stage-ring :deep(.duration) {
  font-size: 10px;
}

.report-sections__skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.skeleton-card {
  height: 88px;
  border-radius: var(--radius-md);
  background: linear-gradient(
    90deg,
    var(--color-bg) 25%,
    var(--color-border) 50%,
    var(--color-bg) 75%
  );
  background-size: 200% 100%;
  animation: sections-shimmer 1.2s ease-in-out infinite;
}

@keyframes sections-shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .section-card {
    transition: none;
  }

  .skeleton-card {
    animation: none;
    background: var(--color-bg);
  }
}
</style>
