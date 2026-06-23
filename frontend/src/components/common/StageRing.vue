<template>
  <div class="stage-ring" :class="{ 'is-placeholder': isPlaceholder }">
    <ol class="steps" role="list">
      <li
        v-for="(stage, index) in displayStages"
        :key="index"
        class="step"
        :class="`status-${stage.status || 'pending'}`"
      >
        <span class="connector" v-if="index > 0" aria-hidden="true" />
        <span class="ring" aria-hidden="true">
          <span class="ring-inner">{{ index + 1 }}</span>
        </span>
        <span class="name">{{ stage.name }}</span>
        <span v-if="stage.duration" class="duration tabular-nums">{{ stage.duration }}</span>
      </li>
    </ol>
    <p v-if="isPlaceholder" class="placeholder-note">
      node_trace 分析阶段环占位（取上下文 → 关联分析 → 根因推断 → 定级 → 成文）
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** 阶段节点：{ name, status: pending|running|done|error, duration? } */
  stages: { type: Array, default: () => [] }
})

const DEFAULT_STAGES = [
  { name: '取上下文', status: 'pending' },
  { name: '关联分析', status: 'pending' },
  { name: '根因推断', status: 'pending' },
  { name: '定级', status: 'pending' },
  { name: '成文', status: 'pending' }
]

const isPlaceholder = computed(() => props.stages.length === 0)

const displayStages = computed(() =>
  isPlaceholder.value ? DEFAULT_STAGES : props.stages
)
</script>

<style scoped>
.stage-ring {
  padding: var(--spacing-md);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.stage-ring.is-placeholder .step {
  opacity: 0.75;
}

.steps {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--spacing-sm) 0;
  list-style: none;
  margin: 0;
  padding: 0;
}

.step {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 72px;
  padding: 0 var(--spacing-sm);
  text-align: center;
}

.connector {
  position: absolute;
  top: 14px;
  right: calc(50% + 18px);
  width: calc(100% - 36px);
  height: 2px;
  background: var(--color-border);
  transform: translateX(-50%);
}

.ring {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid var(--color-border);
  background: var(--color-bg);
  transition: border-color 0.25s ease-out, background 0.25s ease-out;
}

.ring-inner {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
}

.name {
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.3;
  max-width: 80px;
}

.duration {
  margin-top: 2px;
  font-size: 11px;
  color: var(--color-text-muted);
}

.status-running .ring {
  border-color: var(--color-primary);
  background: var(--color-info-bg);
}

.status-running .ring-inner {
  color: var(--color-primary);
}

.status-done .ring {
  border-color: var(--color-success);
  background: var(--color-success-bg);
}

.status-done .ring-inner {
  color: var(--color-success);
}

.status-error .ring {
  border-color: var(--color-danger);
  background: var(--color-danger-bg);
}

.status-error .ring-inner {
  color: var(--color-danger);
}

.placeholder-note {
  margin: var(--spacing-md) 0 0;
  padding-top: var(--spacing-sm);
  border-top: 1px dashed var(--color-border);
  font-size: 12px;
  color: var(--color-text-muted);
  text-align: center;
}

@media (prefers-reduced-motion: reduce) {
  .ring {
    transition: none;
  }
}
</style>
