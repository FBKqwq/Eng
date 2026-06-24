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
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

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
  padding: var(--industrial-panel-padding);
  border: var(--industrial-border-width) solid var(--industrial-border-color);
  border-radius: 0;
  background: var(--industrial-white);
}

.suggestion-panel h2 {
  margin: 0 0 var(--spacing-sm);
  font-size: 14px;
  font-weight: 700;
  color: var(--industrial-dark-gray);
  position: relative;
  padding-left: 16px;
}

.suggestion-panel h2::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 8px;
  height: 8px;
  background: var(--industrial-blue-cyan);
  clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%);
}

.checklist {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.checklist-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: var(--industrial-dark-gray);
  line-height: var(--industrial-line-height);
  padding: 8px 10px;
  border: 1px solid var(--industrial-border-color);
  border-radius: 0;
  background: var(--industrial-light-gray);
  position: relative;
  clip-path: polygon(
    0 0,
    calc(100% - var(--industrial-cut-size)) 0,
    100% var(--industrial-cut-size),
    100% 100%,
    0 100%
  );
}

.checklist-checkbox {
  margin-top: 2px;
  flex-shrink: 0;
  cursor: pointer;
  width: 14px;
  height: 14px;
  accent-color: var(--industrial-blue-cyan);
}

.checklist-label {
  cursor: pointer;
  transition: color 0.15s ease-out, opacity 0.15s ease-out;
  flex: 1;
}

.checklist-label.is-checked {
  color: var(--industrial-medium-gray);
  text-decoration: line-through;
  opacity: 0.75;
}

.checklist-empty {
  margin: 0;
  font-size: 13px;
  color: var(--industrial-medium-gray);
  text-align: center;
  padding: var(--spacing-md);
}

.checklist-note {
  margin: var(--spacing-sm) 0 0;
  font-size: 11px;
  color: var(--industrial-medium-gray);
}

.stage-section {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px dashed var(--industrial-border-color);
}

@media (prefers-reduced-motion: reduce) {
  .checklist-label {
    transition: none;
  }
}
</style>
