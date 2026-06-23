<template>
  <section class="suggestion-panel page-section">
    <h2>建议区</h2>

    <ul v-if="displayItems.length" class="checklist" role="list">
      <li v-for="(item, index) in displayItems" :key="`${index}-${item}`" class="checklist-item">
        <input
          :id="`suggestion-${index}`"
          type="checkbox"
          class="checklist-checkbox"
          :checked="isChecked(index)"
          :aria-label="item"
          @change="toggleChecked(index)"
        />
        <label :for="`suggestion-${index}`" class="checklist-label" :class="{ 'is-checked': isChecked(index) }">
          {{ item }}
        </label>
      </li>
    </ul>
    <p v-else class="checklist-empty">暂无处置建议</p>

    <p v-if="displayItems.length" class="checklist-note">
      处置勾选仅作为当前页面的本地进度标记
    </p>

    <div class="stage-section">
      <LangGraphFlow :node-trace="nodeTrace" :degraded="degraded" />
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import LangGraphFlow from './LangGraphFlow.vue'

const props = defineProps({
  /** 处置建议文案列表 */
  suggestions: { type: Array, default: () => [] },
  /** 分析轨迹，来自 analysis/run 或 report.node_trace */
  nodeTrace: { type: Array, default: () => [] },
  /** 规则/统计降级标记 */
  degraded: { type: Boolean, default: false }
})

const checkedMap = ref({})

const displayItems = computed(() =>
  (props.suggestions || []).filter((item) => typeof item === 'string' && item.trim())
)

watch(
  displayItems,
  (items) => {
    const next = {}
    items.forEach((_, index) => {
      next[index] = Boolean(checkedMap.value[index])
    })
    checkedMap.value = next
  },
  { immediate: true }
)

function isChecked(index) {
  return Boolean(checkedMap.value[index])
}

function toggleChecked(index) {
  checkedMap.value = {
    ...checkedMap.value,
    [index]: !checkedMap.value[index]
  }
}
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

.checklist-checkbox {
  margin-top: 2px;
  flex-shrink: 0;
  cursor: pointer;
}

.checklist-label {
  cursor: pointer;
  transition: color 0.15s ease-out, opacity 0.15s ease-out;
}

.checklist-label.is-checked {
  color: var(--color-text-muted);
  text-decoration: line-through;
  opacity: 0.75;
}

.checklist-empty {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-muted);
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

@media (prefers-reduced-motion: reduce) {
  .checklist-label {
    transition: none;
  }
}
</style>
