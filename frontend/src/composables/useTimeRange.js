import { ref, computed, provide, inject } from 'vue'

const TIME_RANGE_KEY = Symbol('timeRange')

const PRESETS = [
  { label: '近 15 分钟', value: '15m', minutes: 15 },
  { label: '近 1 小时', value: '1h', minutes: 60 },
  { label: '近 6 小时', value: '6h', minutes: 360 },
  { label: '近 24 小时', value: '24h', minutes: 1440 },
  { label: '自定义', value: 'custom', minutes: null }
]

function createTimeRangeState() {
  const preset = ref('1h')
  const customStart = ref(null)
  const customEnd = ref(null)

  const range = computed(() => {
    const now = Date.now()
    if (preset.value === 'custom' && customStart.value && customEnd.value) {
      return { start: customStart.value, end: customEnd.value, preset: 'custom' }
    }
    const item = PRESETS.find((p) => p.value === preset.value) || PRESETS[1]
    return {
      start: now - item.minutes * 60 * 1000,
      end: now,
      preset: item.value
    }
  })

  function setPreset(value) {
    preset.value = value
  }

  function setCustomRange(start, end) {
    customStart.value = start
    customEnd.value = end
    preset.value = 'custom'
  }

  return { presets: PRESETS, preset, range, setPreset, setCustomRange }
}

/** 在 Layout 顶层提供全局时间窗口 */
export function provideTimeRange() {
  const state = createTimeRangeState()
  provide(TIME_RANGE_KEY, state)
  return state
}

/** 页面/组件注入全局时间窗口 */
export function useTimeRange() {
  const state = inject(TIME_RANGE_KEY, null)
  if (!state) {
    return createTimeRangeState()
  }
  return state
}
