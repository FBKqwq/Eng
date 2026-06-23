<template>
  <section class="page-section verify-panel">
    <header class="panel-header">
      <div>
        <h2>链路验证</h2>
        <p class="panel-desc">一键触发全链路验证，输出等宽终端日志（F3 阶段迁移现有能力）</p>
      </div>
      <span class="pending-tag">待接入：POST /system/pipeline/verify</span>
    </header>

    <div class="verify-toolbar">
      <label class="workers-field">
        <span>并发 workers</span>
        <input
          type="number"
          min="1"
          max="8"
          :value="workers"
          disabled
          class="workers-input"
        />
      </label>
      <button type="button" class="verify-btn" disabled>
        一键验证
      </button>
    </div>

    <details class="output-fold" open>
      <summary>验证输出</summary>
      <pre class="output-terminal" aria-label="验证输出占位"><code>{{ placeholderOutput }}</code></pre>
    </details>
  </section>
</template>

<script setup>
defineProps({
  workers: { type: Number, default: 2 },
  running: { type: Boolean, default: false },
  output: { type: [String, Array, Object], default: null },
  error: { type: String, default: '' }
})

const placeholderOutput = `# 验证输出占位 — F3 阶段接入 POST /system/pipeline/verify
# 预期步骤：日志生产 → Kafka → Logstash → Elasticsearch
[--] 等待触发验证...
[--] workers=2（默认，与旧系统页一致）`
</script>

<style scoped>
.verify-panel {
  margin-bottom: 0;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.panel-header h2 {
  margin: 0;
}

.panel-desc {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.pending-tag {
  flex-shrink: 0;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 12px;
  font-weight: 500;
}

.verify-toolbar {
  display: flex;
  align-items: flex-end;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.workers-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.workers-input {
  width: 72px;
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  font-size: 14px;
  font-variant-numeric: tabular-nums;
  color: var(--color-text-secondary);
}

.verify-btn {
  padding: 8px 20px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  opacity: 0.5;
  cursor: not-allowed;
}

.output-fold {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: #1a1d23;
  overflow: hidden;
}

.output-fold summary {
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  user-select: none;
}

.output-terminal {
  margin: 0;
  padding: 14px 16px;
  font-family: ui-monospace, 'Cascadia Code', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #a8b3c5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 240px;
  overflow-y: auto;
}

.output-terminal code {
  font-family: inherit;
}
</style>
