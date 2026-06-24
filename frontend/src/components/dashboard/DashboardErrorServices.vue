<template>
  <DashboardFrame title="Top 错误服务" subtitle="按错误数">
    <table class="service-table">
      <thead><tr><th>服务名称</th><th>错误数</th><th>占比</th><th>趋势</th></tr></thead>
      <tbody>
        <tr v-for="(item, index) in rows" :key="item.key">
          <td>{{ item.key }}</td>
          <td class="tabular-nums">{{ formatNumber(item.count) }}</td>
          <td class="tabular-nums">{{ item.share }}%</td>
          <td><span class="spark" :style="{ '--spark-width': `${Math.max(15, item.share)}%`, '--spark-color': colors[index % colors.length] }" /></td>
        </tr>
      </tbody>
    </table>
  </DashboardFrame>
</template>

<script setup>
import { computed } from 'vue'
import DashboardFrame from './DashboardFrame.vue'
import { formatNumber } from '../../utils/format.js'
const props = defineProps({ buckets: { type: Array, default: () => [] } })
const colors = ['#ef4444', '#f97316', '#f59e0b', '#22c55e', '#0891b2']
const rows = computed(() => {
  const source = props.buckets.slice(0, 5)
  const total = source.reduce((sum, item) => sum + Number(item.count || 0), 0)
  return source.map((item) => ({ ...item, share: total ? Number(((item.count / total) * 100).toFixed(1)) : 0 }))
})
</script>

<style scoped>
.service-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
th { padding: 3px 4px; border-bottom: 1px solid #bdc9d5; color: #6b7f92; font-size: 8px; text-align: left; }
td { height: 21px; padding: 3px 4px; border-bottom: 1px solid #e3e8ed; color: #30485d; font-size: 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
th:first-child { width: 38%; }
.spark { display: block; width: var(--spark-width); height: 3px; background: var(--spark-color); box-shadow: 8px -2px 0 -1px var(--spark-color), 16px 1px 0 -1px var(--spark-color); }
</style>
