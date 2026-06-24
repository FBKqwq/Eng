import { ref, computed, watch, onUnmounted, toValue } from 'vue'
import { useTimeRange } from './useTimeRange.js'
import {
  USE_MOCK,
  queryTraffic,
  queryErrors,
  queryLatency,
  queryBehaviorFunnel,
  querySecurity,
  queryInfraHealth,
  queryGroupedLogs
} from '../api/metrics.js'

const RANGE_DEBOUNCE_MS = 300

/** @typedef {'traffic' | 'errors' | 'latency' | 'behavior_funnel' | 'security' | 'infra_health'} MetricsTemplate */

/** 六类业务聚合模板枚举（与 metrics.js / logTypeMeta.chartTemplates 对齐） */
export const METRICS_TEMPLATES = Object.freeze([
  'traffic',
  'errors',
  'latency',
  'behavior_funnel',
  'security',
  'infra_health'
])

/** @type {Record<MetricsTemplate, (payload: Record<string, unknown>) => Promise<{ data?: object }>>} */
const TEMPLATE_QUERY_MAP = {
  traffic: queryTraffic,
  errors: queryErrors,
  latency: queryLatency,
  behavior_funnel: queryBehaviorFunnel,
  security: querySecurity,
  infra_health: queryInfraHealth
}

/**
 * 统一 metrics 聚合查询：时间窗联动、loading/error 状态、mock 感知。
 * @param {{ template: MetricsTemplate, logType?: string, extraFilters?: Record<string, unknown>, immediate?: boolean }} options
 * @returns {{ data: import('vue').Ref<object|null>, loading: import('vue').Ref<boolean>, error: import('vue').Ref<string|null>, refresh: () => Promise<void>, isMock: import('vue').ComputedRef<boolean> }}
 */
export function useMetrics({ template, groupBy, logType, extraFilters, immediate = true } = {}) {
  const { range } = useTimeRange()

  const data = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const isMock = computed(() => USE_MOCK === true)

  let fetchGeneration = 0
  let unmounted = false
  let rangeDebounceTimer = null

  const queryFn = groupBy ? queryGroupedLogs : TEMPLATE_QUERY_MAP[template]

  function buildPayload() {
    const resolvedExtraFilters = toValue(extraFilters)
    return {
      start_time: new Date(range.value.start).toISOString(),
      end_time: new Date(range.value.end).toISOString(),
      ...(logType ? { log_types: [logType] } : {}),
      ...(groupBy ? { group_by: groupBy } : {}),
      ...(resolvedExtraFilters && typeof resolvedExtraFilters === 'object'
        ? resolvedExtraFilters
        : {})
    }
  }

  async function refresh() {
    if (unmounted) return

    if (!queryFn) {
      error.value = `未知的聚合配置: ${template || groupBy || '未指定'}`
      data.value = null
      loading.value = false
      return
    }

    const generation = ++fetchGeneration
    loading.value = true
    error.value = null

    try {
      const res = await queryFn(buildPayload())
      if (unmounted || generation !== fetchGeneration) return

      data.value = res.data ?? null
    } catch (e) {
      if (unmounted || generation !== fetchGeneration) return

      error.value = e.message ?? '聚合查询失败'
      data.value = null
    } finally {
      if (!unmounted && generation === fetchGeneration) {
        loading.value = false
      }
    }
  }

  watch(
    [range, () => JSON.stringify(toValue(extraFilters) ?? {})],
    () => {
      if (rangeDebounceTimer != null) {
        clearTimeout(rangeDebounceTimer)
      }
      rangeDebounceTimer = setTimeout(() => {
        rangeDebounceTimer = null
        if (unmounted) return
        refresh()
      }, RANGE_DEBOUNCE_MS)
    },
    { deep: true, immediate }
  )

  onUnmounted(() => {
    unmounted = true
    fetchGeneration += 1
    if (rangeDebounceTimer != null) {
      clearTimeout(rangeDebounceTimer)
      rangeDebounceTimer = null
    }
  })

  return {
    data,
    loading,
    error,
    refresh,
    isMock
  }
}
