import { ref, onMounted, onUnmounted } from 'vue'

/**
 * 统一轮询封装：挂载后自动启动，卸载时清除定时器
 * @param {() => void | Promise<void>} fn 轮询回调
 * @param {number} intervalMs 间隔毫秒，默认 30s
 * @param {boolean} immediate 启动时是否立即执行一次
 * @returns {{ start: () => void, stop: () => void, run: () => Promise<void>, loading: import('vue').Ref<boolean>, error: import('vue').Ref<string|null> }}
 */
export function usePolling(fn, intervalMs = 30000, immediate = true) {
  const loading = ref(false)
  const error = ref(null)
  let timer = null

  async function run() {
    loading.value = true
    error.value = null
    try {
      await fn()
    } catch (err) {
      error.value = err?.message ?? '轮询失败'
    } finally {
      loading.value = false
    }
  }

  function start() {
    stop()
    if (immediate) {
      run()
    }
    timer = setInterval(run, intervalMs)
  }

  function stop() {
    if (timer != null) {
      clearInterval(timer)
      timer = null
    }
  }

  onMounted(start)
  onUnmounted(stop)

  return { start, stop, run, loading, error }
}
