<template>
  <div class="root-cause-analysis">
    <div class="page-header">
      <h1 class="title">智能根因分析引擎</h1>
      <p class="subtitle">基于AI的自动化问题诊断与根因分析</p>
    </div>

    <div class="main-content">
      <div class="input-section">
        <div class="card">
          <div class="card-header">
            <span class="icon">🔍</span>
            <h2>问题描述</h2>
          </div>
          <div class="card-body">
            <textarea
              v-model="problemDescription"
              placeholder="请详细描述您遇到的问题，例如：&#10;订单服务数据库连接超时，API响应时间超过5秒，出现大量5xx错误..."
              rows="4"
              class="problem-input"
            ></textarea>
            <div class="context-section">
              <h3>附加上下文（可选）</h3>
              <textarea
                v-model="contextInfo"
                placeholder="可以粘贴相关日志片段、错误信息或指标数据..."
                rows="3"
                class="context-input"
              ></textarea>
            </div>
            <button
              @click="startAnalysis"
              :disabled="!problemDescription.trim() || isAnalyzing"
              class="analyze-btn"
            >
              <span v-if="isAnalyzing" class="loading">分析中...</span>
              <span v-else>🔮 开始智能分析</span>
            </button>
          </div>
        </div>
      </div>

      <div class="result-section" v-if="analysisResult">
        <div class="card">
          <div class="card-header">
            <span class="icon">📊</span>
            <h2>分析结果</h2>
            <span class="confidence-badge" :class="confidenceClass">
              置信度: {{ (analysisResult.confidence * 100).toFixed(0) }}%
            </span>
          </div>

          <div class="diagnosis-steps">
            <h3>诊断流程</h3>
            <div class="steps-container">
              <div
                v-for="(step, index) in analysisResult.steps"
                :key="index"
                class="step-item"
                :class="step.status"
              >
                <span class="step-number">{{ index + 1 }}</span>
                <div class="step-content">
                  <span class="step-name">{{ step.name }}</span>
                  <span class="step-status">{{ getStatusText(step.status) }}</span>
                </div>
                <span class="step-icon">{{ getStatusIcon(step.status) }}</span>
              </div>
            </div>
          </div>

          <div class="root-causes">
            <h3>可能的根因</h3>
            <div class="causes-container">
              <div
                v-for="(cause, index) in analysisResult.root_causes"
                :key="index"
                class="cause-card"
              >
                <div class="cause-header">
                  <span class="cause-rank">#{{ index + 1 }}</span>
                  <span class="cause-confidence" :style="{ width: (cause.confidence * 100) + '%' }"></span>
                </div>
                <div class="cause-content">
                  <p class="cause-title">{{ cause.cause }}</p>
                  <p class="cause-confidence-text">置信度: {{ (cause.confidence * 100).toFixed(0) }}%</p>
                  <div class="related-metrics">
                    <span class="metric-tag" v-for="metric in cause.related_metrics" :key="metric">
                      {{ metric }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="solutions">
            <h3>建议解决方案</h3>
            <div class="solutions-container">
              <div
                v-for="(solution, index) in analysisResult.solutions"
                :key="index"
                class="solution-card"
                :class="solution.priority"
              >
                <div class="solution-header">
                  <span class="solution-rank">{{ index + 1 }}</span>
                  <span class="solution-priority">{{ getPriorityText(solution.priority) }}</span>
                </div>
                <div class="solution-content">
                  <p class="solution-cause">问题原因: {{ solution.cause }}</p>
                  <p class="solution-text">解决方案: {{ solution.solution }}</p>
                </div>
                <button @click="showFeedback(index)" class="feedback-btn">
                  ✅ 反馈效果
                </button>
              </div>
            </div>
          </div>

          <div class="summary-section">
            <h3>分析摘要</h3>
            <pre class="summary-text">{{ analysisResult.summary }}</pre>
          </div>
        </div>
      </div>

      <div class="empty-state" v-if="!analysisResult && !isAnalyzing">
        <div class="empty-icon">🤖</div>
        <h3>智能根因分析引擎</h3>
        <p>输入问题描述，AI将自动分析可能的根本原因并提供解决方案</p>
        <div class="features">
          <div class="feature-item">
            <span class="feature-icon">🧠</span>
            <span>智能模式匹配</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">🔍</span>
            <span>多维度分析</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">💡</span>
            <span>自动生成解决方案</span>
          </div>
        </div>
      </div>
    </div>

    <div class="feedback-modal" v-if="showFeedbackModal" @click.self="closeFeedback">
      <div class="modal-content">
        <div class="modal-header">
          <h3>反馈解决方案效果</h3>
          <button @click="closeFeedback" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <p>请反馈第 {{ feedbackIndex + 1 }} 个解决方案的效果：</p>
          <textarea
            v-model="feedbackText"
            placeholder="请描述解决方案的执行效果，例如：问题已解决/部分解决/无效..."
            rows="3"
          ></textarea>
        </div>
        <div class="modal-footer">
          <button @click="closeFeedback" class="cancel-btn">取消</button>
          <button @click="submitFeedback" class="submit-btn">提交反馈</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>import { ref, computed } from 'vue';
import { analyzeRootCause, submitFeedback as apiSubmitFeedback } from '../../../api/root_cause.js';
const problemDescription = ref('');
const contextInfo = ref('');
const isAnalyzing = ref(false);
const analysisResult = ref(null);
const showFeedbackModal = ref(false);
const feedbackIndex = ref(0);
const feedbackText = ref('');
const confidenceClass = computed(() => {
 if (!analysisResult.value)
 return '';
 const conf = analysisResult.value.confidence;
 if (conf >= 0.8)
 return 'high';
 if (conf >= 0.5)
 return 'medium';
 return 'low';
});
function getStatusText(status) {
 const map = {
 pending: '待处理',
 completed: '已完成',
 failed: '失败'
 };
 return map[status] || status;
}
function getStatusIcon(status) {
 const map = {
 pending: '⏳',
 completed: '✓',
 failed: '✗'
 };
 return map[status] || '•';
}
function getPriorityText(priority) {
 const map = {
 high: '高优先级',
 medium: '中优先级',
 low: '低优先级'
 };
 return map[priority] || priority;
}
async function startAnalysis() {
 if (!problemDescription.value.trim())
 return;
 isAnalyzing.value = true;
 analysisResult.value = null;
 try {
 console.log('开始分析，问题描述:', problemDescription.value);
 const context = contextInfo.value.trim() ? { logs: contextInfo.value } : null;
 const response = await analyzeRootCause({
 problem_description: problemDescription.value,
 context
 });
 console.log('分析响应:', response);
 analysisResult.value = response.data;
 if (!analysisResult.value || analysisResult.value.status === 'failed') {
 throw new Error(analysisResult.value?.summary || '分析失败');
 }
 }
 catch (error) {
 console.error('分析失败:', error);
 console.error('错误详情:', error.response?.data || error.message);
 alert('分析失败，请稍后重试\n' + (error.response?.data?.message || error.message));
 }
 finally {
 isAnalyzing.value = false;
 }
}
function showFeedback(index) {
 feedbackIndex.value = index;
 feedbackText.value = '';
 showFeedbackModal.value = true;
}
function closeFeedback() {
 showFeedbackModal.value = false;
}
async function submitFeedback() {
 if (!feedbackText.value.trim()) {
 alert('请输入反馈内容');
 return;
 }
 try {
 await apiSubmitFeedback(analysisResult.value.analysis_id, {
 solution_index: feedbackIndex.value,
 feedback: feedbackText.value
 });
 alert('反馈提交成功，感谢您的反馈！');
 closeFeedback();
 }
 catch (error) {
 console.error('提交反馈失败:', error);
 alert('提交反馈失败');
 }
}
</script>

<style scoped>
.root-cause-analysis {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.title {
  font-size: 2rem;
  color: #fff;
  margin-bottom: 8px;
}

.subtitle {
  color: #8892b0;
  font-size: 1rem;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
}

.card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.card-header .icon {
  font-size: 1.5rem;
}

.card-header h2 {
  color: #fff;
  font-size: 1.25rem;
  font-weight: 600;
}

.confidence-badge {
  margin-left: auto;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 600;
}

.confidence-badge.high {
  background: rgba(46, 213, 115, 0.2);
  color: #2ed573;
}

.confidence-badge.medium {
  background: rgba(253, 203, 110, 0.2);
  color: #fdcb6e;
}

.confidence-badge.low {
  background: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
}

.card-body {
  padding: 24px;
}

.problem-input, .context-input {
  width: 100%;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
  font-family: inherit;
  font-size: 1rem;
  resize: vertical;
  box-sizing: border-box;
}

.problem-input::placeholder, .context-input::placeholder {
  color: #6b7280;
}

.context-section {
  margin-top: 16px;
}

.context-section h3 {
  color: #8892b0;
  font-size: 0.875rem;
  margin-bottom: 8px;
}

.analyze-btn {
  margin-top: 20px;
  padding: 14px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.analyze-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
}

.analyze-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading {
  display: flex;
  align-items: center;
  gap: 8px;
}

.loading::after {
  content: '';
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.diagnosis-steps, .root-causes, .solutions, .summary-section {
  padding: 20px 24px;
}

.diagnosis-steps h3, .root-causes h3, .solutions h3, .summary-section h3 {
  color: #8892b0;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 16px;
}

.steps-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
}

.step-item.completed {
  border-left: 3px solid #2ed573;
}

.step-item.failed {
  border-left: 3px solid #e74c3c;
}

.step-item.pending {
  border-left: 3px solid #fdcb6e;
}

.step-number {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  color: #8892b0;
  font-size: 0.875rem;
}

.step-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-name {
  color: #fff;
  font-size: 0.9rem;
}

.step-status {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 4px;
}

.step-item.completed .step-status {
  background: rgba(46, 213, 115, 0.2);
  color: #2ed573;
}

.step-item.failed .step-status {
  background: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
}

.step-item.pending .step-status {
  background: rgba(253, 203, 110, 0.2);
  color: #fdcb6e;
}

.step-icon {
  font-size: 1.25rem;
}

.causes-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.cause-card {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  overflow: hidden;
}

.cause-header {
  display: flex;
  align-items: center;
}

.cause-rank {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-weight: 600;
}

.cause-confidence {
  flex: 1;
  height: 36px;
  background: linear-gradient(90deg, #2ed573, #7bed9f);
  transition: width 0.5s ease;
}

.cause-content {
  padding: 16px;
}

.cause-title {
  color: #fff;
  font-size: 0.95rem;
  margin-bottom: 8px;
}

.cause-confidence-text {
  color: #8892b0;
  font-size: 0.8rem;
  margin-bottom: 12px;
}

.related-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.metric-tag {
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  color: #8892b0;
  font-size: 0.75rem;
}

.solutions-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.solution-card {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 16px;
  border-left: 4px solid;
}

.solution-card.high {
  border-left-color: #e74c3c;
}

.solution-card.medium {
  border-left-color: #fdcb6e;
}

.solution-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.solution-rank {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  color: #8892b0;
  font-size: 0.875rem;
}

.solution-priority {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.solution-card.high .solution-priority {
  background: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
}

.solution-card.medium .solution-priority {
  background: rgba(253, 203, 110, 0.2);
  color: #fdcb6e;
}

.solution-content {
  margin-bottom: 12px;
}

.solution-cause {
  color: #8892b0;
  font-size: 0.85rem;
  margin-bottom: 8px;
}

.solution-text {
  color: #fff;
  font-size: 0.95rem;
  line-height: 1.5;
}

.feedback-btn {
  padding: 8px 16px;
  background: rgba(46, 213, 115, 0.2);
  color: #2ed573;
  border: none;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.feedback-btn:hover {
  background: rgba(46, 213, 115, 0.3);
}

.summary-section {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
}

.summary-text {
  color: #8892b0;
  font-size: 0.9rem;
  line-height: 1.8;
  white-space: pre-wrap;
  margin: 0;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 20px;
}

.empty-state h3 {
  color: #fff;
  font-size: 1.5rem;
  margin-bottom: 12px;
}

.empty-state p {
  color: #8892b0;
  font-size: 1rem;
  margin-bottom: 30px;
}

.features {
  display: flex;
  justify-content: center;
  gap: 40px;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.feature-icon {
  font-size: 2rem;
}

.feature-item span:last-child {
  color: #8892b0;
  font-size: 0.9rem;
}

.feedback-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #1a1a2e;
  border-radius: 16px;
  width: 90%;
  max-width: 500px;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h3 {
  color: #fff;
  font-size: 1.1rem;
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  color: #8892b0;
  font-size: 1.5rem;
  cursor: pointer;
}

.modal-body {
  padding: 24px;
}

.modal-body p {
  color: #8892b0;
  margin-bottom: 12px;
}

.modal-body textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
  font-family: inherit;
  font-size: 0.9rem;
  resize: vertical;
  box-sizing: border-box;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.cancel-btn {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.1);
  color: #8892b0;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
}

.submit-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
}
</style>
