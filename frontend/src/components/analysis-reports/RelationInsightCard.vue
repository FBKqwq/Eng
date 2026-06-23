<template>
  <article class="relation-card">
    <header class="relation-card__header">
      <h3>隐藏关系发现</h3>
      <span class="relation-badge">relation_chain 占位</span>
    </header>
    <div class="relation-flow">
      <div class="metric-box">
        <p class="metric-name">左指标占位</p>
        <p class="metric-desc">请求高峰</p>
      </div>
      <span class="arrow" aria-hidden="true">→</span>
      <div class="metric-box">
        <p class="metric-name">右指标占位</p>
        <p class="metric-desc">支付失败上升</p>
      </div>
    </div>
    <p class="relation-note">附两条指标对照迷你折线图佐证（F7 阶段接入）</p>
  </article>
</template>

<script setup>
</script>

<style scoped>
.relation-card {
  padding: var(--spacing-md);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.relation-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: var(--spacing-sm);
}

.relation-card__header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.relation-badge {
  font-size: 11px;
  color: var(--color-text-muted);
}

.relation-flow {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.metric-box {
  flex: 1;
  min-width: 120px;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  text-align: center;
}

.metric-name {
  margin: 0;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text);
}

.metric-desc {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--color-text-muted);
}

.arrow {
  font-size: 20px;
  color: var(--color-primary);
  font-weight: 600;
}

.relation-note {
  margin: var(--spacing-sm) 0 0;
  font-size: 11px;
  color: var(--color-text-muted);
  text-align: center;
}
</style>
