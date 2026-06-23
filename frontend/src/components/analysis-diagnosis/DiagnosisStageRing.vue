<template>
  <div class="diagnosis-stage-ring" :class="{ 'is-degraded': degraded }">
    <StageRing :stages="mappedStages" />
    <p v-if="degraded" class="degraded-note">统计模式 · 部分 LLM 阶段已跳过</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import StageRing from '../common/StageRing.vue'

const props = defineProps({
  /** node_trace 条目：{ node_name, status, duration_ms?, output_summary? } */
  nodeTrace: { type: Array, default: () => [] },
  /** 规则/统计降级：LLM 相关阶段标记为已跳过 */
  degraded: { type: Boolean, default: false }
})

const BUSINESS_STAGES = ['取上下文', '关联分析', '根因推断', '定级', '成文']

/** 关联分析、根因推断、定级 — LLM 阶段，降级时可跳过 */
const LLM_STAGE_INDICES = new Set([1, 2, 3])

const NODE_STAGE_MAP = {
  log_fetch: 0,
  pattern_detect: 1,
  rule_diagnose: 2,
  report_write: 4,
  normalize_trigger: 0,
  build_state: 0,
  merge_result: 1,
  main_alert_decision: 3,
  main_persist_result: 4,
  parse_trigger_event: 0,
  fetch_context: 0,
  correlate_events: 1,
  build_evidence: 1,
  infer_root_cause: 2,
  assess_severity: 3,
  generate_event_report: 4,
  build_time_window: 0,
  plan_queries: 0,
  aggregate_metrics: 0,
  sample_logs: 0,
  analyze_relations: 1,
  generate_report: 4
}

const IGNORED_NODES = new Set(['run_scheduled_subgraph', 'run_rule_subgraph'])

const STATUS_PRIORITY = { failed: 4, running: 3, pending: 2, skipped: 1, success: 0 }

function resolveStageIndex(nodeName) {
  const raw = String(nodeName || '').trim()
  if (!raw || IGNORED_NODES.has(raw)) return -1

  const key = raw.includes('.') ? raw.split('.').pop() : raw
  const normalized = key.toLowerCase()

  if (NODE_STAGE_MAP[normalized] !== undefined) {
    return NODE_STAGE_MAP[normalized]
  }

  if (/fetch|log|sample|context|window|plan|aggregate|trigger|state/.test(normalized)) return 0
  if (/correlat|relation|evidence|pattern|merge/.test(normalized)) return 1
  if (/infer|root|diagnos|cause/.test(normalized)) return 2
  if (/severity|assess|alert|decision|grade/.test(normalized)) return 3
  if (/report|write|persist|generat/.test(normalized)) return 4

  return -1
}

function formatDurationMs(ms) {
  if (ms == null || Number.isNaN(ms)) return ''
  const value = Number(ms)
  if (value >= 1000) return `${(value / 1000).toFixed(1)}s`
  return `${value}ms`
}

function toRingStatus(nodeStatus) {
  if (nodeStatus === 'success') return 'done'
  if (nodeStatus === 'failed') return 'error'
  if (nodeStatus === 'running') return 'running'
  return 'pending'
}

function mergeNodeStatus(current, incoming) {
  const curPri = STATUS_PRIORITY[current] ?? -1
  const incPri = STATUS_PRIORITY[incoming] ?? -1
  return incPri > curPri ? incoming : current
}

function buildDurationLabel(nodeStatus, durationMs, isRuleFallback) {
  if (nodeStatus === 'skipped') return '已跳过'
  const time = formatDurationMs(durationMs)
  if (isRuleFallback) return time ? `${time} · 降级` : '降级'
  return time
}

const mappedStages = computed(() => {
  const buckets = BUSINESS_STAGES.map((name) => ({
    name,
    nodeStatus: 'pending',
    ringStatus: 'pending',
    durationMs: 0,
    hasNodes: false,
    isRuleFallback: false
  }))

  for (const entry of props.nodeTrace || []) {
    const stageIndex = resolveStageIndex(entry?.node_name)
    if (stageIndex < 0) continue

    const bucket = buckets[stageIndex]
    const nodeStatus = entry?.status || 'pending'
    bucket.hasNodes = true
    bucket.nodeStatus = mergeNodeStatus(bucket.nodeStatus, nodeStatus)
    bucket.durationMs += Number(entry?.duration_ms) || 0

    if (props.degraded && LLM_STAGE_INDICES.has(stageIndex) && nodeStatus === 'success') {
      bucket.isRuleFallback = true
    }
  }

  if (props.degraded) {
    for (const index of LLM_STAGE_INDICES) {
      const bucket = buckets[index]
      if (!bucket.hasNodes || bucket.nodeStatus === 'pending') {
        bucket.nodeStatus = 'skipped'
        bucket.ringStatus = 'pending'
        bucket.durationMs = 0
        bucket.isRuleFallback = false
      }
    }
  }

  return buckets.map((bucket) => {
    if (!bucket.hasNodes && !props.degraded) {
      return { name: bucket.name, status: 'pending', duration: '' }
    }

    if (bucket.nodeStatus === 'skipped') {
      return { name: bucket.name, status: 'pending', duration: '已跳过' }
    }

    return {
      name: bucket.name,
      status: toRingStatus(bucket.nodeStatus),
      duration: buildDurationLabel(bucket.nodeStatus, bucket.durationMs, bucket.isRuleFallback)
    }
  })
})
</script>

<style scoped>
.diagnosis-stage-ring {
  position: relative;
}

.diagnosis-stage-ring.is-degraded :deep(.stage-ring) {
  opacity: 0.92;
}

.degraded-note {
  margin: var(--spacing-sm) 0 0;
  font-size: 11px;
  color: var(--color-text-muted);
  text-align: center;
}
</style>
