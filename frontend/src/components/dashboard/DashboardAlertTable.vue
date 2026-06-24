<template>
  <DashboardFrame title="活跃预警摘要" :subtitle="`ACTIVE ${total}`" tone="red" flush>
    <template #actions><router-link to="/analysis/alerts">查看全部 →</router-link></template>
    <table class="alert-table">
      <thead><tr><th>级别</th><th>告警内容</th><th>开始时间</th><th>证据</th></tr></thead>
      <tbody>
        <tr v-for="item in alerts.slice(0, 5)" :key="item.alert_id">
          <td><span :class="`severity severity--${tone(item.severity)}`">{{ severityLabel(item.severity) }}</span></td>
          <td>
            <strong>{{ item.title || item.alert_type || '待处理预警' }}</strong>
            <small>{{ item.affected_service || '未知服务' }}</small>
          </td>
          <td class="tabular-nums">{{ shortTime(item.created_at) }}</td>
          <td class="tabular-nums">{{ item.evidence_count ?? '-' }}</td>
        </tr>
        <tr v-if="!alerts.length"><td colspan="4" class="alert-table__empty">暂无活跃预警</td></tr>
      </tbody>
    </table>
  </DashboardFrame>
</template>

<script setup>
import DashboardFrame from './DashboardFrame.vue'
defineProps({ alerts: { type: Array, default: () => [] }, total: { type: Number, default: 0 } })
function tone(level) {
  const value = String(level || '').toLowerCase()
  return value === 'critical' || value === 'high' ? 'high' : value === 'medium' || value === 'warning' ? 'medium' : 'low'
}
function severityLabel(level) { return { high: '高', critical: '高', medium: '中', warning: '中', low: '低' }[String(level || '').toLowerCase()] || '中' }
function shortTime(value) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '-' : date.toLocaleTimeString('zh-CN', { hour12: false })
}
</script>

<style scoped>
a { color: #2563eb; font-size: 9px; font-weight: 800; }
.alert-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.alert-table th {
  padding: 5px 6px;
  border-bottom: 1px solid #b7c5d3;
  color: #63778a;
  font-size: 8px;
  font-weight: 700;
  text-align: left;
}
.alert-table th:nth-child(1) { width: 44px; }
.alert-table th:nth-child(3) { width: 58px; }
.alert-table th:nth-child(4) { width: 34px; }
.alert-table td { height: 31px; padding: 4px 6px; border-bottom: 1px solid #e0e6ec; color: #52677b; font-size: 8px; }
.alert-table td strong { display: block; overflow: hidden; color: #253d52; font-size: 9px; text-overflow: ellipsis; white-space: nowrap; }
.alert-table td small { color: #8292a3; font-size: 8px; }
.severity { display: inline-grid; min-width: 26px; height: 18px; place-items: center; color: white; font-size: 9px; font-weight: 900; }
.severity--high { background: #ef4444; }
.severity--medium { background: #f59e0b; }
.severity--low { background: #22c55e; }
.alert-table__empty { text-align: center; color: #8292a3; }
</style>
