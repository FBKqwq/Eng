import { ref, computed, provide, inject } from 'vue'

const TIME_RANGE_KEY = Symbol('timeRange')

/** 全局时间窗口预设项（5 项） */
const PRESETS = [
  { label: '近 15 分钟', value: '15m', minutes: 15 },
  { label: '近 1 小时', value: '1h', minutes: 60 },
  { label: '近 6 小时', value: '6h', minutes: 360 },
  { label: '近 24 小时', value: '24h', minutes: 1440 },
  { label: '自定义', value: 'custom', minutes: null }
]

const DEFAULT_PRESET = '1h'

function resolvePresetMinutes(value) {
  const item = PRESETS.find((p) => p.value === value && p.minutes != null)
  if (item) return item.minutes
  return PRESETS.find((p) => p.value === DEFAULT_PRESET).minutes
}

function createTimeRangeState() {
  const preset = ref(DEFAULT_PRESET)
  const customStart = ref(null)
  const customEnd = ref(null)

  /** 可用于 API 查询的 { start, end }，随 preset 变化自动重算 */
  const range = computed(() => {
    const now = Date.now()
    if (preset.value === 'custom' && customStart.value != null && customEnd.value != null) {
      return { start: customStart.value, end: customEnd.value }
    }
    const minutes = resolvePresetMinutes(preset.value)
    return {
      start: now - minutes * 60 * 1000,
      end: now
    }
  })

  function setPreset(value) {
    preset.value = value
  }

  /** 设置自定义起止时间并切换至 custom 预设 */
  function setCustomRange(start, end) {
    customStart.value = start
    customEnd.value = end
    preset.value = 'custom'
  }

  return { presets: PRESETS, preset, range, setPreset, setCustomRange }
}

/** 在 Layout 顶层调用，向子树注入全局时间窗口 */
export function provideTimeRange() {
  const state = createTimeRangeState()
  provide(TIME_RANGE_KEY, state)
  return state
}

/** 页面/组件消费全局时间窗口；无注入时返回独立本地状态 */
export function useTimeRange() {
  const state = inject(TIME_RANGE_KEY, null)
  if (!state) {
    return createTimeRangeState()
  }
  return state
}
