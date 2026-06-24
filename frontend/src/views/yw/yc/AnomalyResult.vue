<template>
  <div class="anomaly-result" v-if="result">
    <div class="result-header">
      <div class="header-left">
        <h3>异常检测结果</h3>
        <span class="metric-label">{{ result.metric_name }}</span>
      </div>
      <div class="summary-badge" :class="severityClass">
        {{ anomalySummary }}
      </div>
    </div>
    
    <div class="result-body">
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ result.total_points }}</div>
          <div class="stat-label">数据点总数</div>
        </div>
        <div class="stat-card highlight">
          <div class="stat-value" :class="{ critical: result.anomaly_count > 0 }">
            {{ result.anomaly_count }}
          </div>
          <div class="stat-label">异常点数量</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ (result.anomaly_ratio * 100).toFixed(1) }}%</div>
          <div class="stat-label">异常占比</div>
        </div>
        <div class="stat-card">
          <div class="stat-value method">{{ result.method }}</div>
          <div class="stat-label">检测方法</div>
        </div>
      </div>
      
      <div class="stats-detail" v-if="result.stats">
        <div class="detail-title">统计摘要</div>
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">平均值</span>
            <span class="detail-value">{{ result.stats.mean?.toFixed(4) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">标准差</span>
            <span class="detail-value">{{ result.stats.std?.toFixed(4) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">最小值</span>
            <span class="detail-value">{{ result.stats.min?.toFixed(4) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">最大值</span>
            <span class="detail-value">{{ result.stats.max?.toFixed(4) }}</span>
          </div>
        </div>
      </div>
      
      <div class="anomaly-list" v-if="result.anomalies && result.anomalies.length > 0">
        <div class="list-header">
          <span>异常点详情</span>
          <span class="count">{{ result.anomalies.length }} 条</span>
        </div>
        <div class="anomaly-items">
          <div 
            v-for="(anomaly, index) in result.anomalies" 
            :key="index"
            class="anomaly-item"
            :class="anomaly.level"
          >
            <div class="item-time">{{ formatTime(anomaly.timestamp) }}</div>
            <div class="item-value">
              <span class="actual">{{ anomaly.value }}</span>
              <span class="expected">预期: {{ anomaly.expected }}</span>
            </div>
            <div class="item-deviation">偏离 {{ anomaly.deviation.toFixed(2) }}σ</div>
            <div class="item-reason">{{ anomaly.reason }}</div>
          </div>
        </div>
      </div>
      
      <div class="result-summary">
        <p>{{ result.summary }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  result: {
    type: Object,
    default: null
  }
})

const severityClass = computed(() => {
  if (!props.result) return ''
  const ratio = props.result.anomaly_ratio
  if (ratio > 0.3) return 'critical'
  if (ratio > 0.1) return 'warning'
  return 'normal'
})

const anomalySummary = computed(() => {
  if (!props.result) return ''
  const count = props.result.anomaly_count
  if (count === 0) return '✅ 未检测到异常'
  if (count > 0 && props.result.anomaly_ratio > 0.3) return '🔴 严重异常'
  if (count > 0 && props.result.anomaly_ratio > 0.1) return '🟡 存在异常'
  return '🟢 偶发异常'
})

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
</script>

<style scoped>
.anomaly-result {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e8e8e8;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #92400e;
}

.metric-label {
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 4px;
  font-size: 13px;
  color: #b45309;
}

.summary-badge {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.summary-badge.normal {
  background: #dcfce7;
  color: #166534;
}

.summary-badge.warning {
  background: #fef3c7;
  color: #92400e;
}

.summary-badge.critical {
  background: #fee2e2;
  color: #991b1b;
}

.result-body {
  padding: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card {
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.stat-card.highlight {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
}

.stat-value.critical {
  color: #dc2626;
}

.stat-value.method {
  font-size: 14px;
  font-weight: 500;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
}

.stats-detail {
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}

.detail-title {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 12px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px dashed #e2e8f0;
}

.detail-label {
  font-size: 13px;
  color: #64748b;
}

.detail-value {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.anomaly-list {
  margin-bottom: 20px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.count {
  font-size: 12px;
  font-weight: 400;
  color: #64748b;
}

.anomaly-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.anomaly-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-radius: 8px;
  background: #f8fafc;
  border-left: 4px solid;
}

.anomaly-item.normal {
  border-color: #22c55e;
}

.anomaly-item.warning {
  border-color: #f59e0b;
}

.anomaly-item.critical {
  border-color: #dc2626;
}

.item-time {
  font-size: 13px;
  color: #64748b;
  min-width: 120px;
}

.item-value {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.item-value .actual {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.item-value .expected {
  font-size: 12px;
  color: #64748b;
}

.item-deviation {
  font-size: 13px;
  color: #dc2626;
  font-weight: 500;
  min-width: 100px;
}

.item-reason {
  flex: 1;
  font-size: 13px;
  color: #475569;
}

.result-summary {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-radius: 8px;
  padding: 14px 16px;
}

.result-summary p {
  margin: 0;
  font-size: 14px;
  color: #1e40af;
}
</style>
