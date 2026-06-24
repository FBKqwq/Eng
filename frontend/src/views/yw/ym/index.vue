<template>
  <div class="log-qa-assistant">
    <div class="page-header">
      <button @click="goBack" class="back-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 18l-6-6 6-6"/>
        </svg>
        返回
      </button>
      <h1 class="title">AI 日志问答助手</h1>
      <p class="subtitle">基于大语言模型的智能日志分析与问答</p>
    </div>

    <div class="chat-container">
      <div class="chat-messages" ref="chatMessages">
        <div class="welcome-message">
          <div class="avatar bot">🤖</div>
          <div class="message-content">
            <div class="message-header">
              <span class="sender">AI 助手</span>
              <span class="time">{{ currentTime }}</span>
            </div>
            <p class="message-text">
              您好！我是您的AI日志助手，很高兴为您服务！😊
            </p>
            <p class="message-text">
              我可以帮助您查询和分析系统日志，支持多种自然语言提问方式。
            </p>
            <ul class="capabilities">
              <li>🔍 查询特定服务的日志</li>
              <li>⚠️ 分析错误和异常</li>
              <li>📊 生成日志摘要</li>
              <li>📈 识别趋势和模式</li>
              <li>🏷️ 智能日志分类</li>
              <li>🎯 根因分析增强</li>
              <li>🔮 趋势预测</li>
              <li>💡 智能修复建议</li>
            </ul>
            <p class="message-text">
              您可以试试这些问题：
            </p>
            <div class="quick-questions">
              <button class="quick-question" @click="sendQuickQuestion('最近有什么错误？')">最近有什么错误？</button>
              <button class="quick-question" @click="sendQuickQuestion('订单服务状态如何？')">订单服务状态如何？</button>
              <button class="quick-question" @click="sendQuickQuestion('帮我总结一下日志')">帮我总结一下日志</button>
              <button class="quick-question" @click="sendQuickQuestion('分析一下根因')">分析一下根因</button>
              <button class="quick-question" @click="sendQuickQuestion('预测一下趋势')">预测一下趋势</button>
            </div>
          </div>
        </div>

        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="chat-message"
          :class="msg.type"
        >
          <div class="avatar" :class="msg.type === 'user' ? 'user' : 'bot'">
            {{ msg.type === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="message-content">
            <div class="message-header">
              <span class="sender">{{ msg.type === 'user' ? '我' : 'AI 助手' }}</span>
              <span class="time">{{ msg.time }}</span>
            </div>
            <p v-if="msg.type === 'user'" class="message-text">{{ msg.question }}</p>
            <div v-if="msg.type === 'bot'" class="bot-response">
              <div class="confidence-badge">
                置信度: {{ (msg.confidence * 100).toFixed(0) }}%
              </div>
              <pre class="answer-text">{{ msg.answer }}</pre>
              <div v-if="msg.sources && msg.sources.length > 0" class="sources-section">
                <h4>📚 引用来源：</h4>
                <div class="sources-list">
                  <div v-for="(source, sIndex) in msg.sources.slice(0, 3)" :key="sIndex" class="source-item">
                    <span class="source-time">{{ source.timestamp }}</span>
                    <span class="source-level" :class="source.level.toLowerCase()">{{ source.level }}</span>
                    <span class="source-service">{{ source.service }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="isLoading" class="loading-message">
          <div class="avatar bot">🤖</div>
          <div class="message-content">
            <div class="loading-dots">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>
        </div>
      </div>

      <div class="input-area">
        <div class="quick-questions">
          <button
            v-for="(question, index) in quickQuestions"
            :key="index"
            @click="sendQuickQuestion(question)"
            class="quick-btn"
          >
            {{ question }}
          </button>
        </div>
        <div class="input-wrapper">
          <textarea
            v-model="inputMessage"
            placeholder="输入您的问题，例如：&#10;最近有哪些错误？&#10;订单服务的状态如何？&#10;帮我总结今天的日志..."
            rows="2"
            class="question-input"
            @keydown.enter.exact.prevent="sendMessage"
          ></textarea>
          <button
            @click="sendMessage"
            :disabled="!inputMessage.trim() || isLoading"
            class="send-btn"
          >
            <span v-if="!isLoading">发送</span>
            <span v-else class="loading-icon">⏳</span>
          </button>
        </div>
      </div>
    </div>

    <div class="tips-panel">
      <h3>💡 使用提示</h3>
      <ul>
        <li><strong>自然语言查询：</strong>直接用中文提问，不需要特定格式</li>
        <li><strong>服务查询：</strong>"订单服务有什么错误？"</li>
        <li><strong>摘要分析：</strong>"帮我总结今天的日志"</li>
        <li><strong>趋势分析：</strong>"最近的系统趋势如何？"</li>
      </ul>
    </div>
  </div>
</template>

<script setup>import { ref, computed, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { askLogQA } from '../../../api/log_qa.js';

const router = useRouter();

function goBack() {
  router.back();
}
const inputMessage = ref('');
const messages = ref([]);
const isLoading = ref(false);
const chatMessages = ref(null);
const quickQuestions = [
 '最近有哪些错误？',
 '订单服务的状态如何？',
 '帮我总结今天的日志',
 '分析一下系统趋势',
 '帮我分类这些日志',
 '分析问题根因',
 '预测系统趋势',
 '给出修复建议'
];
const currentTime = computed(() => {
 const now = new Date();
 return now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
});
function formatTime(date) {
 return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}
async function sendMessage() {
 if (!inputMessage.value.trim() || isLoading.value)
 return;
 const question = inputMessage.value.trim();
 inputMessage.value = '';
 messages.value.push({
 type: 'user',
 question: question,
 time: formatTime(new Date())
 });
 isLoading.value = true;
 await nextTick(() => {
 scrollToBottom();
 });
 try {
 const response = await askLogQA({ question });
 const data = response.data;
 messages.value.push({
 type: 'bot',
 question: question,
 answer: data.answer,
 confidence: data.confidence,
 sources: data.sources,
 time: formatTime(new Date())
 });
 }
 catch (error) {
 console.error('问答失败:', error);
 messages.value.push({
 type: 'bot',
 question: question,
 answer: '抱歉，我无法回答这个问题。请稍后重试。',
 confidence: 0,
 sources: [],
 time: formatTime(new Date())
 });
 }
 finally {
 isLoading.value = false;
 await nextTick(() => {
 scrollToBottom();
 });
 }
}
function sendQuickQuestion(question) {
 inputMessage.value = question;
 sendMessage();
}
function scrollToBottom() {
 if (chatMessages.value) {
 chatMessages.value.scrollTop = chatMessages.value.scrollHeight;
 }
}
</script>

<style scoped>
.log-qa-assistant {
  min-height: 100%;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding: 20px;
  box-sizing: border-box;
}

.page-header {
  text-align: center;
  margin-bottom: 20px;
  position: relative;
}

.back-btn {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: #8892b0;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.4);
}

.back-btn svg {
  width: 16px;
  height: 16px;
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

.chat-container {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 200px);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.welcome-message {
  display: flex;
  gap: 12px;
  animation: fadeIn 0.5s ease;
}

.chat-message {
  display: flex;
  gap: 12px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  flex-shrink: 0;
}

.avatar.user {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.avatar.bot {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.message-content {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 16px;
  max-width: 80%;
}

.chat-message.user .message-content {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%);
  margin-left: auto;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.sender {
  color: #fff;
  font-weight: 600;
  font-size: 0.9rem;
}

.time {
  color: #6b7280;
  font-size: 0.75rem;
}

.message-text {
  color: #e5e7eb;
  line-height: 1.5;
  margin: 0;
}

.capabilities {
  list-style: none;
  padding: 0;
  margin: 12px 0;
  color: #8892b0;
}

.capabilities li {
  padding: 4px 0;
}

.bot-response {
  margin-top: 12px;
}

.confidence-badge {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(46, 213, 115, 0.2);
  color: #2ed573;
  border-radius: 20px;
  font-size: 0.75rem;
  margin-bottom: 12px;
}

.answer-text {
  color: #e5e7eb;
  line-height: 1.8;
  white-space: pre-wrap;
  margin: 0;
  font-family: inherit;
}

.sources-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.sources-section h4 {
  color: #8892b0;
  font-size: 0.85rem;
  margin: 0 0 12px 0;
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  font-size: 0.8rem;
}

.source-time {
  color: #6b7280;
}

.source-level {
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.source-level.error {
  background: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
}

.source-level.warn {
  background: rgba(253, 203, 110, 0.2);
  color: #fdcb6e;
}

.source-level.info {
  background: rgba(52, 152, 219, 0.2);
  color: #3498db;
}

.source-service {
  color: #8892b0;
  margin-left: auto;
}

.loading-message {
  display: flex;
  gap: 12px;
}

.loading-dots {
  display: flex;
  gap: 6px;
  padding: 12px 16px;
}

.dot {
  width: 8px;
  height: 8px;
  background: #8892b0;
  border-radius: 50%;
  animation: loading 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }
.dot:nth-child(3) { animation-delay: 0s; }

@keyframes loading {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.input-area {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.quick-btn {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  color: #8892b0;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.quick-btn:hover {
  background: rgba(102, 126, 234, 0.3);
  border-color: rgba(102, 126, 234, 0.5);
  color: #fff;
}

.input-wrapper {
  display: flex;
  gap: 12px;
}

.question-input {
  flex: 1;
  padding: 14px 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
  font-family: inherit;
  font-size: 1rem;
  resize: none;
  box-sizing: border-box;
}

.question-input::placeholder {
  color: #6b7280;
}

.send-btn {
  padding: 14px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-icon {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.quick-question {
  padding: 6px 14px;
  background: rgba(102, 126, 234, 0.15);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 20px;
  color: #a5b4fc;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.quick-question:hover {
  background: rgba(102, 126, 234, 0.3);
  border-color: rgba(102, 126, 234, 0.5);
  transform: translateY(-1px);
}

.tips-panel {
  max-width: 900px;
  margin: 20px auto 0;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.tips-panel h3 {
  color: #8892b0;
  font-size: 0.9rem;
  margin: 0 0 12px 0;
}

.tips-panel ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.tips-panel li {
  color: #8892b0;
  font-size: 0.85rem;
  padding: 4px 0;
}

.tips-panel strong {
  color: #fff;
}
</style>
