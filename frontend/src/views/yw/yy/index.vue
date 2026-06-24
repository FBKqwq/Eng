<template>
  <div class="yy-page">
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>🔍 智能日志分析</h1>
          <p class="subtitle">基于模式识别的日志智能分析与聚类</p>
        </div>
        <div class="header-actions">
          <button class="action-btn" @click="generateMockLogs">🎲 生成模拟日志</button>
          <button class="action-btn" @click="clearLogs">🗑️ 清空日志</button>
        </div>
      </div>
    </div>
    
    <div class="page-body">
      <div class="left-panel">
        <div class="log-input-panel">
          <div class="panel-header">
            <h3>📝 日志输入</h3>
            <span class="log-count">已输入 {{ logs.length }} 条日志</span>
          </div>
          <textarea v-model="logInput" class="log-textarea" placeholder="每行输入一条日志，格式：时间戳|级别|消息"></textarea>
          <div class="textarea-actions">
            <button class="btn btn-primary" @click="parseLogs">解析日志</button>
            <button class="btn btn-secondary" @click="clearLogs">清空</button>
          </div>
        </div>
        
        <div class="log-list-panel">
          <div class="panel-header">
            <h3>📋 日志列表</h3>
          </div>
          <div class="log-list">
            <div v-for="(log, index) in logs" :key="index" class="log-item" :class="log.level.toLowerCase()">
              <span class="log-timestamp">{{ formatTime(log.timestamp) }}</span>
              <span class="log-level">{{ log.level }}</span>
              <span class="log-message">{{ truncate(log.message, 50) }}</span>
            </div>
            <div v-if="logs.length === 0" class="empty-state">暂无日志数据</div>
          </div>
        </div>
        
        <div class="loading-overlay" v-if="loading">
          <div class="spinner"></div>
          <span>正在分析日志...</span>
        </div>
      </div>
      
      <div class="right-panel">
        <div class="tabs">
          <button class="tab-btn" :class="{ active: activeTab === 'pattern' }" @click="activeTab = 'pattern'">📊 模式分析</button>
          <button class="tab-btn" :class="{ active: activeTab === 'anomaly' }" @click="activeTab = 'anomaly'">⚠️ 异常检测</button>
          <button class="tab-btn" :class="{ active: activeTab === 'cluster' }" @click="activeTab = 'cluster'">🗂️ 聚类分析</button>
        </div>
        
        <div class="tab-content">
          <div v-if="activeTab === 'pattern'">
            <div v-if="analysisResult?.pattern_analysis" class="result-card">
              <div class="card-header">
                <h3>日志模式分析结果</h3>
                <span class="result-summary">{{ analysisResult.pattern_analysis.summary }}</span>
              </div>
              <div class="pattern-list">
                <div v-for="(pattern, index) in analysisResult.pattern_analysis.patterns" :key="index" class="pattern-item">
                  <div class="pattern-header">
                    <span class="pattern-rank">#{{ index + 1 }}</span>
                    <span class="pattern-count">{{ pattern.count }} 次</span>
                    <span class="pattern-percentage">{{ pattern.percentage.toFixed(1) }}%</span>
                  </div>
                  <div class="pattern-text">{{ pattern.pattern }}</div>
                  <div class="pattern-examples">
                    <div class="example-title">示例:</div>
                    <div v-for="(example, i) in pattern.examples" :key="i" class="example-item">{{ truncate(example, 60) }}</div>
                  </div>
                  <div class="pattern-severity">
                    <span v-for="(count, level) in pattern.severity_distribution" :key="level" class="severity-tag">{{ level }}: {{ count }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else-if="!loading" class="empty-state">请输入日志并执行分析</div>
          </div>
          
          <div v-if="activeTab === 'anomaly'">
            <div v-if="analysisResult?.anomaly_patterns && analysisResult.anomaly_patterns.length > 0" class="result-card">
              <div class="card-header">
                <h3>🔴 异常模式检测结果</h3>
                <span class="result-summary">发现 {{ analysisResult.anomaly_patterns.length }} 个异常模式</span>
              </div>
              <div class="anomaly-list">
                <div v-for="(anomaly, index) in analysisResult.anomaly_patterns" :key="index" class="anomaly-item">
                  <div class="anomaly-header">
                    <span class="anomaly-level" :class="anomaly.level.toLowerCase()">{{ anomaly.level }}</span>
                    <span class="anomaly-count">{{ anomaly.count }} 次 ({{ anomaly.percentage.toFixed(3) }}%)</span>
                  </div>
                  <div class="anomaly-pattern">{{ anomaly.pattern }}</div>
                  <div class="anomaly-details">
                    <span>首次出现: {{ formatTime(anomaly.first_occurrence) }}</span>
                  </div>
                  <div class="anomaly-message">{{ anomaly.message }}</div>
                </div>
              </div>
            </div>
            <div v-else-if="!loading" class="result-card">
              <div class="empty-state success">✅ 未检测到异常模式</div>
            </div>
          </div>
          
          <div v-if="activeTab === 'cluster'">
            <div v-if="analysisResult?.cluster_result" class="result-card">
              <div class="card-header">
                <h3>聚类分析结果</h3>
                <span class="result-summary">{{ analysisResult.cluster_result.summary }}</span>
              </div>
              <div class="cluster-list">
                <div v-for="cluster in analysisResult.cluster_result.clusters" :key="cluster.cluster_id" class="cluster-item">
                  <div class="cluster-header">
                    <span class="cluster-id">{{ cluster.cluster_id }}</span>
                    <span class="cluster-count">{{ cluster.count }} 条日志</span>
                  </div>
                  <div class="cluster-pattern">{{ cluster.pattern }}</div>
                  <div class="cluster-representative">
                    <span class="rep-label">代表消息:</span>
                    <span class="rep-text">{{ truncate(cluster.representative, 80) }}</span>
                  </div>
                  <div class="cluster-severity">
                    <span v-for="(count, level) in cluster.severity_distribution" :key="level" class="severity-tag">{{ level }}: {{ count }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else-if="!loading" class="empty-state">请输入日志并执行分析</div>
          </div>
        </div>
        
        <button class="btn btn-primary btn-large" @click="runAnalysis" :disabled="logs.length === 0 || loading">
          {{ loading ? '分析中...' : '🚀 执行日志分析' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { logAnalysis } from '../../../api/log_analysis.js'

const logInput = ref('')
const logs = ref([])
const activeTab = ref('pattern')
const loading = ref(false)
const analysisResult = ref(null)

function parseLogs() {
  const lines = logInput.value.trim().split('\n')
  logs.value = lines.filter(line => line.trim()).map(line => {
    const parts = line.split('|')
    return {
      timestamp: parts[0] || new Date().toISOString(),
      level: parts[1] || 'INFO',
      message: parts.slice(2).join('|') || line
    }
  })
}

function generateMockLogs() {
  const mockLogs = [
    { timestamp: '2024-01-15T10:00:00Z', level: 'INFO', message: 'User login successful: user_id=123' },
    { timestamp: '2024-01-15T10:00:01Z', level: 'INFO', message: 'User login successful: user_id=456' },
    { timestamp: '2024-01-15T10:00:02Z', level: 'INFO', message: 'User login successful: user_id=789' },
    { timestamp: '2024-01-15T10:00:03Z', level: 'ERROR', message: 'Database connection failed: timeout' },
    { timestamp: '2024-01-15T10:00:04Z', level: 'WARN', message: 'High memory usage detected: 85%' },
    { timestamp: '2024-01-15T10:00:05Z', level: 'INFO', message: 'API request received: GET /api/users' },
    { timestamp: '2024-01-15T10:00:06Z', level: 'INFO', message: 'API request received: POST /api/orders' },
    { timestamp: '2024-01-15T10:00:07Z', level: 'ERROR', message: 'Database connection failed: timeout' },
    { timestamp: '2024-01-15T10:00:08Z', level: 'DEBUG', message: 'Cache hit for key: user_123' },
    { timestamp: '2024-01-15T10:00:09Z', level: 'INFO', message: 'User logout: user_id=123' },
    { timestamp: '2024-01-15T10:00:10Z', level: 'WARN', message: 'Slow query detected: SELECT * FROM orders' },
    { timestamp: '2024-01-15T10:00:11Z', level: 'INFO', message: 'User login successful: user_id=101' },
    { timestamp: '2024-01-15T10:00:12Z', level: 'INFO', message: 'API request received: GET /api/products' },
    { timestamp: '2024-01-15T10:00:13Z', level: 'FATAL', message: 'Critical error: Service unavailable' },
    { timestamp: '2024-01-15T10:00:14Z', level: 'INFO', message: 'User login successful: user_id=202' },
    { timestamp: '2024-01-15T10:00:15Z', level: 'WARN', message: 'High memory usage detected: 90%' },
    { timestamp: '2024-01-15T10:00:16Z', level: 'INFO', message: 'API request received: PUT /api/users/123' },
    { timestamp: '2024-01-15T10:00:17Z', level: 'DEBUG', message: 'Cache miss for key: product_456' },
    { timestamp: '2024-01-15T10:00:18Z', level: 'INFO', message: 'User login successful: user_id=303' },
    { timestamp: '2024-01-15T10:00:19Z', level: 'ERROR', message: 'API request failed: 500 Internal Server Error' },
    { timestamp: '2024-01-15T10:00:20Z', level: 'INFO', message: 'User login successful: user_id=404' },
  ]
  logs.value = mockLogs
  logInput.value = mockLogs.map(log => `${log.timestamp}|${log.level}|${log.message}`).join('\n')
}

function clearLogs() {
  logInput.value = ''
  logs.value = []
  analysisResult.value = null
}

async function runAnalysis() {
  if (logs.value.length === 0) return
  loading.value = true
  analysisResult.value = null
  try {
    const response = await logAnalysis({
      logs: logs.value,
      top_n: 10,
      anomaly_threshold: 0.05,
      max_clusters: 10
    })
    analysisResult.value = response.data
  } catch (error) {
    console.error('分析失败:', error)
    alert('分析失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleString('zh-CN')
}

function truncate(str, length) {
  if (str.length <= length) return str
  return str.substring(0, length) + '...'
}
</script>

<style scoped>
.yy-page {
  min-height: 100vh;
  padding: 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
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
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
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
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover:not(:disabled) {
  background: rgba(16, 185, 129, 0.2);
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

.log-input-panel,
.log-list-panel {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;
  background: #f8fafc;
}

.panel-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.log-count {
  font-size: 12px;
  color: #64748b;
}

.log-textarea {
  width: 100%;
  height: 200px;
  padding: 12px;
  border: none;
  resize: none;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.5;
  box-sizing: border-box;
}

.textarea-actions {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #e8e8e8;
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
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #fff;
}

.btn-secondary {
  background: #e2e8f0;
  color: #475569;
}

.btn-large {
  width: 100%;
  padding: 12px 20px;
  font-size: 14px;
}

.log-list-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.log-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.log-item {
  display: flex;
  gap: 8px;
  padding: 6px 10px;
  margin-bottom: 4px;
  border-radius: 4px;
  font-size: 12px;
  background: #f8fafc;
}

.log-item.info {
  border-left: 3px solid #3b82f6;
}

.log-item.warn {
  border-left: 3px solid #f59e0b;
}

.log-item.error {
  border-left: 3px solid #ef4444;
}

.log-item.debug {
  border-left: 3px solid #6b7280;
}

.log-item.fatal {
  border-left: 3px solid #991b1b;
}

.log-timestamp {
  color: #64748b;
  font-family: monospace;
  white-space: nowrap;
}

.log-level {
  font-weight: 600;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 3px;
  white-space: nowrap;
}

.log-item.info .log-level {
  background: #dbeafe;
  color: #1e40af;
}

.log-item.warn .log-level {
  background: #fef3c7;
  color: #d97706;
}

.log-item.error .log-level {
  background: #fee2e2;
  color: #dc2626;
}

.log-item.debug .log-level {
  background: #f3f4f6;
  color: #4b5563;
}

.log-item.fatal .log-level {
  background: #fecaca;
  color: #991b1b;
}

.log-message {
  flex: 1;
  color: #374151;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #94a3b8;
}

.empty-state.success {
  color: #059669;
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
  border-top-color: #10b981;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.right-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tabs {
  display: flex;
  gap: 8px;
  background: #fff;
  padding: 8px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
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
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.tab-btn.active {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #fff;
}

.tab-content {
  flex: 1;
  min-height: 500px;
}

.result-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e8e8e8;
  background: #f8fafc;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.result-summary {
  font-size: 13px;
  color: #64748b;
}

.pattern-list,
.anomaly-list,
.cluster-list {
  padding: 16px;
}

.pattern-item,
.anomaly-item,
.cluster-item {
  padding: 12px;
  margin-bottom: 12px;
  background: #f8fafc;
  border-radius: 6px;
}

.pattern-item:last-child,
.anomaly-item:last-child,
.cluster-item:last-child {
  margin-bottom: 0;
}

.pattern-header,
.anomaly-header,
.cluster-header {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.pattern-rank {
  font-weight: 600;
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.pattern-count,
.pattern-percentage,
.anomaly-count,
.cluster-count {
  font-size: 12px;
  color: #64748b;
}

.pattern-text {
  font-family: monospace;
  font-size: 13px;
  color: #1e293b;
  margin-bottom: 8px;
}

.pattern-examples {
  margin-bottom: 8px;
}

.example-title {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
}

.example-item {
  font-size: 12px;
  color: #475569;
  padding: 2px 0;
}

.pattern-severity,
.cluster-severity {
  display: flex;
  gap: 8px;
}

.severity-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 3px;
  background: #e2e8f0;
  color: #475569;
}

.anomaly-level {
  font-weight: 600;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.anomaly-level.info {
  background: #dbeafe;
  color: #1e40af;
}

.anomaly-level.warn {
  background: #fef3c7;
  color: #d97706;
}

.anomaly-level.error {
  background: #fee2e2;
  color: #dc2626;
}

.anomaly-level.fatal {
  background: #fecaca;
  color: #991b1b;
}

.anomaly-pattern {
  font-family: monospace;
  font-size: 13px;
  color: #dc2626;
  margin-bottom: 8px;
}

.anomaly-details {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 8px;
}

.anomaly-message {
  font-size: 12px;
  color: #374151;
}

.cluster-id {
  font-weight: 600;
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.cluster-pattern {
  font-size: 13px;
  color: #1e293b;
  margin-bottom: 8px;
}

.cluster-representative {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 12px;
}

.rep-label {
  color: #64748b;
}

.rep-text {
  color: #374151;
}
</style>
