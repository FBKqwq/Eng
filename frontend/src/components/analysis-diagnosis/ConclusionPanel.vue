<template>
  <div class="conclusion-panel">
    <EmptyState
      v-if="!result"
      compact
      title="暂无诊断结论"
      description="LangGraph 推断链路运行后，严重度、置信度、根因结论与证据会在此联动更新"
    />

    <template v-else>
      <div class="gauge-row page-grid page-grid-2">
        <div class="gauge-slot">
          <p class="gauge-label">严重度</p>
          <GaugeChart
            title="严重度"
            :value="severityGauge.value"
            :min="0"
            :max="100"
            height="200px"
            placeholder="等待严重度数据"
          />
          <p class="gauge-caption tabular-nums">{{ severityGauge.label }}</p>
        </div>
        <div class="gauge-slot">
          <p class="gauge-label">置信度</p>
          <GaugeChart
            title="置信度"
            :value="confidencePercent"
            :min="0"
            :max="100"
            unit="%"
            height="200px"
            placeholder="等待置信度数据"
          />
          <p v-if="degraded" class="gauge-caption gauge-caption--muted">规则判定区间 0.35~0.45</p>
        </div>
      </div>

      <div class="meta-row">
        <span class="anomaly-badge" :class="anomalyToneClass">{{ anomalyLabel }}</span>
        <span
          v-for="service in affectedServices"
          :key="service"
          class="service-tag"
        >{{ service }}</span>
        <span v-if="!affectedServices.length" class="service-tag service-tag--muted">暂无受影响服务</span>
      </div>

      <article class="root-cause-card" :class="{ 'root-cause-card--degraded': degraded }">
        <header class="root-cause-card__header">
          <h3>根因结论</h3>
          <span v-if="degraded" class="rule-badge">基于规则判定</span>
        </header>
        <p class="root-cause-card__headline">{{ headline }}</p>
        <ul v-if="reasoningPoints.length" class="root-cause-card__points">
          <li v-for="(point, index) in reasoningPoints" :key="index">{{ point }}</li>
        </ul>
        <p v-else class="root-cause-card__empty-points">暂无结构化推理依据要点</p>
      </article>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import GaugeChart from '../common/charts/GaugeChart.vue'
import EmptyState from '../common/EmptyState.vue'

const props = defineProps({
  /** 诊断结果对象（diagnosis 字段解包后）；null 时显示空态 */
  result: { type: Object, default: null },
  /** 规则降级标记：显示灰色角标与置信度区间文案 */
  degraded: { type: Boolean, default: false }
})

const SEVERITY_GAUGE_MAP = {
  low: { value: 25, label: '低 (low)' },
  medium: { value: 50, label: '中 (medium)' },
  high: { value: 75, label: '高 (high)' },
  critical: { value: 100, label: '严重 (critical)' }
}

const ANOMALY_TYPE_LABELS = {
  service_timeout: '服务超时',
  error_spike: '错误激增',
  latency_spike: '延迟尖峰',
  dependency_failure: '依赖故障',
  resource_exhaustion: '资源耗尽',
  security_anomaly: '安全异常'
}

const severityGauge = computed(() => {
  const key = String(props.result?.severity ?? '').toLowerCase()
  return SEVERITY_GAUGE_MAP[key] ?? { value: 50, label: key || '未知' }
})

const confidencePercent = computed(() => {
  const raw = props.result?.confidence
  if (raw === null || raw === undefined || Number.isNaN(Number(raw))) {
    return props.degraded ? 40 : null
  }
  const num = Number(raw)
  return num <= 1 ? Math.round(num * 100) : Math.round(num)
})

const anomalyLabel = computed(() => {
  const type = props.result?.anomaly_type
  if (!type) return '未知异常类型'
  const key = String(type).toLowerCase()
  if (ANOMALY_TYPE_LABELS[key]) return ANOMALY_TYPE_LABELS[key]
  return String(type).replace(/_/g, ' ')
})

const anomalyToneClass = computed(() => {
  const key = String(props.result?.severity ?? 'medium').toLowerCase()
  if (key === 'critical' || key === 'high') return 'tone-danger'
  if (key === 'low') return 'tone-info'
  return 'tone-warning'
})

const affectedServices = computed(() => {
  const list = props.result?.affected_services
  return Array.isArray(list) ? list.filter(Boolean) : []
})

const headline = computed(() => {
  const r = props.result
  if (r?.summary) return r.summary
  if (r?.title) return r.title
  const text = r?.root_cause
  if (!text) return '暂无根因结论'
  const firstSentence = text.split(/[。！？\n]/)[0]?.trim()
  return firstSentence || text
})

const reasoningPoints = computed(() => {
  const r = props.result
  const points = []

  const candidates = r?.root_cause_candidates
  if (Array.isArray(candidates)) {
    for (const item of candidates) {
      const text = item?.reason || item?.cause
      if (text) points.push(text)
    }
  }

  const matchedRules = r?.context_summary?.matched_rules
  if (Array.isArray(matchedRules)) {
    for (const rule of matchedRules) {
      if (rule) points.push(`匹配规则：${rule}`)
    }
  }

  if (!points.length && r?.root_cause) {
    const sentences = r.root_cause
      .split(/[。！？\n]/)
      .map((s) => s.trim())
      .filter(Boolean)
    if (sentences.length > 1) {
      return sentences.slice(1)
    }
  }

  return points
})
</script>

<style scoped>
.conclusion-panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.gauge-label {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.gauge-caption {
  margin: 4px 0 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
  text-align: center;
}

.gauge-caption--muted {
  font-weight: 500;
  font-size: 12px;
  color: var(--color-text-muted);
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.anomaly-badge {
  display: inline-block;
  padding: 8px 14px;
  border-radius: var(--radius-md);
  font-size: 16px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: 0.01em;
}

.anomaly-badge.tone-info {
  background: var(--color-info-bg);
  color: var(--color-info);
  border: 1px solid var(--color-info);
}

.anomaly-badge.tone-warning {
  background: var(--color-warning-bg);
  color: var(--color-warning);
  border: 1px solid var(--color-warning);
}

.anomaly-badge.tone-danger {
  background: var(--color-danger-bg);
  color: var(--color-danger);
  border: 1px solid var(--color-danger);
}

.service-tag {
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  font-size: 12px;
  color: var(--color-text-secondary);
}

.service-tag--muted {
  color: var(--color-text-muted);
  border-style: dashed;
}

.root-cause-card {
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
  border-left: 3px solid var(--color-primary);
  transition: box-shadow 180ms ease;
}

.root-cause-card--degraded {
  border-left-color: var(--color-text-muted);
}

.root-cause-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: var(--spacing-sm);
}

.root-cause-card__header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.rule-badge {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-muted);
}

.root-cause-card__headline {
  margin: 0 0 var(--spacing-sm);
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.5;
}

.root-cause-card__points {
  margin: 0;
  padding-left: 1.2em;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.root-cause-card__empty-points {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-muted);
}

@media (prefers-reduced-motion: reduce) {
  .root-cause-card {
    transition: none;
  }
}
</style>
