<template>
  <section class="analysis-workbench" :class="`analysis-workbench--${tone}`">
    <div class="analysis-workbench__grid" aria-hidden="true" />
    <Teleport v-if="actionsTargetReady" to="#topbar-page-actions">
      <slot name="actions" />
    </Teleport>
    <slot />
  </section>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watchEffect } from 'vue'
import { usePageHeader } from '../../composables/usePageHeader.js'

const props = defineProps({
  title: { type: String, required: true },
  eyebrow: { type: String, default: 'LANGGRAPH OPS / TACTICAL UI' },
  subtitle: { type: String, default: '' },
  tone: {
    type: String,
    default: 'blue',
    validator: (value) => ['blue', 'red', 'amber', 'green', 'slate', 'violet'].includes(value)
  }
})

const headerSource = Symbol('analysis-workbench-header')
const actionsTargetReady = ref(false)
const { setPageHeader, clearPageHeader } = usePageHeader()

watchEffect(() => {
  setPageHeader(headerSource, {
    title: props.title,
    eyebrow: props.eyebrow,
    subtitle: props.subtitle,
    tone: props.tone
  })
})

onBeforeUnmount(() => {
  clearPageHeader(headerSource)
})

onMounted(() => {
  actionsTargetReady.value = true
})
</script>

<style scoped>
.analysis-workbench {
  --workbench-accent: #6f9eac;
  --workbench-accent-rgb: 111, 158, 172;
  --workbench-danger: #b96a61;
  --workbench-warning: #b28b5a;
  --workbench-success: #6d9482;
  --workbench-line: rgba(181, 193, 205, 0.18);
  --workbench-line-strong: rgba(213, 222, 232, 0.34);
  --workbench-panel: rgba(13, 17, 22, 0.9);
  --workbench-panel-2: rgba(24, 29, 36, 0.86);
  position: relative;
  min-height: calc(100vh - 90px);
  padding: 12px;
  overflow: hidden;
  color: #e6edf3;
  background:
    linear-gradient(135deg, #05070a 0%, #11161d 43%, #070a0e 100%),
    #080b10;
  border: 0;
  border-radius: 0;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.045), 0 18px 42px rgba(0, 0, 0, 0.28);
}

.analysis-workbench::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, transparent 0 23px, rgba(var(--workbench-accent-rgb), 0.08) 23px 24px, transparent 24px),
    linear-gradient(180deg, transparent 0 23px, rgba(255, 255, 255, 0.045) 23px 24px, transparent 24px);
  background-size: 48px 48px;
  mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.44), transparent 62%);
}

.analysis-workbench::after {
  content: '';
  position: absolute;
  top: 0;
  left: 18px;
  width: 220px;
  height: 4px;
  background: var(--workbench-accent);
  box-shadow: 0 0 18px rgba(var(--workbench-accent-rgb), 0.48);
  clip-path: polygon(0 0, calc(100% - 26px) 0, 100% 100%, 0 100%);
}

.analysis-workbench--red {
  --workbench-accent: #b96a61;
  --workbench-accent-rgb: 185, 106, 97;
}

.analysis-workbench--amber {
  --workbench-accent: #b28b5a;
  --workbench-accent-rgb: 178, 139, 90;
}

.analysis-workbench--green {
  --workbench-accent: #6d9482;
  --workbench-accent-rgb: 109, 148, 130;
}

.analysis-workbench--violet,
.analysis-workbench--slate,
.analysis-workbench--blue {
  --workbench-accent: #6f9eac;
  --workbench-accent-rgb: 111, 158, 172;
}

.analysis-workbench__grid {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, rgba(var(--workbench-accent-rgb), 0.09), transparent 28%),
    linear-gradient(290deg, rgba(255, 255, 255, 0.035), transparent 25%);
  opacity: 0.75;
}

.analysis-workbench :deep(.ak-panel) {
  position: relative;
  z-index: 1;
  min-width: 0;
  padding: 10px;
  color: #dce4eb;
  background:
    linear-gradient(180deg, var(--workbench-panel-2), var(--workbench-panel));
  border: 1px solid var(--workbench-line);
  border-radius: 3px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 10px 24px rgba(0, 0, 0, 0.18);
}

.analysis-workbench :deep(.ak-panel::after) {
  content: '';
  position: absolute;
  top: -1px;
  right: -1px;
  width: 32px;
  height: 18px;
  border-top: 1px solid rgba(var(--workbench-accent-rgb), 0.62);
  border-right: 1px solid rgba(var(--workbench-accent-rgb), 0.62);
  clip-path: polygon(18px 0, 100% 0, 100% 100%, 0 100%);
  opacity: 0.75;
  pointer-events: none;
}

.analysis-workbench :deep(.ak-panel__title) {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 9px;
  color: #f0f4f8;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0;
}

.analysis-workbench :deep(.ak-panel__title::before) {
  content: '';
  width: 16px;
  height: 10px;
  flex: 0 0 auto;
  background: var(--workbench-accent);
  box-shadow: 0 0 14px rgba(var(--workbench-accent-rgb), 0.5);
  clip-path: polygon(0 0, 70% 0, 100% 100%, 0 100%);
}

.analysis-workbench :deep(.ak-muted) {
  color: #8c98a5;
}

.analysis-workbench :deep(.ak-button) {
  padding: 7px 12px;
  border: 1px solid rgba(var(--workbench-accent-rgb), 0.5);
  border-radius: 2px;
  background: rgba(var(--workbench-accent-rgb), 0.11);
  color: #e7f2f4;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  clip-path: polygon(0 0, calc(100% - 10px) 0, 100% 100%, 0 100%);
}

.analysis-workbench :deep(.ak-button:hover:not(:disabled)) {
  border-color: rgba(var(--workbench-accent-rgb), 0.8);
  background: rgba(var(--workbench-accent-rgb), 0.18);
}

.analysis-workbench :deep(.ak-button:disabled) {
  cursor: not-allowed;
  opacity: 0.48;
}

@media (max-width: 900px) {
  .analysis-workbench {
    padding: 9px;
  }
}
</style>
