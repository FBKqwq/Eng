<template>
  <aside class="alert-drawer" aria-label="预警详情抽屉占位">
    <header class="alert-drawer__header">
      <h3>预警详情</h3>
      <span class="drawer-badge">右侧抽屉占位</span>
    </header>
    <div class="alert-drawer__sections">
      <section v-for="block in sections" :key="block.title" class="detail-section">
        <h4>{{ block.title }}</h4>
        <p>{{ block.content }}</p>
      </section>
    </div>
    <button type="button" class="diagnosis-link" disabled>发起深度诊断</button>
    <p class="drawer-note">alert_chain 解释文案按「现象 / 影响 / 建议」三段版式渲染，禁止聊天气泡（F6 阶段）</p>
  </aside>
</template>

<script setup>
const sections = [
  { title: '现象', content: '预警触发现象描述占位（版式化文本，非对话流）' },
  { title: '影响', content: '业务影响范围与严重度说明占位' },
  { title: '建议', content: '初步处置建议要点占位' }
]
</script>

<style scoped>
.alert-drawer {
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
  max-width: 360px;
  margin-left: auto;
}

.alert-drawer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--color-border);
}

.alert-drawer__header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.drawer-badge {
  font-size: 11px;
  color: var(--color-text-muted);
}

.detail-section {
  margin-bottom: var(--spacing-md);
}

.detail-section h4 {
  margin: 0 0 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
}

.detail-section p {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.diagnosis-link {
  width: 100%;
  padding: 8px 16px;
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-primary);
  font-size: 13px;
  opacity: 0.5;
  cursor: not-allowed;
}

.drawer-note {
  margin: var(--spacing-sm) 0 0;
  font-size: 11px;
  color: var(--color-text-muted);
  line-height: 1.4;
}
</style>
