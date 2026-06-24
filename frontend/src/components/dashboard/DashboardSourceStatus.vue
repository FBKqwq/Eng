<template>
  <DashboardFrame title="日志源接入状态" subtitle="INGEST SOURCES" tone="cyan" flush>
    <table class="source-table">
      <thead><tr><th>日志源</th><th>状态</th><th>日志量</th><th>窗口占比</th><th>健康度</th></tr></thead>
      <tbody>
        <tr v-for="row in rows" :key="row.key">
          <td><span class="source-icon">{{ row.short }}</span>{{ row.label }}</td>
          <td><span class="source-status" :class="{ muted: !row.count }">{{ row.count ? '正常' : '无流量' }}</span></td>
          <td class="tabular-nums">{{ formatNumber(row.count) }}</td>
          <td class="tabular-nums">{{ row.share }}%</td>
          <td><span class="health-bar"><i :style="{ width: `${row.health}%` }" /></span></td>
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
const meta = {
  application: ['应用服务日志', 'APP'],
  behavior: ['用户行为日志', 'USR'],
  web_server: ['Web服务器日志', 'WEB'],
  performance: ['性能指标日志', 'PER'],
  security: ['安全日志', 'SEC'],
  infrastructure: ['基础设施日志', 'INF'],
  audit: ['审计日志', 'AUD']
}
const rows = computed(() => {
  const map = new Map(props.buckets.map((item) => [String(item.key), Number(item.count || 0)]))
  const total = [...map.values()].reduce((sum, value) => sum + value, 0)
  return Object.entries(meta).map(([key, [label, short]]) => {
    const count = map.get(key) || 0
    const share = total ? Number(((count / total) * 100).toFixed(1)) : 0
    return { key, label, short, count, share, health: count ? Math.min(100, 62 + share * 2.2) : 8 }
  })
})
</script>

<style scoped>
.source-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.source-table th { height: 25px; padding: 4px 6px; border-bottom: 1px solid #b7c5d3; color: #63778a; font-size: 8px; text-align: left; }
.source-table th:first-child { width: 34%; }
.source-table td { height: 28px; padding: 4px 6px; border-bottom: 1px solid #e0e6ec; color: #30485d; font-size: 8px; }
.source-icon {
  display: inline-grid;
  width: 26px;
  height: 17px;
  margin-right: 6px;
  place-items: center;
  background: #e0f2fe;
  color: #0369a1;
  font-family: var(--font-mono);
  font-size: 7px;
  font-weight: 900;
}
.source-status { color: #16a34a; }
.source-status::before { display: inline-block; width: 5px; height: 5px; margin-right: 4px; border-radius: 50%; background: currentColor; content: ''; }
.source-status.muted { color: #94a3b8; }
.health-bar { display: block; width: 100%; height: 6px; background: #e2e8f0; }
.health-bar i { display: block; height: 100%; background: repeating-linear-gradient(90deg, #16a34a 0 8px, transparent 8px 11px); }
</style>
