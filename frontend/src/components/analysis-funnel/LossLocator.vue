<template>
  <section class="page-section loss-locator">
    <header class="loss-locator__header">
      <h2>流失定位</h2>
      <span v-if="showMockBadge" class="loss-locator__mock">演示数据</span>
    </header>

    <p v-if="!selectedStep" class="loss-hint">
      请在主漏斗中选中异常步骤，查看该时段内相关错误码 Top N
    </p>

    <template v-else>
      <p class="loss-hint">
        当前步骤：<strong>{{ stepLabel }}</strong> · 应用日志错误码分布（同一时间窗）
      </p>

      <EmptyState
        v-if="error"
        compact
        title="错误码分布加载失败"
        :description="error"
      >
        <button type="button" class="loss-locator__retry" @click="refresh">重试</button>
      </EmptyState>

      <BarChart
        v-else
        :categories="errorCategories"
        :series="errorSeries"
        horizontal
        :loading="loading"
        height="220px"
        placeholder="该步骤时段内暂无错误码聚合数据"
      />

      <button
        type="button"
        class="jump-btn"
        :disabled="!selectedStep"
        @click="goToApplicationLogs"
      >
        查看应用日志
      </button>
    </template>
  </section>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import BarChart from '../common/charts/BarChart.vue'
import EmptyState from '../common/EmptyState.vue'
import { useMetrics } from '../../composables/useMetrics.js'

const STEP_LABELS = {
  page_view: '页面浏览',
  product_click: '商品点击',
  add_to_cart: '加入购物车',
  checkout_click: '结算点击',
  pay_button_click: '支付点击'
}

const TOP_N = 10

const props = defineProps({
  /** 漏斗步骤 event_type 键 */
  selectedStep: { type: String, default: '' }
})

const router = useRouter()

const { data, loading, error, refresh, isMock } = useMetrics({
  template: 'errors',
  extraFilters: { top_n: TOP_N },
  immediate: false
})

const showMockBadge = computed(() => isMock.value && Boolean(props.selectedStep))

const stepLabel = computed(() => STEP_LABELS[props.selectedStep] || props.selectedStep || '—')

const errorBuckets = computed(() => data.value?.buckets ?? [])

const errorCategories = computed(() =>
  errorBuckets.value.map((b) => (b.key == null || b.key === '' ? '未知' : String(b.key)))
)

const errorSeries = computed(() => [
  {
    name: '错误次数',
    data: errorBuckets.value.map((b) => Number(b.count ?? 0))
  }
])

const primaryErrorCode = computed(() => errorCategories.value[0] ?? '')

watch(
  () => props.selectedStep,
  (step) => {
    if (step) refresh()
  }
)

/**
 * 跳转监控页预置筛选 query 约定（F2 对齐）：
 * - log_levels / error_codes 为逗号分隔，监控页后续可解析为 LogQueryRequest 数组字段
 * - funnel_step 保留漏斗上下文，不影响当前监控页查询
 */
function goToApplicationLogs() {
  if (!props.selectedStep) return

  const query = {
    log_levels: 'ERROR',
    funnel_step: props.selectedStep
  }

  if (primaryErrorCode.value) {
    query.error_codes = primaryErrorCode.value
  }

  router.push({ path: '/monitor/application', query })
}
</script>

<style scoped>
.loss-locator__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.loss-locator__header h2 {
  margin: 0;
  color: #f2f5f7;
  font-size: 13px;
  font-weight: 900;
}

.loss-locator__mock {
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

.loss-hint {
  margin: 0 0 var(--spacing-sm);
  font-size: 12px;
  color: #aab4bf;
  line-height: 1.5;
}

.loss-hint strong {
  color: #f2f5f7;
  font-weight: 900;
}

.loss-locator__retry {
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

.jump-btn {
  align-self: flex-start;
  margin-top: var(--spacing-sm);
  padding: 6px 14px;
  border: 1px solid rgba(111, 158, 172, 0.48);
  border-radius: 2px;
  background: rgba(111, 158, 172, 0.1);
  color: #c9dde2;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 150ms ease;
  clip-path: polygon(0 0, calc(100% - 9px) 0, 100% 100%, 0 100%);
}

.jump-btn:hover:not(:disabled) {
  background: rgba(111, 158, 172, 0.18);
  color: #f2f5f7;
}

.jump-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
