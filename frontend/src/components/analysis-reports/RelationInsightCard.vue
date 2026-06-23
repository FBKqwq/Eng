<template>
  <section v-if="shouldRender" class="relation-insight" aria-label="隐藏关系发现">
    <header class="relation-insight__header">
      <h3>隐藏关系发现</h3>
      <span v-if="showMockBadge" class="relation-insight__mock">演示数据</span>
    </header>

    <article
      v-for="(item, index) in displayRelations"
      :key="`${item.description}-${index}`"
      class="relation-card"
    >
      <p v-if="item.description" class="relation-card__desc">{{ item.description }}</p>

      <div class="relation-flow">
        <div class="metric-box">
          <p class="metric-name">{{ item.leftLabel }}</p>
          <TrendChart
            :categories="item.leftChart.categories"
            :series="item.leftChart.series"
            height="88px"
            :placeholder="item.leftChart.placeholder"
          />
        </div>

        <div class="relation-arrow" aria-hidden="true">
          <span class="relation-arrow__line" />
          <span class="relation-arrow__head">→</span>
        </div>

        <div class="metric-box">
          <p class="metric-name">{{ item.rightLabel }}</p>
          <TrendChart
            :categories="item.rightChart.categories"
            :series="item.rightChart.series"
            height="88px"
            :placeholder="item.rightChart.placeholder"
          />
        </div>
      </div>

      <footer v-if="item.confidence != null" class="relation-card__footer">
        <span class="confidence-label">置信度</span>
        <span class="confidence-value tabular-nums">{{ formatConfidence(item.confidence) }}</span>
      </footer>
    </article>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import TrendChart from '../common/charts/TrendChart.vue'
import { USE_MOCK } from '../../api/reports.js'

const props = defineProps({
  /** report.relations / relation_chain 数组 */
  relations: { type: Array, default: () => [] },
  /** 父级控制是否展示整块；无有效关系数据时组件自身也不渲染 */
  visible: { type: Boolean, default: true }
})

const ENTITY_LABELS = {
  traffic_peak: '请求高峰',
  pay_fail: '支付失败',
  traffic: '流量',
  errors: '错误率',
  latency: '耗时',
  request_peak: '请求高峰',
  payment_fail: '支付失败上升'
}

const DEMO_RELATIONS = [
  {
    relation_type: 'temporal_correlation',
    description: '流量高峰后支付失败率上升',
    entities: ['traffic_peak', 'pay_fail'],
    confidence: 0.82,
    left_metric: '请求高峰',
    right_metric: '支付失败上升',
    left: {
      categories: ['10:00', '10:15', '10:30', '10:45'],
      values: [42, 58, 120, 95]
    },
    right: {
      categories: ['10:00', '10:15', '10:30', '10:45'],
      values: [2, 3, 12, 15]
    }
  }
]

const showMockBadge = computed(
  () => USE_MOCK === true && (!Array.isArray(props.relations) || props.relations.length === 0)
)

const displayRelations = computed(() => {
  const source =
    Array.isArray(props.relations) && props.relations.length
      ? props.relations
      : USE_MOCK
        ? DEMO_RELATIONS
        : []
  return source.map(normalizeRelation).filter(Boolean)
})

const shouldRender = computed(
  () => props.visible !== false && displayRelations.value.length > 0
)

function entityLabel(key) {
  if (!key) return ''
  const normalized = String(key).toLowerCase()
  return ENTITY_LABELS[normalized] || String(key).replace(/_/g, ' ')
}

function formatConfidence(value) {
  const pct = Math.round(Math.max(0, Math.min(1, Number(value))) * 100)
  return `${pct}%`
}

function parseSeries(raw, label) {
  if (!raw) {
    return {
      categories: [],
      series: [],
      placeholder: `${label}：等待指标序列`
    }
  }

  if (Array.isArray(raw.categories) && (Array.isArray(raw.values) || Array.isArray(raw.data))) {
    const values = raw.values || raw.data
    if (raw.categories.length && values.length) {
      return {
        categories: raw.categories,
        series: [{ name: label, data: values, area: true }],
        placeholder: ''
      }
    }
  }

  const buckets = raw.buckets || raw.series?.[0]?.data
  if (Array.isArray(buckets) && buckets.length) {
    const categories = []
    const values = []
    for (const bucket of buckets) {
      const key = bucket.key_as_string ?? bucket.key ?? bucket.label
      const value = bucket.doc_count ?? bucket.value ?? bucket.count
      if (key == null || value == null) continue
      categories.push(String(key))
      values.push(Number(value))
    }
    if (categories.length) {
      return {
        categories,
        series: [{ name: label, data: values, area: true }],
        placeholder: ''
      }
    }
  }

  return {
    categories: [],
    series: [],
    placeholder: `${label}：等待指标序列`
  }
}

function normalizeRelation(raw) {
  if (!raw || typeof raw !== 'object') return null

  const leftLabel =
    raw.left_metric ||
    raw.left?.label ||
    entityLabel(raw.entities?.[0]) ||
    '左指标'
  const rightLabel =
    raw.right_metric ||
    raw.right?.label ||
    entityLabel(raw.entities?.[1]) ||
    '右指标'

  return {
    description: raw.description || '',
    confidence: typeof raw.confidence === 'number' ? raw.confidence : null,
    leftLabel,
    rightLabel,
    leftChart: parseSeries(raw.left_series || raw.left || raw.series?.left, leftLabel),
    rightChart: parseSeries(raw.right_series || raw.right || raw.series?.right, rightLabel)
  }
}
</script>

<style scoped>
.relation-insight {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px dashed var(--color-border);
}

.relation-insight__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
}

.relation-insight__header h3 {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
}

.relation-insight__mock {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 11px;
  line-height: 1.4;
}

.relation-card {
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
}

.relation-card:hover {
  border-color: var(--color-primary-muted, var(--color-border));
  box-shadow: var(--shadow-sm, 0 1px 3px rgba(15, 23, 42, 0.06));
  transform: translateY(-1px);
}

.relation-card__desc {
  margin: 0 0 var(--spacing-sm);
  font-size: 13px;
  line-height: 1.55;
  color: var(--color-text-secondary);
}

.relation-flow {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  gap: var(--spacing-sm);
}

.metric-box {
  min-width: 0;
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
}

.metric-name {
  margin: 0 0 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text);
  text-align: center;
}

.relation-arrow {
  display: flex;
  align-items: center;
  gap: 2px;
  color: var(--color-primary);
  font-weight: 700;
}

.relation-arrow__line {
  display: block;
  width: 12px;
  height: 2px;
  border-radius: 1px;
  background: currentColor;
  opacity: 0.45;
}

.relation-arrow__head {
  font-size: 18px;
  line-height: 1;
}

.relation-card__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  margin-top: var(--spacing-sm);
  padding-top: var(--spacing-sm);
  border-top: 1px dashed var(--color-border);
}

.confidence-label {
  font-size: 11px;
  color: var(--color-text-muted);
}

.confidence-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-primary);
}

@media (max-width: 720px) {
  .relation-flow {
    grid-template-columns: 1fr;
    justify-items: stretch;
  }

  .relation-arrow {
    justify-content: center;
    transform: rotate(90deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .relation-card {
    transition: none;
  }

  .relation-card:hover {
    transform: none;
  }
}
</style>
