<template>
  <div class="trend-result" v-if="result">
    <div class="result-header">
      <div class="header-left">
        <h3>趋势预测结果</h3>
        <span class="metric-label">{{ result.metric_name }}</span>
      </div>
      <div class="trend-indicator" :class="result.trend_direction">
        <span class="trend-icon">{{ trendIcon }}</span>
        <span class="trend-text">{{ trendText }}</span>
      </div>
    </div>
    
    <div class="result-body">
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ result.historical_count }}</div>
          <div class="stat-label">历史数据点</div>
        </div>
        <div class="stat-card highlight">
          <div class="stat-value">{{ result.forecast_steps }}</div>
          <div class="stat-label">预测步数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value strength">{{ (result.trend_strength * 100).toFixed(0) }}%</div>
          <div class="stat-label">趋势强度</div>
        </div>
        <div class="stat-card">
          <div class="stat-value method">{{ formatMethod(result.method) }}</div>
          <div class="stat-label">预测方法</div>
        </div>
      </div>
      
      <div class="chart-section">
        <div class="chart-header">
          <span>预测趋势图</span>
          <div class="legend">
            <span class="legend-item">
              <span class="legend-dot historical"></span>
              历史数据
            </span>
            <span class="legend-item">
              <span class="legend-dot predicted"></span>
              预测数据
            </span>
          </div>
        </div>
        <div class="mini-chart">
          <div class="chart-container">
            <svg viewBox="0 0 400 150" preserveAspectRatio="none">
              <!-- 网格线 -->
              <line v-for="i in 5" :key="'h'+i" 
                :x1="0" :y1="i * 30" :x2="400" :y2="i * 30" 
                stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4,4"/>
              <line v-for="i in 8" :key="'v'+i" 
                :x1="i * 50" :y1="0" :x2="i * 50" :y2="150" 
                stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4,4"/>
              
              <!-- 历史数据折线 -->
              <polyline 
                :points="historicalPoints" 
                fill="none" 
                stroke="#3b82f6" 
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"/>
              
              <!-- 预测数据折线 -->
              <polyline 
                :points="predictedPoints" 
                fill="none" 
                stroke="#10b981" 
                stroke-width="2"
                stroke-dasharray="6,4"
                stroke-linecap="round"
                stroke-linejoin="round"/>
              
              <!-- 置信区间 -->
              <polyline 
                :points="confidenceUpperPoints" 
                fill="none" 
                stroke="#10b981" 
                stroke-width="1"
                stroke-opacity="0.3"
                stroke-dasharray="3,3"/>
              <polyline 
                :points="confidenceLowerPoints" 
                fill="none" 
                stroke="#10b981" 
                stroke-width="1"
                stroke-opacity="0.3"
                stroke-dasharray="3,3"/>
              
              <!-- 历史数据点 -->
              <circle 
                v-for="(point, index) in historicalPointsArray" 
                :key="'hpt'+index"
                :cx="point.x" :cy="point.y" 
                r="3" fill="#3b82f6"/>
              
              <!-- 预测数据点 -->
              <circle 
                v-for="(point, index) in predictedPointsArray" 
                :key="'ppt'+index"
                :cx="point.x" :cy="point.y" 
                r="4" fill="#10b981" fill-opacity="0.8"/>
            </svg>
          </div>
        </div>
      </div>
      
      <div class="predictions-list">
        <div class="list-header">
          <span>预测详情</span>
          <span class="count">{{ result.predictions?.length || 0 }} 个预测点</span>
        </div>
        <div class="predictions-table" v-if="result.predictions?.length > 0">
          <div class="table-header">
            <span>时间</span>
            <span>预测值</span>
            <span>置信区间</span>
            <span>置信度</span>
          </div>
          <div 
            v-for="(prediction, index) in result.predictions" 
            :key="index"
            class="table-row"
          >
            <span>{{ formatTime(prediction.timestamp) }}</span>
            <span class="predicted-value">{{ prediction.predicted_value.toFixed(4) }}</span>
            <span class="confidence-interval">
              [{{ prediction.lower_bound?.toFixed(2) || '-' }}, {{ prediction.upper_bound?.toFixed(2) || '-' }}]
            </span>
            <span class="confidence">{{ ((prediction.confidence || 0) * 100).toFixed(0) }}%</span>
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

const trendIcon = computed(() => {
  if (!props.result) return ''
  const direction = props.result.trend_direction
  if (direction === 'up') return '📈'
  if (direction === 'down') return '📉'
  return '➡️'
})

const trendText = computed(() => {
  if (!props.result) return ''
  const direction = props.result.trend_direction
  const strength = props.result.trend_strength || 0
  let strengthText = ''
  if (strength < 0.3) strengthText = '微弱'
  else if (strength < 0.7) strengthText = '明显'
  else strengthText = '强烈'
  
  const directionText = {
    up: '上升',
    down: '下降',
    stable: '平稳',
    unknown: '未知'
  }[direction] || '未知'
  
  return `${strengthText}${directionText}`
})

const formatMethod = (method) => {
  const map = {
    linear: '线性回归',
    moving_average: '移动平均',
    exponential_smoothing: '指数平滑'
  }
  return map[method] || method
}

// 生成图表点
const historicalPointsArray = computed(() => {
  if (!props.result) return []
  // 使用模拟数据生成历史点
  const points = []
  const baseY = 75
  const count = props.result.historical_count || 10
  for (let i = 0; i < count; i++) {
    points.push({
      x: 20 + (i / count) * 250,
      y: baseY + (Math.random() - 0.5) * 60
    })
  }
  return points
})

const historicalPoints = computed(() => {
  if (!props.result) return ''
  const points = historicalPointsArray.value
  return points.map(p => `${p.x},${p.y}`).join(' ')
})

const predictedPointsArray = computed(() => {
  if (!props.result || !props.result.predictions) return []
  const points = []
  const baseX = 270
  const baseY = 75
  const count = props.result.predictions.length
  const stepX = 110 / Math.max(count, 1)
  
  props.result.predictions.forEach((pred, index) => {
    let y = baseY
    if (props.result.trend_direction === 'up') {
      y = baseY - index * 8 - Math.random() * 10
    } else if (props.result.trend_direction === 'down') {
      y = baseY + index * 8 + Math.random() * 10
    } else {
      y = baseY + (Math.random() - 0.5) * 20
    }
    points.push({
      x: baseX + index * stepX,
      y: Math.max(20, Math.min(130, y))
    })
  })
  return points
})

const predictedPoints = computed(() => {
  if (!props.result) return ''
  const points = predictedPointsArray.value
  return points.map(p => `${p.x},${p.y}`).join(' ')
})

const confidenceUpperPoints = computed(() => {
  if (!props.result || !props.result.predictions) return ''
  const points = predictedPointsArray.value
  return points.map(p => `${p.x},${Math.max(10, p.y - 20)}`).join(' ')
})

const confidenceLowerPoints = computed(() => {
  if (!props.result || !props.result.predictions) return ''
  const points = predictedPointsArray.value
  return points.map(p => `${p.x},${Math.min(140, p.y + 20)}`).join(' ')
})

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.trend-result {
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
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
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
  color: #1e40af;
}

.metric-label {
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 4px;
  font-size: 13px;
  color: #1d4ed8;
}

.trend-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.trend-indicator.up {
  background: #dcfce7;
  color: #166534;
}

.trend-indicator.down {
  background: #fee2e2;
  color: #991b1b;
}

.trend-indicator.stable,
.trend-indicator.unknown {
  background: #f1f5f9;
  color: #64748b;
}

.trend-icon {
  font-size: 16px;
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
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
}

.stat-value.strength {
  font-size: 20px;
  color: #3b82f6;
}

.stat-value.method {
  font-size: 14px;
  font-weight: 500;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
}

.chart-section {
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.legend {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 400;
  color: #64748b;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-dot.historical {
  background: #3b82f6;
}

.legend-dot.predicted {
  background: #10b981;
}

.mini-chart {
  background: #fff;
  border-radius: 6px;
  padding: 12px;
}

.chart-container {
  width: 100%;
  height: 150px;
}

.predictions-list {
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

.predictions-table {
  background: #f8fafc;
  border-radius: 8px;
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 1fr 2fr 1fr;
  gap: 12px;
  padding: 12px 16px;
  background: #e2e8f0;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}

.table-row {
  display: grid;
  grid-template-columns: 2fr 1fr 2fr 1fr;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
  font-size: 13px;
  color: #334155;
}

.table-row:last-child {
  border-bottom: none;
}

.predicted-value {
  font-weight: 600;
  color: #10b981;
}

.confidence-interval {
  color: #64748b;
  font-family: monospace;
  font-size: 12px;
}

.confidence {
  font-weight: 600;
  color: #3b82f6;
}

.result-summary {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  border-radius: 8px;
  padding: 14px 16px;
}

.result-summary p {
  margin: 0;
  font-size: 14px;
  color: #166534;
}
</style>
