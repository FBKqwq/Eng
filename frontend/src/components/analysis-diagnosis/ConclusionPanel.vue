<template>
  <div class="conclusion-panel">
    <div class="gauge-row page-grid page-grid-2">
      <div class="gauge-slot">
        <p class="gauge-label">严重度</p>
        <GaugeChart title="严重度" placeholder="severity 四段式仪表（low/medium/high/critical）" height="200px" />
      </div>
      <div class="gauge-slot">
        <p class="gauge-label">置信度</p>
        <GaugeChart title="置信度" placeholder="confidence 0~1 环形进度" height="200px" />
      </div>
    </div>

    <div class="meta-row">
      <SeverityBadge level="medium" label="异常类型占位" />
      <span class="service-tag">受影响服务占位</span>
    </div>

    <article class="root-cause-card">
      <header class="root-cause-card__header">
        <h3>根因结论</h3>
        <span class="rule-badge">规则判定角标占位</span>
      </header>
      <p class="root-cause-card__headline">结论一句话占位（加粗渲染 root_cause 摘要）</p>
      <ul class="root-cause-card__points">
        <li>推理依据要点占位 1</li>
        <li>推理依据要点占位 2</li>
        <li>推理依据要点占位 3</li>
      </ul>
      <p class="pending-note">版式化卡片渲染，禁止聊天气泡 / 对话框形态</p>
    </article>
  </div>
</template>

<script setup>
import GaugeChart from '../common/charts/GaugeChart.vue'
import SeverityBadge from '../common/SeverityBadge.vue'
</script>

<style scoped>
.conclusion-panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.gauge-label {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.service-tag {
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  font-size: 12px;
  color: var(--color-text-muted);
}

.root-cause-card {
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
  border-left: 3px solid var(--color-primary);
}

.root-cause-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: var(--spacing-sm);
}

.root-cause-card__header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.rule-badge {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  border: 1px dashed var(--color-border);
  font-size: 11px;
  color: var(--color-text-muted);
}

.root-cause-card__headline {
  margin: 0 0 var(--spacing-sm);
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.5;
}

.root-cause-card__points {
  margin: 0;
  padding-left: 1.2em;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.pending-note {
  margin: var(--spacing-sm) 0 0;
  font-size: 11px;
  color: var(--color-text-muted);
}
</style>
