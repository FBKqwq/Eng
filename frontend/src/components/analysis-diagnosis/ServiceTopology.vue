<template>
  <div class="topology-block">
    <div class="topology-graph" :class="{ 'is-placeholder': isPlaceholder }">
      <div class="topology-track" role="list" aria-label="受影响服务拓扑">
        <template v-for="(node, index) in displayNodes" :key="node.name">
          <span
            class="topology-node"
            role="listitem"
            :class="{ abnormal: node.abnormal }"
            :title="node.abnormal ? '异常服务' : undefined"
          >
            {{ node.name }}
          </span>
          <span
            v-if="index < displayNodes.length - 1"
            class="topology-edge"
            :class="{ 'edge-abnormal': node.abnormal || displayNodes[index + 1].abnormal }"
            aria-hidden="true"
          >
            <span class="edge-line" />
            <span class="edge-head">›</span>
          </span>
        </template>
      </div>
      <p class="topology-note">{{ topologyNote }}</p>
    </div>

    <div class="similar-errors">
      <div class="similar-errors__header">
        <p class="similar-errors__label">同类错误频次</p>
        <span v-if="isBurst" class="burst-badge">集中爆发</span>
        <span v-else-if="similarTotal > 0" class="total-badge tabular-nums">共 {{ similarTotal }} 次</span>
      </div>
      <BarChart
        :categories="chartCategories"
        :series="chartSeries"
        height="120px"
        :placeholder="chartPlaceholder"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import BarChart from '../common/charts/BarChart.vue'
import { formatTime } from '../../utils/format.js'

/** 电商调用链默认顺序（无 affected_services 时作占位拓扑） */
const DEFAULT_CHAIN = ['gateway', 'order-service', 'payment-service', 'inventory-service']

const props = defineProps({
  /** affected_services：异常/受影响服务名列表 */
  affectedServices: { type: Array, default: () => [] },
  /**
   * get_similar_errors 结果摘要：
   * { total, error_code?, time_histogram[{ key, count }], by_service[{ key, count }] }
   */
  similarErrors: { type: Object, default: null }
})

const affectedSet = computed(() => {
  const names = props.affectedServices || []
  return new Set(names.map((name) => String(name).trim()).filter(Boolean))
})

const isPlaceholder = computed(() => affectedSet.value.size === 0)

function isAbnormalService(name) {
  if (!affectedSet.value.size) return false
  const normalized = String(name).trim()
  return (
    affectedSet.value.has(normalized) ||
    affectedSet.value.has(normalized.replace(/-service$/, '-svc')) ||
    affectedSet.value.has(normalized.replace(/-svc$/, '-service'))
  )
}

const displayNodes = computed(() =>
  DEFAULT_CHAIN.map((name) => ({
    name,
    abnormal: isAbnormalService(name)
  }))
)

const topologyNote = computed(() => {
  if (isPlaceholder.value) {
    return 'affected_services 简化拓扑，异常服务红色脉冲（等待诊断结果）'
  }
  const list = [...affectedSet.value].join('、')
  return `受影响服务：${list}`
})

const histogramBuckets = computed(() => {
  const buckets = props.similarErrors?.time_histogram
  return Array.isArray(buckets) ? buckets : []
})

const similarTotal = computed(() => {
  const total = props.similarErrors?.total
  if (typeof total === 'number' && total >= 0) return total
  return histogramBuckets.value.reduce((sum, bucket) => sum + (bucket.count || 0), 0)
})

const isBurst = computed(() => {
  const counts = histogramBuckets.value.map((bucket) => bucket.count || 0)
  if (counts.length < 2) return false
  const max = Math.max(...counts)
  const avg = counts.reduce((sum, count) => sum + count, 0) / counts.length
  return max >= Math.max(3, avg * 2)
})

function formatBucketLabel(key) {
  if (!key) return '—'
  const formatted = formatTime(key)
  if (formatted === String(key)) {
    const date = new Date(key)
    if (!Number.isNaN(date.getTime())) {
      return date.toLocaleString('zh-CN', {
        hour12: false,
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
  return formatted.replace(/\d{4}\//, '').replace(/:\d{2}$/, '')
}

const chartCategories = computed(() =>
  histogramBuckets.value.map((bucket) => formatBucketLabel(bucket.key))
)

const chartSeries = computed(() => {
  if (!histogramBuckets.value.length) return []
  const code = props.similarErrors?.error_code
  return [
    {
      name: code ? String(code) : '频次',
      data: histogramBuckets.value.map((bucket) => bucket.count || 0)
    }
  ]
})

const chartPlaceholder = computed(() => {
  if (props.similarErrors?.error) {
    return `同类错误统计不可用：${props.similarErrors.error}`
  }
  return 'get_similar_errors 时间分布迷你图（等待诊断上下文）'
})
</script>

<style scoped>
.topology-block {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.topology-graph {
  padding: var(--industrial-panel-padding);
  border: var(--industrial-border-width) solid var(--industrial-border-color);
  border-radius: 0;
  background: var(--industrial-white);
  transition: border-color 0.3s ease, box-shadow 0.2s ease-out;
}

.topology-graph.is-placeholder {
  border-style: dashed;
}

.topology-track {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.topology-node {
  padding: 8px 14px;
  border-radius: 0;
  border: 1px solid var(--industrial-border-color);
  background: var(--industrial-light-gray);
  font-size: 12px;
  font-weight: 500;
  color: var(--industrial-dark-gray);
  position: relative;
  clip-path: polygon(
    0 0,
    calc(100% - var(--industrial-cut-size)) 0,
    100% var(--industrial-cut-size),
    100% 100%,
    0 100%
  );
  transition:
    border-color 0.3s ease,
    color 0.3s ease,
    background-color 0.3s ease,
    box-shadow 0.2s ease-out;
}

.topology-node.abnormal {
  border-color: #dc2626;
  color: #991b1b;
  background: rgba(220, 38, 38, 0.06);
  box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.1);
  animation: pulse-abnormal 3s ease-in-out infinite;
}

.topology-edge {
  display: inline-flex;
  align-items: center;
  width: 28px;
  color: var(--industrial-medium-gray);
  opacity: 0.65;
  transition: color 0.3s ease, opacity 0.3s ease;
}

.topology-edge.edge-abnormal {
  color: var(--industrial-red);
  opacity: 0.85;
}

.edge-line {
  flex: 1;
  height: 1px;
  background: currentColor;
}

.edge-head {
  margin-left: -2px;
  font-size: 16px;
  line-height: 1;
}

.topology-note {
  margin: var(--spacing-sm) 0 0;
  font-size: 11px;
  color: var(--industrial-medium-gray);
  text-align: center;
}

.similar-errors__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.similar-errors__label {
  margin: 0;
  font-size: 12px;
  font-weight: 500;
  color: var(--industrial-dark-gray);
}

.burst-badge {
  padding: 2px 8px;
  border-radius: 0;
  font-size: 11px;
  font-weight: 600;
  color: var(--industrial-red);
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid var(--industrial-red);
}

.total-badge {
  font-size: 11px;
  color: var(--industrial-medium-gray);
  font-family: var(--font-mono);
}

@keyframes pulse-abnormal {
  0%,
  100% {
    opacity: 0.95;
    box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.1);
  }
  50% {
    opacity: 0.85;
    box-shadow: 0 0 0 4px rgba(220, 38, 38, 0.05);
  }
}

@media (prefers-reduced-motion: reduce) {
  .topology-node.abnormal {
    animation: none;
  }
}
</style>
