<template>
  <div class="loss-locator">
    <p class="loss-hint">选中异常步骤后，展示该步骤相关错误码 Top N</p>
    <BarChart
      horizontal
      height="200px"
      placeholder="错误码 Top N 条形图占位（behavior_funnel 聚合，F4/F7 阶段）"
    />
    <button type="button" class="jump-btn" disabled>跳转应用日志监控（带预置筛选）</button>
  </div>
</template>

<script setup>
import BarChart from '../common/charts/BarChart.vue'
</script>

<style scoped>
.loss-locator {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.loss-hint {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.jump-btn {
  align-self: flex-start;
  padding: 6px 14px;
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-primary);
  font-size: 12px;
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
