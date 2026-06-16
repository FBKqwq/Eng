import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

/**
 * 统一轮询组合式函数
 * @param {() => Promise<void>} fetcher 轮询回调
 * @param {number} intervalMs 间隔毫秒，默认 30s
 * @param {boolean} immediate 是否立即执行
 */
export function usePolling(fetcher, intervalMs = 30000, immediate = true) {
  const loading = ref(false)
  const error = ref(null)
  let timer = null

  async function run() {
    loading.value = true
    error.value = null
    try {
      await fetcher()
    } catch (err) {
      error.value = err?.message || '轮询失败'
    } finally {
      loading.value = false
    }
  }

  function start() {
    stop()
    if (immediate) run()
    timer = setInterval(run, intervalMs)
  }

  function stop() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  onMounted(start)
  onBeforeUnmount(stop)

  return { loading, error, run, start, stop }
}

/**
 * 可动态调整间隔的轮询
 */
export function usePollingWithInterval(fetcher, intervalRef, immediate = true) {
  const { loading, error, run, start, stop } = usePolling(fetcher, intervalRef.value, immediate)

  watch(intervalRef, () => {
    start()
  })

  return { loading, error, run, start, stop }
}
