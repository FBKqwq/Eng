<template>
  <div class="langgraph-flow-card">
    <header class="langgraph-flow-card__header">
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
  degraded: { type: Boolean, default: false }
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
    position: { x: index * 180 + 30, y: 30 },
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
  min-height: 340px;
  padding: 12px;
  border: var(--industrial-border-width) solid var(--industrial-border-color);
  border-radius: 0;
  background: var(--industrial-dark-gray);
  box-shadow: none;
}

.langgraph-flow-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: 8px;
  padding: 12px 16px;
  background: var(--industrial-dark-gray);
  border-radius: 0;
  position: relative;
  clip-path: polygon(
    0 0,
    calc(100% - var(--industrial-cut-size)) 0,
    100% var(--industrial-cut-size),
    100% 100%,
    0 100%
  );
}

.langgraph-flow-card__header::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 8px;
  height: 8px;
  background: var(--industrial-blue-cyan);
}

.langgraph-flow-card__eyebrow {
  margin: 0 0 2px;
  color: var(--industrial-blue-cyan);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
  font-family: var(--font-mono);
}

.langgraph-flow-card__header h3 {
  margin: 0;
  color: var(--industrial-white);
  font-size: 14px;
  font-weight: 700;
}

.mode-badge {
  padding: 3px 8px;
  border-radius: 0;
  background: rgba(249, 115, 22, 0.08);
  color: var(--industrial-orange);
  font-size: 11px;
  font-weight: 700;
  border: 1px solid var(--industrial-orange);
}

.langgraph-flow {
  min-height: 280px;
  border-radius: 0;
  background:
    linear-gradient(rgba(148, 163, 184, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.1) 1px, transparent 1px);
  background-size: 20px 20px;
  background-color: rgba(30, 41, 59, 0.5);
}

.flow-node {
  min-width: 124px;
  padding: 10px 12px;
  border: 1px solid var(--industrial-border-color);
  border-radius: 0;
  background: var(--industrial-white);
  position: relative;
  clip-path: polygon(
    0 0,
    calc(100% - var(--industrial-cut-size)) 0,
    100% var(--industrial-cut-size),
    100% 100%,
    0 100%
  );
}

.flow-node__index {
  position: absolute;
  left: 0;
  top: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #475569;
  color: var(--industrial-white);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
}

.flow-node strong {
  display: block;
  margin-top: 2px;
  margin-left: 28px;
  color: var(--industrial-dark-gray);
  font-size: 12px;
  font-weight: 700;
}

.flow-node small {
  display: block;
  margin-top: 4px;
  margin-left: 28px;
  color: var(--industrial-medium-gray);
  font-size: 10px;
}

.flow-node--done {
  border-color: #94a3b8;
  background: #f8fafc;
}

.flow-node--done .flow-node__index {
  background: #64748b;
}

.flow-node--running {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.flow-node--running .flow-node__index {
  background: #3b82f6;
  animation: pulse 3s ease-in-out infinite;
}

.flow-node--error {
  border-color: #dc2626;
  box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.1);
}

.flow-node--error .flow-node__index {
  background: #dc2626;
}

.flow-node--skipped {
  opacity: 0.55;
  border-style: dashed;
}

.flow-node--skipped .flow-node__index {
  background: #64748b;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.9;
  }
  50% {
    opacity: 0.5;
  }
}

@media (prefers-reduced-motion: reduce) {
  .flow-node--running .flow-node__index {
    animation: none;
  }
}
</style>
