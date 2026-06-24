<template>
  <section class="reasoning-inspector" :class="[`reasoning-inspector--${variant}`, { 'is-empty': !normalizedTrace.length }]">
    <header class="reasoning-inspector__header">
      <div>
        <h3>{{ title }}</h3>
        <p>{{ subtitle }}</p>
      </div>
      <span class="reasoning-inspector__count tabular-nums">{{ normalizedTrace.length }} nodes</span>
    </header>

    <div v-if="!normalizedTrace.length" class="reasoning-inspector__empty">
      暂无 LangGraph node_trace，等待规则子图、周期体检或预警链路返回。
    </div>

    <div v-else class="reasoning-inspector__body">
      <ol class="reasoning-inspector__steps">
        <li
          v-for="(node, index) in visibleTrace"
          :key="node.key"
          class="reasoning-inspector__step"
          :class="[`reasoning-inspector__step--${node.tone}`, { active: selectedIndex === index }]"
        >
          <button type="button" @click="selectedIndex = index">
            <span class="reasoning-inspector__index tabular-nums">{{ String(index + 1).padStart(2, '0') }}</span>
            <span class="reasoning-inspector__main">
              <strong>{{ node.stage }}</strong>
              <small>{{ node.summary }}</small>
            </span>
            <span class="reasoning-inspector__duration tabular-nums">{{ node.duration }}</span>
          </button>
        </li>
      </ol>

      <article class="reasoning-inspector__detail">
        <div class="reasoning-inspector__detail-head">
          <span :class="['reasoning-inspector__status', `reasoning-inspector__status--${selectedNode.tone}`]">
            {{ selectedNode.status }}
          </span>
          <span class="tabular-nums">{{ selectedNode.duration }}</span>
        </div>
        <h4>{{ selectedNode.stage }}</h4>
        <p>{{ selectedNode.summary }}</p>
        <dl>
          <div>
            <dt>节点</dt>
            <dd>{{ selectedNode.nodeName }}</dd>
          </div>
          <div v-if="selectedNode.error">
            <dt>错误</dt>
            <dd>{{ selectedNode.error }}</dd>
          </div>
        </dl>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { formatDuration } from '../../utils/format.js'

const props = defineProps({
  nodeTrace: { type: Array, default: () => [] },
  variant: {
    type: String,
    default: 'full',
    validator: (value) => ['full', 'compact'].includes(value)
  },
  title: { type: String, default: 'LangGraph 推理路径' },
  subtitle: { type: String, default: '展示业务阶段、节点状态、耗时、输出摘要与失败原因' },
  maxVisible: { type: Number, default: 8 }
})

const selectedIndex = ref(0)

const STAGE_LABELS = [
  ['parse', '解析事件'],
  ['trigger', '触发识别'],
  ['fetch', '上下文取证'],
  ['context', '上下文取证'],
  ['cluster', '规则聚类'],
  ['correlate', '关联分析'],
  ['evidence', '证据构建'],
  ['infer', '根因推断'],
  ['severity', '风险定级'],
  ['assess', '风险定级'],
  ['alert', '预警决策'],
  ['report', '结论生成'],
  ['generate', '结论生成']
]

const normalizedTrace = computed(() =>
  (props.nodeTrace || []).map((node, index) => {
    const nodeName = String(node?.node_name || node?.name || `node_${index + 1}`)
    const status = String(node?.status || 'unknown')
    return {
      key: `${nodeName}-${index}`,
      nodeName,
      status,
      stage: resolveStage(nodeName),
      tone: resolveTone(status),
      duration: formatDuration(node?.duration_ms),
      summary: node?.output_summary || node?.summary || node?.message || '该节点未返回摘要',
      error: node?.error_message || node?.error || ''
    }
  })
)

const visibleTrace = computed(() => normalizedTrace.value.slice(0, Math.max(1, props.maxVisible)))

const selectedNode = computed(() =>
  normalizedTrace.value[selectedIndex.value] || {
    nodeName: '-',
    status: '-',
    tone: 'muted',
    duration: '-',
    stage: '暂无推理节点',
    summary: '等待 LangGraph 返回 node_trace',
    error: ''
  }
)

watch(
  () => props.nodeTrace,
  () => {
    selectedIndex.value = 0
  }
)

function resolveStage(name) {
  const lower = String(name).toLowerCase()
  const match = STAGE_LABELS.find(([keyword]) => lower.includes(keyword))
  return match?.[1] || '推理节点'
}

function resolveTone(status) {
  const lower = String(status).toLowerCase()
  if (['success', 'completed', 'ok'].includes(lower)) return 'success'
  if (['failed', 'error'].includes(lower)) return 'danger'
  if (['running', 'pending'].includes(lower)) return 'blue'
  if (['skipped', 'degraded'].includes(lower)) return 'amber'
  return 'muted'
}
</script>

<style scoped>
.reasoning-inspector {
  color: #dce4eb;
}

.reasoning-inspector__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 9px;
}

.reasoning-inspector__header h3 {
  margin: 0;
  color: #f2f5f7;
  font-size: 13px;
  font-weight: 950;
}

.reasoning-inspector__header p {
  margin: 3px 0 0;
  color: #8e9aa6;
  font-size: 11px;
}

.reasoning-inspector__count {
  color: #8fb4bd;
  font-size: 11px;
  font-weight: 900;
}

.reasoning-inspector__empty {
  padding: 14px;
  color: #8e9aa6;
  border: 1px dashed rgba(185, 196, 207, 0.24);
  border-radius: 3px;
  background: rgba(9, 12, 16, 0.42);
}

.reasoning-inspector__body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 10px;
}

.reasoning-inspector--compact .reasoning-inspector__body {
  grid-template-columns: minmax(0, 1fr) 260px;
}

.reasoning-inspector__steps {
  display: grid;
  gap: 6px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.reasoning-inspector--compact .reasoning-inspector__steps {
  grid-auto-flow: column;
  grid-auto-columns: minmax(154px, 1fr);
  overflow-x: auto;
  padding-bottom: 2px;
}

.reasoning-inspector__step {
  --step-accent: #6f9eac;
}

.reasoning-inspector__step button {
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr) 50px;
  align-items: center;
  gap: 7px;
  width: 100%;
  min-height: 48px;
  padding: 7px;
  border: 1px solid rgba(185, 196, 207, 0.18);
  border-left: 3px solid var(--step-accent);
  border-radius: 2px;
  background: rgba(12, 15, 20, 0.72);
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.reasoning-inspector--compact .reasoning-inspector__step button {
  grid-template-columns: 28px minmax(0, 1fr);
  min-height: 70px;
}

.reasoning-inspector__step.active button,
.reasoning-inspector__step button:hover {
  border-color: color-mix(in srgb, var(--step-accent) 56%, rgba(185, 196, 207, 0.2));
  background: color-mix(in srgb, var(--step-accent) 11%, rgba(12, 15, 20, 0.82));
}

.reasoning-inspector__step--success {
  --step-accent: #6d9482;
}

.reasoning-inspector__step--danger {
  --step-accent: #b96a61;
}

.reasoning-inspector__step--blue {
  --step-accent: #6f9eac;
}

.reasoning-inspector__step--amber {
  --step-accent: #b28b5a;
}

.reasoning-inspector__step--muted {
  --step-accent: #6b7280;
}

.reasoning-inspector__index {
  color: var(--step-accent);
  font-weight: 950;
}

.reasoning-inspector__main strong,
.reasoning-inspector__main small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reasoning-inspector__main strong {
  color: #edf2f6;
  font-size: 12px;
}

.reasoning-inspector__main small,
.reasoning-inspector__duration {
  color: #8e9aa6;
  font-size: 10px;
}

.reasoning-inspector--compact .reasoning-inspector__duration {
  display: none;
}

.reasoning-inspector__detail {
  padding: 10px;
  background: rgba(7, 10, 14, 0.58);
  border: 1px solid rgba(185, 196, 207, 0.18);
  border-radius: 3px;
}

.reasoning-inspector__detail-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.reasoning-inspector__status {
  color: #8e9aa6;
  font-size: 10px;
  font-weight: 950;
  text-transform: uppercase;
}

.reasoning-inspector__status--success {
  color: #8ab49f;
}

.reasoning-inspector__status--danger {
  color: #d4877c;
}

.reasoning-inspector__status--blue {
  color: #8fb4bd;
}

.reasoning-inspector__status--amber {
  color: #c3a06d;
}

.reasoning-inspector__detail h4 {
  margin: 0 0 7px;
  color: #f2f5f7;
  font-size: 14px;
}

.reasoning-inspector__detail p,
.reasoning-inspector__detail dd {
  color: #aeb8c2;
  font-size: 12px;
  line-height: 1.52;
}

.reasoning-inspector__detail dl {
  margin: 9px 0 0;
}

.reasoning-inspector__detail dt {
  color: #737f8c;
  font-size: 10px;
}

.reasoning-inspector__detail dd {
  margin: 2px 0 7px;
  word-break: break-word;
}

@media (max-width: 960px) {
  .reasoning-inspector__body,
  .reasoning-inspector--compact .reasoning-inspector__body {
    grid-template-columns: 1fr;
  }
}
</style>
