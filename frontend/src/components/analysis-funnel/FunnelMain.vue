<template>
  <section class="page-section funnel-main">
    <header class="funnel-main__header">
      <h2>主漏斗</h2>
      <span v-if="isMock" class="funnel-main__mock">演示数据</span>
    </header>

    <EmptyState
      v-if="error"
      compact
      title="漏斗加载失败"
      :description="error"
    >
      <button type="button" class="funnel-main__retry" @click="refresh">重试</button>
    </EmptyState>

    <template v-else>
      <FunnelChart
        :data="chartData"
        :loading="loading"
        height="320px"
        placeholder="五步转化漏斗：page_view → product_click → add_to_cart → checkout_click → pay_button_click"
      />

      <ul class="funnel-main__steps" role="list">
        <li
          v-for="(step, index) in funnelSteps"
          :key="step.key"
          class="funnel-main__step"
          :class="[
            `funnel-main__step--${step.severity}`,
            { 'funnel-main__step--active': step.key === activeStepKey }
          ]"
        >
          <button
            type="button"
            class="funnel-main__step-btn"
            :aria-pressed="step.key === activeStepKey"
            @click="selectStep(step.key)"
          >
            <span class="funnel-main__step-index">{{ index + 1 }}</span>
            <span class="funnel-main__step-body">
              <span class="funnel-main__step-label">{{ step.label }}</span>
              <span class="funnel-main__step-meta tabular-nums">
                <span class="funnel-main__step-count">{{ formatNumber(step.count) }}</span>
                <span v-if="index > 0" class="funnel-main__step-rate">
                  转化 {{ formatPercent(step.conversionRate) }}
                  <span v-if="step.dropoutRate != null" class="funnel-main__step-drop">
                    · 流失 {{ formatPercent(step.dropoutRate) }}
                  </span>
                </span>
                <span v-else class="funnel-main__step-rate">入口</span>
              </span>
            </span>
          </button>
        </li>
      </ul>
    </template>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import FunnelChart from '../common/charts/FunnelChart.vue'
import EmptyState from '../common/EmptyState.vue'
import { useMetrics } from '../../composables/useMetrics.js'
import { formatNumber, formatPercent } from '../../utils/format.js'

const CHART_COLORS = {
  primary: '#3b82f6',
  warning: '#d97706',
  danger: '#dc2626'
}

/** 五步漏斗顺序（对齐后端 field_catalog.funnel_steps） */
const FUNNEL_STEPS = [
  { key: 'page_view', label: '页面浏览' },
  { key: 'product_click', label: '商品点击' },
  { key: 'add_to_cart', label: '加入购物车' },
  { key: 'checkout_click', label: '结算点击' },
  { key: 'pay_button_click', label: '支付点击' }
]

/** 步骤间流失率阈值：≥35% 标橙，≥55% 标红 */
const DROPOUT_WARNING = 0.35
const DROPOUT_DANGER = 0.55

const emit = defineEmits(['select-step'])

const { data, loading, error, refresh, isMock } = useMetrics({ template: 'behavior_funnel' })

const activeStepKey = ref(null)
const autoSelected = ref(false)

const funnelSteps = computed(() => {
  const bucketMap = new Map((data.value?.buckets ?? []).map((b) => [b.key, b]))

  return FUNNEL_STEPS.map((step, index) => {
    const bucket = bucketMap.get(step.key) ?? { count: 0, extra: {} }
    const count = Number(bucket.count ?? 0)

    let conversionRate = null
    if (bucket.extra?.conversion_rate != null) {
      conversionRate = Number(bucket.extra.conversion_rate)
    } else if (index > 0) {
      const prevCount = Number(bucketMap.get(FUNNEL_STEPS[index - 1].key)?.count ?? 0)
      if (prevCount > 0) conversionRate = count / prevCount
    }

    let dropoutRate = null
    if (index > 0 && conversionRate != null) {
      dropoutRate = Math.max(0, 1 - conversionRate)
    }

    let severity = 'normal'
    if (dropoutRate != null) {
      if (dropoutRate >= DROPOUT_DANGER) severity = 'danger'
      else if (dropoutRate >= DROPOUT_WARNING) severity = 'warning'
    }

    return {
      ...step,
      count,
      conversionRate,
      dropoutRate,
      severity
    }
  })
})

const chartData = computed(() =>
  funnelSteps.value.map((step) => ({
    name: step.label,
    value: step.count,
    itemStyle: { color: stepColor(step) }
  }))
)

function stepColor(step) {
  if (step.severity === 'danger') return CHART_COLORS.danger
  if (step.severity === 'warning') return CHART_COLORS.warning
  return CHART_COLORS.primary
}

function selectStep(key) {
  activeStepKey.value = key
  emit('select-step', key)
}

watch(
  funnelSteps,
  (steps) => {
    if (!steps.length || autoSelected.value) return

    const abnormal = steps.find(
      (s) => s.severity === 'danger' || s.severity === 'warning'
    )
    const target = abnormal?.key ?? steps[steps.length - 1]?.key
    if (target) {
      autoSelected.value = true
      selectStep(target)
    }
  },
  { immediate: true }
)

watch(
  () => data.value,
  () => {
    autoSelected.value = false
    activeStepKey.value = null
  }
)
</script>

<style scoped>
.funnel-main__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.funnel-main__header h2 {
  margin: 0;
  color: #f2f5f7;
  font-size: 13px;
  font-weight: 900;
}

.funnel-main__mock {
  flex-shrink: 0;
  padding: 2px 8px;
  border: 1px solid rgba(178, 139, 90, 0.42);
  border-radius: 2px;
  background: rgba(178, 139, 90, 0.12);
  color: #c3a06d;
  font-size: 11px;
  font-weight: 900;
  line-height: 1.4;
}

.funnel-main__retry {
  margin-top: var(--spacing-sm);
  padding: 6px 14px;
  border: 1px solid rgba(111, 158, 172, 0.42);
  border-radius: 2px;
  background: rgba(111, 158, 172, 0.1);
  color: #c9dde2;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  clip-path: polygon(0 0, calc(100% - 9px) 0, 100% 100%, 0 100%);
}

.funnel-main__steps {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  margin: var(--spacing-md) 0 0;
  padding: 0;
  list-style: none;
}

.funnel-main__step-btn {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  width: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(185, 196, 207, 0.16);
  border-radius: 2px;
  background:
    linear-gradient(90deg, rgba(111, 158, 172, 0.035) 0 1px, transparent 1px 28px),
    rgba(7, 10, 14, 0.58);
  background-size: 28px 28px;
  color: #dce4eb;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 180ms ease,
    box-shadow 180ms ease,
    transform 180ms ease;
}

.funnel-main__step-btn:hover {
  transform: translateY(-1px);
  border-color: rgba(111, 158, 172, 0.42);
  box-shadow: 0 0 0 1px rgba(111, 158, 172, 0.18);
}

.funnel-main__step--active .funnel-main__step-btn {
  border-color: rgba(111, 158, 172, 0.62);
  background: rgba(111, 158, 172, 0.12);
  box-shadow: inset 3px 0 0 #6f9eac;
}

.funnel-main__step--warning .funnel-main__step-btn {
  border-color: rgba(178, 139, 90, 0.46);
}

.funnel-main__step--danger .funnel-main__step-btn {
  border-color: rgba(185, 106, 97, 0.5);
}

.funnel-main__step-index {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
  background: rgba(185, 196, 207, 0.12);
  color: #aab4bf;
  font-size: 11px;
  font-weight: 900;
}

.funnel-main__step--warning .funnel-main__step-index {
  background: rgba(178, 139, 90, 0.18);
  color: #c3a06d;
}

.funnel-main__step--danger .funnel-main__step-index {
  background: rgba(185, 106, 97, 0.18);
  color: #d4877c;
}

.funnel-main__step-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.funnel-main__step-label {
  font-size: 13px;
  font-weight: 900;
  color: #f2f5f7;
}

.funnel-main__step-meta {
  font-size: 12px;
  color: #aab4bf;
}

.funnel-main__step-count {
  font-weight: 900;
  color: #e6edf3;
  margin-right: 6px;
}

.funnel-main__step--warning .funnel-main__step-drop {
  color: #c3a06d;
  font-weight: 900;
}

.funnel-main__step--danger .funnel-main__step-drop {
  color: #d4877c;
  font-weight: 900;
}

@media (prefers-reduced-motion: reduce) {
  .funnel-main__step-btn {
    transition: none;
  }

  .funnel-main__step-btn:hover {
    transform: none;
  }
}
</style>
