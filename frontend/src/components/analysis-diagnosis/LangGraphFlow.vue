<template>
  <div class="langgraph-flow-card" :class="{ 'is-fill': fill }">
    <header v-if="showHeader" class="langgraph-flow-card__header">
      <div>
        <p class="langgraph-flow-card__eyebrow">LangGraph Inference</p>
        <h3>推断路径</h3>
      </div>
      <span v-if="degraded" class="mode-badge">规则降级</span>
    </header>

    <VueFlow
      class="langgraph-flow"
      :nodes="flowNodes"
      :edges="flowEdges"
      :fit-view-on-init="true"
      :nodes-draggable="false"
      :nodes-connectable="false"
      :elements-selectable="false"
      :zoom-on-scroll="false"
      :pan-on-scroll="false"
      :prevent-scrolling="false"
      :fit-view-options="fitViewOptions"
    >
      <template #node-diagnostic="{ data }">
        <div class="flow-node" :class="`flow-node--${data.status}`">
          <span class="flow-node__index">{{ data.index }}</span>
          <strong>{{ data.label }}</strong>
          <small>{{ data.detail }}</small>
        </div>
      </template>
    </VueFlow>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { VueFlow } from '@vue-flow/core'

const props = defineProps({
  nodeTrace: { type: Array, default: () => [] },
  degraded: { type: Boolean, default: false },
  showHeader: { type: Boolean, default: true },
  fill: { type: Boolean, default: false }
})

const BUSINESS_STAGES = [
  { key: 'context', label: '上下文取证' },
  { key: 'correlate', label: '事件关联' },
  { key: 'infer', label: '根因推断' },
  { key: 'grade', label: '风险定级' },
  { key: 'report', label: '结论成文' }
]

const NODE_STAGE_MAP = {
  log_fetch: 0,
  normalize_trigger: 0,
  build_state: 0,
  parse_trigger_event: 0,
  fetch_context: 0,
  build_time_window: 0,
  plan_queries: 0,
  aggregate_metrics: 0,
  sample_logs: 0,
  pattern_detect: 1,
  merge_result: 1,
  correlate_events: 1,
  build_evidence: 1,
  analyze_relations: 1,
  rule_diagnose: 2,
  infer_root_cause: 2,
  assess_severity: 3,
  main_alert_decision: 3,
  report_write: 4,
  main_persist_result: 4,
  generate_event_report: 4,
  generate_report: 4
}

function resolveStageIndex(nodeName) {
  const raw = String(nodeName || '').trim()
  const key = raw.includes('.') ? raw.split('.').pop() : raw
  const normalized = key.toLowerCase()
  if (NODE_STAGE_MAP[normalized] !== undefined) return NODE_STAGE_MAP[normalized]
  if (/fetch|log|sample|context|window|plan|aggregate|trigger|state/.test(normalized)) return 0
  if (/correlat|relation|evidence|pattern|merge/.test(normalized)) return 1
  if (/infer|root|diagnos|cause/.test(normalized)) return 2
  if (/severity|assess|alert|decision|grade/.test(normalized)) return 3
  if (/report|write|persist|generat/.test(normalized)) return 4
  return -1
}

function formatDuration(ms) {
  if (ms == null || Number.isNaN(Number(ms))) return ''
  const value = Number(ms)
  return value >= 1000 ? `${(value / 1000).toFixed(1)}s` : `${value}ms`
}

const stageState = computed(() => {
  const buckets = BUSINESS_STAGES.map((stage) => ({
    ...stage,
    status: 'pending',
    duration: 0,
    count: 0
  }))

  for (const entry of props.nodeTrace || []) {
    const index = resolveStageIndex(entry?.node_name)
    if (index < 0) continue
    const bucket = buckets[index]
    bucket.count += 1
    bucket.duration += Number(entry?.duration_ms) || 0
    if (entry?.status === 'failed') bucket.status = 'error'
    else if (entry?.status === 'running' && bucket.status !== 'error') bucket.status = 'running'
    else if (bucket.status === 'pending') bucket.status = 'done'
  }

  if (props.degraded) {
    for (const index of [1, 2, 3]) {
      if (!buckets[index].count) buckets[index].status = 'skipped'
    }
  }

  return buckets
})

const flowNodes = computed(() =>
  stageState.value.map((stage, index) => ({
    id: stage.key,
    type: 'diagnostic',
    position: props.fill
      ? { x: index * 188, y: index % 2 === 0 ? 24 : 132 }
      : { x: index * 168, y: index % 2 === 0 ? 20 : 104 },
    data: {
      index: String(index + 1).padStart(2, '0'),
      label: stage.label,
      status: stage.status,
      detail: stage.status === 'skipped'
        ? '已跳过'
        : stage.count
          ? `${stage.count} 节点 · ${formatDuration(stage.duration) || '已完成'}`
          : '等待执行'
    }
  }))
)

const fitViewOptions = computed(() => ({
  padding: props.fill ? 0.015 : 0.12
}))

const flowEdges = computed(() =>
  BUSINESS_STAGES.slice(0, -1).map((stage, index) => {
    const next = BUSINESS_STAGES[index + 1]
    const sourceState = stageState.value[index]
    return {
      id: `${stage.key}-${next.key}`,
      source: stage.key,
      target: next.key,
      animated: ['done', 'running'].includes(sourceState.status),
      type: 'smoothstep',
      style: {
        stroke: sourceState.status === 'error' ? '#dc2626' : '#2563eb',
        strokeWidth: 2
      }
    }
  })
)
</script>

<style scoped>
.langgraph-flow-card {
  height: 320px;
  padding: 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background:
    radial-gradient(circle at 12% 14%, rgba(37, 99, 235, 0.08), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.92));
  box-shadow: var(--shadow-card);
}

.langgraph-flow-card.is-fill {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 380px;
  padding: 8px;
  background:
    radial-gradient(circle at 12% 14%, rgba(37, 99, 235, 0.08), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.92));
  border-color: var(--color-border);
  box-shadow: var(--shadow-card);
}

.langgraph-flow-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: 8px;
}

.langgraph-flow-card__eyebrow {
  margin: 0 0 2px;
  color: var(--color-primary);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

.langgraph-flow-card__header h3 {
  margin: 0;
  color: var(--color-text);
  font-size: 14px;
}

.mode-badge {
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 11px;
  font-weight: 700;
}

.langgraph-flow {
  height: 250px;
  border-radius: var(--radius-sm);
  background:
    linear-gradient(rgba(37, 99, 235, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(37, 99, 235, 0.05) 1px, transparent 1px);
  background-size: 24px 24px;
}

.langgraph-flow-card.is-fill .langgraph-flow {
  flex: 1 1 auto;
  height: auto;
  min-height: 352px;
  background-size: 20px 20px;
}

.flow-node {
  min-width: 124px;
  padding: 10px 12px;
  border: 1px solid rgba(37, 99, 235, 0.28);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.1);
}

.langgraph-flow-card.is-fill .flow-node {
  min-width: 146px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.96);
  border-color: rgba(37, 99, 235, 0.28);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.12);
}

.flow-node__index {
  display: block;
  color: var(--color-primary);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 800;
}

.flow-node strong {
  display: block;
  margin-top: 2px;
  color: var(--color-text);
  font-size: 12px;
}

.langgraph-flow-card.is-fill .flow-node strong {
  color: var(--color-text);
  font-size: 13px;
}

.flow-node small {
  display: block;
  margin-top: 4px;
  color: var(--color-text-secondary);
  font-size: 10px;
}

.langgraph-flow-card.is-fill .flow-node small {
  color: var(--color-text-secondary);
  font-size: 11px;
}

.flow-node--done {
  border-color: rgba(22, 163, 74, 0.36);
}

.flow-node--running {
  border-color: rgba(37, 99, 235, 0.46);
  box-shadow: 0 0 0 5px rgba(37, 99, 235, 0.1), 0 10px 24px rgba(15, 23, 42, 0.1);
}

.flow-node--error {
  border-color: rgba(220, 38, 38, 0.46);
}

.flow-node--skipped {
  opacity: 0.72;
  border-style: dashed;
}
</style>
