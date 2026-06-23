<template>
  <section class="suggestion-panel page-section">
    <h2>建议区</h2>
    <ul class="checklist" role="list">
      <li v-for="item in placeholderItems" :key="item" class="checklist-item">
        <input type="checkbox" disabled :aria-label="item" />
        <span>{{ item }}</span>
      </li>
    </ul>
    <p class="checklist-note">suggestions 可勾选核对清单（前端演示态，F5 阶段接入）</p>
    <div class="stage-section">
      <p class="stage-label">分析阶段</p>
      <StageRing />
    </div>
  </section>
</template>

<script setup>
import StageRing from '../common/StageRing.vue'

const placeholderItems = [
  '检查 order-service 连接池配置',
  '回滚近期 payment-service 变更',
  '扩容 inventory-service 实例'
]
</script>

<style scoped>
.suggestion-panel {
  margin-bottom: 0;
}

.checklist {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.checklist-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.checklist-note {
  margin: var(--spacing-sm) 0 0;
  font-size: 11px;
  color: var(--color-text-muted);
}

.stage-section {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px dashed var(--color-border);
}

.stage-label {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
}
</style>
