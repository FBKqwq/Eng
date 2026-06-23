<template>
  <section class="entry-panel page-section">
    <h2>诊断输入</h2>
    <div class="entry-tabs" role="tablist">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        class="entry-tab"
        :class="{ active: activeTab === tab.id }"
        role="tab"
        :aria-selected="activeTab === tab.id"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>
    <div class="entry-body">
      <template v-if="activeTab === 'log'">
        <label class="field-label">异常日志</label>
        <textarea
          class="field-textarea"
          rows="6"
          placeholder="粘贴异常日志片段（F5 阶段提交诊断）"
          disabled
        />
      </template>
      <template v-else-if="activeTab === 'alert'">
        <label class="field-label">活跃预警</label>
        <div class="field-select-placeholder">选择活跃预警（待接入 GET /alerts/active）</div>
      </template>
      <template v-else>
        <label class="field-label">服务名称</label>
        <input class="field-input" type="text" placeholder="如 order-service" disabled />
        <label class="field-label">时间窗口</label>
        <div class="field-select-placeholder">跟随全局时间范围（useTimeRange）</div>
      </template>
      <button type="button" class="submit-btn" disabled>发起诊断</button>
    </div>
    <p class="pending-tag">待接入：POST /api/v1/diagnosis</p>
  </section>
</template>

<script setup>
import { ref } from 'vue'

const tabs = [
  { id: 'log', label: '粘贴日志' },
  { id: 'alert', label: '选择预警' },
  { id: 'service', label: '服务+时间窗' }
]

const activeTab = ref('log')
</script>

<style scoped>
.entry-panel {
  margin-bottom: 0;
}

.entry-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: var(--spacing-sm);
}

.entry-tab {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: border-color 0.15s ease-out, color 0.15s ease-out;
}

.entry-tab.active {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-info-bg);
}

.entry-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.field-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.field-textarea,
.field-input,
.field-select-placeholder {
  width: 100%;
  padding: 8px 10px;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  font-size: 13px;
  color: var(--color-text-muted);
  box-sizing: border-box;
}

.field-textarea {
  resize: vertical;
  min-height: 100px;
}

.field-select-placeholder {
  padding: 10px;
}

.submit-btn {
  margin-top: 4px;
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: #fff;
  font-size: 13px;
  opacity: 0.45;
  cursor: not-allowed;
}

.pending-tag {
  margin: var(--spacing-sm) 0 0;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 12px;
  text-align: center;
}

@media (prefers-reduced-motion: reduce) {
  .entry-tab {
    transition: none;
  }
}
</style>
