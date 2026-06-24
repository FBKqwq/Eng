<template>
  <DashboardFrame title="最新体检结论" subtitle="LATEST INSPECTION" tone="red">
    <div v-if="report" class="report-panel" role="button" tabindex="0" @click="goReport" @keydown.enter="goReport">
      <div class="report-panel__risk">
        <span :class="`risk-${riskLevel}`">!</span>
        <div>
          <small>风险等级</small>
          <strong>{{ riskLabel }}</strong>
        </div>
      </div>
      <div class="report-panel__summary">
        <small>体检结论摘要</small>
        <p>{{ report.summary || '暂无摘要' }}</p>
      </div>
      <footer>
        <dl>
          <div><dt>报告类型</dt><dd>{{ reportType }}</dd></div>
          <div><dt>报告时间</dt><dd class="tabular-nums">{{ formatTime(report.created_at) }}</dd></div>
        </dl>
        <span>查看体检报告 →</span>
      </footer>
    </div>
    <div v-else class="report-panel__empty">暂无周期体检报告</div>
  </DashboardFrame>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import DashboardFrame from './DashboardFrame.vue'
import { formatTime } from '../../utils/format.js'

const props = defineProps({ report: { type: Object, default: null } })
const router = useRouter()
const riskLevel = computed(() => String(props.report?.risk_level || 'medium').toLowerCase())
const riskLabel = computed(() => ({ low: '低风险', medium: '中风险', high: '高风险' }[riskLevel.value] || '未知'))
const reportType = computed(() => props.report?.report_type === 'periodic' ? '周期体检' : '事件诊断')
function goReport() { router.push('/analysis/reports') }
</script>

<style scoped>
.report-panel {
  display: grid;
  grid-template-columns: 126px minmax(0, 1fr);
  grid-template-rows: 92px 36px;
  height: 136px;
  cursor: pointer;
}
.report-panel__risk {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 5px 11px;
  border-right: 1px solid #d5dee8;
}
.report-panel__risk > span {
  display: grid;
  place-items: center;
  width: 42px;
  height: 49px;
  color: #fff;
  font-size: 27px;
  font-weight: 950;
  clip-path: polygon(50% 0, 94% 19%, 84% 78%, 50% 100%, 16% 78%, 6% 19%);
}
.risk-high { background: #ef4444; }
.risk-medium { background: #f59e0b; }
.risk-low { background: #22c55e; }
.report-panel small, .report-panel dt { color: #6b7f92; font-size: 9px; }
.report-panel__risk strong {
  display: block;
  margin-top: 4px;
  color: #dc2626;
  font-size: 16px;
  line-height: 1;
  white-space: nowrap;
}
.report-panel__summary { padding: 8px 12px; }
.report-panel__summary p {
  display: -webkit-box;
  margin: 5px 0 0;
  overflow: hidden;
  color: #273f55;
  font-size: 11px;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}
.report-panel footer {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 10px;
  border-top: 1px solid #d5dee8;
}
.report-panel footer dl { display: flex; gap: 24px; margin: 0; }
.report-panel footer dl div { display: flex; gap: 7px; }
.report-panel footer dd { margin: 0; color: #30485d; font-size: 9px; }
.report-panel footer > span {
  padding: 4px 9px;
  border: 1px solid #6b7f92;
  color: #173b5c;
  font-size: 9px;
  font-weight: 900;
}
.report-panel__empty { display: grid; height: 136px; place-items: center; color: #8292a3; font-size: 11px; }
</style>
