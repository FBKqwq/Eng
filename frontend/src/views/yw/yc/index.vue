<template>
  <div class="yc-page" :class="{ 'dark-theme': isDark }">
    <!-- 顶部工具栏 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>📊 异常预测中心</h1>
          <p class="subtitle">基于统计方法的时序异常检测与趋势预测</p>
        </div>
        <div class="header-actions">
          <button class="action-btn" @click="toggleTheme">
            {{ isDark ? '☀️ 浅色' : '🌙 深色' }}
          </button>
          <button class="action-btn" @click="showHistory = true" :disabled="historyList.length === 0">
            📜 历史记录
          </button>
        </div>
      </div>
    </div>
    
    <div class="page-body">
      <div class="left-panel">
        <PredictionPanel @predict="handlePredict" />
        
        <!-- 告警规则配置 -->
        <div class="alarm-panel">
          <div class="panel-header">
            <h3>🔔 告警规则配置</h3>
            <button 
              class="btn btn-sm" 
              @click="alarmEnabled = !alarmEnabled"
              :class="alarmEnabled ? 'btn-success' : 'btn-secondary'"
            >
              {{ alarmEnabled ? '已启用' : '已禁用' }}
            </button>
          </div>
          <div class="alarm-config" v-if="alarmEnabled">
            <div class="form-row">
              <div class="form-group">
                <label>异常级别阈值</label>
                <select v-model="alarmConfig.level" class="form-control">
                  <option value="warning">警告</option>
                  <option value="critical">严重</option>
                  <option value="both">两者都触发</option>
                </select>
              </div>
              <div class="form-group">
                <label>异常占比阈值 (%)</label>
                <input v-model.number="alarmConfig.rateThreshold" type="number" min="1" max="100" class="form-control" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>趋势方向告警</label>
                <select v-model="alarmConfig.trendDirection" class="form-control">
                  <option value="none">不检测</option>
                  <option value="up">上升趋势</option>
                  <option value="down">下降趋势</option>
                  <option value="both">双向检测</option>
                </select>
              </div>
              <div class="form-group">
                <label>趋势强度阈值</label>
                <input v-model.number="alarmConfig.trendStrength" type="number" min="0" max="1" step="0.1" class="form-control" />
              </div>
            </div>
            <button class="btn btn-primary btn-block" @click="saveAlarmConfig">
              💾 保存配置
            </button>
          </div>
        </div>
        
        <div class="loading-overlay" v-if="loading">
          <div class="spinner"></div>
          <span>正在执行预测分析...</span>
        </div>
      </div>
      
      <div class="right-panel">
        <div class="tabs">
          <button class="tab-btn" :class="{ active: activeTab === 'chart' }" @click="activeTab = 'chart'">
            📈 数据图表
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'anomaly' }" @click="activeTab = 'anomaly'">
            🔍 异常检测
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'trend' }" @click="activeTab = 'trend'">
            📊 趋势预测
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'summary' }" @click="activeTab = 'summary'">
            📋 综合摘要
          </button>
        </div>
        
        <div class="tab-content">
          <!-- 数据图表 -->
          <div v-if="activeTab === 'chart'">
            <div v-if="predictionResult" class="chart-container">
              <TimeSeriesChart 
                :historical-data="originalData"
                :predictions="predictionResult.trend?.predictions || []"
                :anomalies="predictionResult.anomaly?.anomalies || []"
                :metric-name="predictionResult.metric_name"
                height="350px"
              />
            </div>
            <EmptyState v-else :loading="loading" />
          </div>
          
          <!-- 异常检测 -->
          <div v-if="activeTab === 'anomaly'">
            <AnomalyResult v-if="predictionResult?.anomaly" :result="predictionResult.anomaly" />
            <EmptyState v-else :loading="loading" />
          </div>
          
          <!-- 趋势预测 -->
          <div v-if="activeTab === 'trend'">
            <TrendResult v-if="predictionResult?.trend" :result="predictionResult.trend" />
            <EmptyState v-else :loading="loading" />
          </div>
          
          <!-- 综合摘要 -->
          <div v-if="activeTab === 'summary'">
            <div class="summary-card" v-if="predictionResult">
              <div class="card-header">
                <h3>综合分析报告</h3>
                <div class="card-actions">
                  <button class="btn btn-sm btn-secondary" @click="exportData('json')">
                    📥 导出 JSON
                  </button>
                  <button class="btn btn-sm btn-secondary" @click="exportData('csv')">
                    📥 导出 CSV
                  </button>
                </div>
              </div>
              <div class="summary-content">
                <div class="summary-item">
                  <span class="summary-label">指标名称</span>
                  <span class="summary-value">{{ predictionResult.metric_name }}</span>
                </div>
                <div class="summary-item highlight">
                  <span class="summary-label">综合结论</span>
                  <span class="summary-value">{{ predictionResult.combined_summary }}</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">异常检测</span>
                  <span class="summary-value">
                    {{ predictionResult.anomaly?.anomaly_count || 0 }} 个异常点
                    ({{ ((predictionResult.anomaly?.anomaly_ratio || 0) * 100).toFixed(1) }}%)
                  </span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">趋势预测</span>
                  <span class="summary-value">
                    {{ getTrendLabel(predictionResult.trend?.trend_direction) }}
                    (强度: {{ (predictionResult.trend?.trend_strength || 0) * 100 }}%)
                  </span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">检测方法</span>
                  <span class="summary-value">{{ getMethodLabel(predictionResult.anomaly?.method) }}</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">预测方法</span>
                  <span class="summary-value">{{ getPredictMethodLabel(predictionResult.trend?.method) }}</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">数据点总数</span>
                  <span class="summary-value">{{ predictionResult.anomaly?.total_points || 0 }}</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">预测步数</span>
                  <span class="summary-value">{{ predictionResult.trend?.forecast_steps || 0 }}</span>
                </div>
              </div>
            </div>
            <EmptyState v-else :loading="loading" />
          </div>
        </div>
      </div>
    </div>
    
    <!-- 历史记录弹窗 -->
    <div class="modal-overlay" v-if="showHistory" @click.self="showHistory = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>📜 预测历史记录</h3>
          <button class="modal-close" @click="showHistory = false">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="historyList.length === 0" class="empty-history">
            暂无历史记录
          </div>
          <div v-else class="history-list">
            <div 
              v-for="(item, index) in historyList" 
              :key="index" 
              class="history-item"
              @click="loadHistory(item)"
            >
              <div class="history-header">
                <span class="history-metric">{{ item.metric_name }}</span>
                <span class="history-time">{{ formatDateTime(item.timestamp) }}</span>
              </div>
              <div class="history-summary">{{ item.combined_summary }}</div>
              <div class="history-stats">
                <span>异常: {{ item.anomaly?.anomaly_count || 0 }}</span>
                <span>趋势: {{ getTrendLabel(item.trend?.trend_direction) }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="clearHistory">清空记录</button>
          <button class="btn btn-primary" @click="showHistory = false">关闭</button>
        </div>
      </div>
    </div>
    
    <!-- 告警通知 -->
    <div class="toast" :class="{ show: showToast }">
      <div class="toast-icon">{{ toastIcon }}</div>
      <div class="toast-content">
        <div class="toast-title">{{ toastTitle }}</div>
        <div class="toast-message">{{ toastMessage }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import PredictionPanel from './PredictionPanel.vue'
import AnomalyResult from './AnomalyResult.vue'
import TrendResult from './TrendResult.vue'
import EmptyState from '../../../components/common/EmptyState.vue'
import TimeSeriesChart from '../../../components/common/charts/TimeSeriesChart.vue'
import { prediction } from '../../../api/prediction.js'

// 主题状态
const isDark = ref(true)
const activeTab = ref('chart')
const loading = ref(false)
const predictionResult = ref(null)
const originalData = ref([])

// 历史记录
const showHistory = ref(false)
const historyList = ref([])

// 告警配置
const alarmEnabled = ref(false)
const alarmConfig = reactive({
  level: 'warning',
  rateThreshold: 5,
  trendDirection: 'up',
  trendStrength: 0.5
})

// Toast通知
const showToast = ref(false)
const toastIcon = ref('')
const toastTitle = ref('')
const toastMessage = ref('')

// 加载历史记录
function loadHistoryList() {
  const saved = localStorage.getItem('prediction_history')
  if (saved) {
    historyList.value = JSON.parse(saved)
  }
}

// 保存到历史记录
function saveToHistory(result) {
  const record = {
    ...result,
    timestamp: new Date().toISOString()
  }
  historyList.value.unshift(record)
  // 最多保留20条记录
  if (historyList.value.length > 20) {
    historyList.value = historyList.value.slice(0, 20)
  }
  localStorage.setItem('prediction_history', JSON.stringify(historyList.value))
}

// 加载历史记录项
function loadHistory(item) {
  predictionResult.value = item
  activeTab.value = 'chart'
  showHistory.value = false
  showNotification('✅', '历史记录', '已加载历史预测结果')
}

// 清空历史记录
function clearHistory() {
  historyList.value = []
  localStorage.removeItem('prediction_history')
  showNotification('🗑️', '清空完成', '历史记录已清空')
}

// 切换主题
function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem('yc_dark_mode', String(isDark.value))
}

// 显示通知
function showNotification(icon, title, message) {
  toastIcon.value = icon
  toastTitle.value = title
  toastMessage.value = message
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 3000)
}

// 导出数据
function exportData(format) {
  if (!predictionResult.value) return
  
  const data = predictionResult.value
  const filename = `prediction_${data.metric_name}_${Date.now()}`
  
  if (format === 'json') {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    downloadBlob(blob, `${filename}.json`)
  } else {
    // CSV格式
    const headers = ['时间', '数值', '是否异常']
    const rows = []
    
    // 历史数据
    originalData.value.forEach(d => {
      rows.push([new Date(d.timestamp).toLocaleString('zh-CN'), d.value, '否'])
    })
    
    // 异常点
    if (data.anomaly?.anomalies) {
      data.anomaly.anomalies.forEach(a => {
        const row = rows.find(r => r[0] === new Date(a.timestamp).toLocaleString('zh-CN'))
        if (row) {
          row[2] = '是'
        }
      })
    }
    
    // 预测数据
    if (data.trend?.predictions) {
      data.trend.predictions.forEach(p => {
        rows.push([new Date(p.timestamp).toLocaleString('zh-CN'), p.predicted_value, '预测'])
      })
    }
    
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv' })
    downloadBlob(blob, `${filename}.csv`)
  }
  
  showNotification('📥', '导出成功', `数据已导出为 ${format.toUpperCase()} 格式`)
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// 保存告警配置
function saveAlarmConfig() {
  localStorage.setItem('alarm_config', JSON.stringify(alarmConfig))
  showNotification('💾', '保存成功', '告警配置已保存')
}

// 检查告警条件
function checkAlarms(result) {
  if (!alarmEnabled.value) return
  
  const alarms = []
  
  // 检查异常占比
  const anomalyRatio = result.anomaly?.anomaly_ratio || 0
  if (anomalyRatio * 100 >= alarmConfig.rateThreshold) {
    alarms.push(`异常占比超过阈值 (${(anomalyRatio * 100).toFixed(1)}% > ${alarmConfig.rateThreshold}%)`)
  }
  
  // 检查趋势
  const trendDirection = result.trend?.trend_direction
  const trendStrength = result.trend?.trend_strength || 0
  
  if (alarmConfig.trendDirection !== 'none') {
    if (alarmConfig.trendDirection === 'both' && trendStrength >= alarmConfig.trendStrength) {
      alarms.push(`${getTrendLabel(trendDirection)}趋势超过阈值 (强度: ${(trendStrength * 100).toFixed(1)}%)`)
    } else if (alarmConfig.trendDirection === trendDirection && trendStrength >= alarmConfig.trendStrength) {
      alarms.push(`${getTrendLabel(trendDirection)}趋势超过阈值 (强度: ${(trendStrength * 100).toFixed(1)}%)`)
    }
  }
  
  if (alarms.length > 0) {
    showNotification('⚠️', '告警触发', alarms.join('\n'))
  }
}

// 处理预测
async function handlePredict(data) {
  loading.value = true
  predictionResult.value = null
  
  try {
    originalData.value = data.data || []
    const response = await prediction(data)
    predictionResult.value = response.data
    
    // 保存到历史记录
    saveToHistory(response.data)
    
    // 检查告警
    checkAlarms(response.data)
    
  } catch (error) {
    console.error('请求失败:', error)
    showNotification('❌', '请求失败', '预测分析失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

// 工具函数
function getTrendLabel(direction) {
  const labels = {
    'up': '📈 上升',
    'down': '📉 下降',
    'stable': '➡️ 稳定'
  }
  return labels[direction] || '未知'
}

function getMethodLabel(method) {
  const labels = {
    'zscore': 'Z-Score',
    'iqr': 'IQR',
    'mad': 'MAD'
  }
  return labels[method] || method
}

function getPredictMethodLabel(method) {
  const labels = {
    'linear': '线性回归',
    'moving_average': '移动平均',
    'exponential_smoothing': '指数平滑'
  }
  return labels[method] || method
}

function formatDateTime(timestamp) {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleString('zh-CN')
}

// 初始化
loadHistoryList()
const savedDarkMode = localStorage.getItem('yc_dark_mode')
if (savedDarkMode !== null) {
  isDark.value = savedDarkMode === 'true'
}
const savedAlarmConfig = localStorage.getItem('alarm_config')
if (savedAlarmConfig) {
  Object.assign(alarmConfig, JSON.parse(savedAlarmConfig))
}
</script>

<style scoped>
.yc-page {
  min-height: 100vh;
  padding: 20px;
  transition: background 0.3s;
}

.yc-page:not(.dark-theme) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

.yc-page.dark-theme {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

.page-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1600px;
  margin: 0 auto;
}

.title-section h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  margin: 8px 0 0;
  font-size: 14px;
  color: #64748b;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.2);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-body {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

.left-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.alarm-panel {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.alarm-panel .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;
  background: #f8fafc;
}

.alarm-panel h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.alarm-config {
  padding: 16px;
}

.alarm-config .form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.alarm-config .form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.alarm-config .form-group label {
  font-size: 12px;
  color: #64748b;
}

.alarm-config .form-control {
  padding: 6px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  font-size: 13px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;
}

.btn-secondary {
  background: #e2e8f0;
  color: #475569;
}

.btn-success {
  background: #22c55e;
  color: #fff;
}

.btn-sm {
  padding: 4px 12px;
  font-size: 12px;
}

.btn-block {
  width: 100%;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border-radius: 8px;
  z-index: 10;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-overlay span {
  font-size: 14px;
  color: #64748b;
}

.right-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tabs {
  display: flex;
  gap: 8px;
  background: rgba(255, 255, 255, 0.8);
  padding: 8px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.dark-theme .tabs {
  background: rgba(255, 255, 255, 0.05);
}

.tab-btn {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #64748b;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.tab-btn.active {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;
}

.tab-content {
  flex: 1;
  min-height: 500px;
}

.chart-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 16px;
}

.summary-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.summary-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e8e8e8;
  background: #f8fafc;
}

.summary-card h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.summary-content {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 20px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 6px;
}

.summary-item.highlight {
  grid-column: span 2;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
}

.summary-label {
  font-size: 12px;
  color: #64748b;
}

.summary-value {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.summary-item.highlight .summary-value {
  color: #1e40af;
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-content {
  background: #fff;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e8e8e8;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
}

.modal-close {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #64748b;
}

.modal-body {
  padding: 16px;
  overflow-y: auto;
  max-height: 400px;
}

.empty-history {
  text-align: center;
  color: #94a3b8;
  padding: 40px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.history-item:hover {
  background: #f1f5f9;
}

.history-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.history-metric {
  font-weight: 600;
  color: #1e293b;
}

.history-time {
  font-size: 12px;
  color: #64748b;
}

.history-summary {
  font-size: 13px;
  color: #475569;
  margin-bottom: 8px;
}

.history-stats {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #64748b;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e8e8e8;
}

/* Toast通知 */
.toast {
  position: fixed;
  bottom: 32px;
  right: 32px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: #1e293b;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  transform: translateX(120%);
  opacity: 0;
  transition: all 0.3s;
  z-index: 200;
}

.toast.show {
  transform: translateX(0);
  opacity: 1;
}

.toast-icon {
  font-size: 24px;
}

.toast-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.toast-title {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
}

.toast-message {
  font-size: 13px;
  color: #94a3b8;
}

@media (max-width: 1200px) {
  .page-body {
    grid-template-columns: 1fr;
  }
  
  .left-panel {
    max-width: 600px;
    margin: 0 auto;
  }
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .summary-content {
    grid-template-columns: 1fr;
  }
  
  .summary-item.highlight {
    grid-column: span 1;
  }
  
  .tabs {
    flex-wrap: wrap;
  }
  
  .tab-btn {
    flex: none;
    min-width: calc(50% - 4px);
  }
}
</style>
