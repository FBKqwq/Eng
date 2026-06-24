<template>
  <div class="prediction-panel">
    <div class="panel-header">
      <h3>预测参数配置</h3>
      <div class="header-actions">
        <button class="btn btn-primary" @click="runPrediction" :disabled="isGenerating">
          <span class="btn-icon">📊</span>
          {{ isGenerating ? '生成中...' : '执行预测' }}
        </button>
      </div>
    </div>
    
    <div class="panel-body">
      <div class="form-row">
        <div class="form-group">
          <label>指标名称</label>
          <input 
            v-model="form.metric_name" 
            type="text" 
            placeholder="如: error_rate, response_time"
            class="form-control"
          />
        </div>
        
        <div class="form-group">
          <label>预测步数</label>
          <select v-model="form.forecast_steps" class="form-control">
            <option :value="3">3 步</option>
            <option :value="5">5 步</option>
            <option :value="10">10 步</option>
            <option :value="15">15 步</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>数据间隔(分钟)</label>
          <select v-model="form.interval_minutes" class="form-control">
            <option :value="1">1</option>
            <option :value="5">5</option>
            <option :value="15">15</option>
            <option :value="30">30</option>
            <option :value="60">60</option>
          </select>
        </div>
      </div>
      
      <div class="form-row">
        <div class="form-group">
          <label>异常检测方法</label>
          <select v-model="form.detect_method" class="form-control">
            <option value="zscore">Z-Score (标准差法)</option>
            <option value="iqr">IQR (四分位距法)</option>
            <option value="mad">MAD (绝对中位差法)</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>趋势预测方法</label>
          <select v-model="form.predict_method" class="form-control">
            <option value="linear">线性回归</option>
            <option value="moving_average">移动平均</option>
            <option value="exponential_smoothing">指数平滑</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>异常阈值</label>
          <input 
            v-model.number="form.threshold" 
            type="number" 
            min="0.5" 
            max="5" 
            step="0.1"
            class="form-control"
          />
        </div>
      </div>
      
      <div class="form-group">
        <label>模拟数据生成</label>
        <div class="simulate-controls">
          <button 
            class="btn btn-secondary" 
            @click="handleGenerateMockData"
            :disabled="isGenerating"
            :class="{ generating: isGenerating }"
          >
            <span v-if="isGenerating" class="spinner-small"></span>
            <span v-else>🎲</span>
            {{ isGenerating ? '生成中...' : '生成模拟数据' }}
          </button>
          <span class="data-count" :class="{ updated: justUpdated }">
            当前 {{ mockData.length }} 个数据点
          </span>
        </div>
        
        <!-- 数据预览 -->
        <div class="data-preview" v-if="mockData.length > 0">
          <div class="preview-header">
            <span>数据预览</span>
            <button class="preview-close" @click="clearPreview">✕</button>
          </div>
          <div class="preview-content">
            <div class="preview-row header-row">
              <span>时间</span>
              <span>数值</span>
            </div>
            <div 
              v-for="(item, index) in mockData.slice(-5)" 
              :key="index" 
              class="preview-row"
              :class="{ anomaly: item.is_anomaly }"
            >
              <span>{{ formatTime(item.timestamp) }}</span>
              <span>{{ item.value }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const emit = defineEmits(['predict'])

const form = reactive({
  metric_name: 'error_rate',
  forecast_steps: 5,
  interval_minutes: 5,
  detect_method: 'zscore',
  predict_method: 'linear',
  threshold: 2.0
})

const mockData = ref([])
const isGenerating = ref(false)
const justUpdated = ref(false)

function generateMockData() {
  const data = []
  const now = Date.now()
  const interval = form.interval_minutes * 60 * 1000
  let value = 5
  
  for (let i = 20; i >= 0; i--) {
    const timestamp = new Date(now - i * interval).toISOString()
    // 添加一些随机波动和异常点
    const noise = (Math.random() - 0.5) * 2
    const trend = i > 15 ? 0 : (15 - i) * 0.1
    let pointValue = value + noise + trend
    let isAnomaly = false
    
    // 随机添加异常点
    if (i === 10 && Math.random() > 0.5) {
      pointValue += 10
      isAnomaly = true
    }
    if (i === 5 && Math.random() > 0.5) {
      pointValue -= 8
      isAnomaly = true
    }
    
    data.push({
      timestamp,
      value: parseFloat(pointValue.toFixed(2)),
      is_anomaly: isAnomaly
    })
  }
  
  return data
}

async function handleGenerateMockData() {
  isGenerating.value = true
  
  // 添加延迟让用户看到加载状态
  await new Promise(resolve => setTimeout(resolve, 500))
  
  mockData.value = generateMockData()
  justUpdated.value = true
  
  // 3秒后移除更新提示样式
  setTimeout(() => {
    justUpdated.value = false
  }, 3000)
  
  isGenerating.value = false
}

function runPrediction() {
  if (mockData.value.length === 0) {
    mockData.value = generateMockData()
  }
  
  emit('predict', {
    ...form,
    data: mockData.value.map(item => ({
      timestamp: item.timestamp,
      value: item.value
    }))
  })
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function clearPreview() {
  mockData.value = []
}

// 初始化生成一些模拟数据
mockData.value = generateMockData()
</script>

<style scoped>
.prediction-panel {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e8e8e8;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.header-actions .btn {
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
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

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.btn-secondary {
  background: #e2e8f0;
  color: #475569;
}

.btn-secondary:hover:not(:disabled) {
  background: #cbd5e1;
}

.btn-secondary.generating {
  background: #dbeafe;
  color: #1e40af;
}

.spinner-small {
  width: 14px;
  height: 14px;
  border: 2px solid #cbd5e1;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.panel-body {
  padding: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: #475569;
}

.form-control {
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-control:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.simulate-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.data-count {
  font-size: 13px;
  color: #64748b;
  transition: all 0.3s;
}

.data-count.updated {
  color: #22c55e;
  font-weight: 600;
}

.data-preview {
  margin-top: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}

.preview-close {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 14px;
  padding: 2px 4px;
}

.preview-close:hover {
  color: #64748b;
}

.preview-content {
  max-height: 120px;
  overflow-y: auto;
}

.preview-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 12px;
  color: #64748b;
}

.preview-row.header-row {
  font-weight: 600;
  color: #475569;
  border-bottom: 1px dashed #e2e8f0;
  margin-bottom: 4px;
}

.preview-row.anomaly {
  color: #dc2626;
  background: rgba(220, 38, 38, 0.05);
  padding: 4px 8px;
  border-radius: 4px;
  margin: 2px 0;
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
