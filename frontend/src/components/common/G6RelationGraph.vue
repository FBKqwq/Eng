<template>
  <div class="g6-graph">
    <div class="g6-graph__hud">
      <span>{{ title }}</span>
      <strong class="tabular-nums">{{ props.nodes.length }}N / {{ props.edges.length }}E</strong>
    </div>
    <div ref="containerRef" class="g6-graph__canvas" />
    <div v-if="!hasGraphData" class="g6-graph__empty">等待关系图谱数据</div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Graph } from '@antv/g6'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  edges: { type: Array, default: () => [] },
  layout: { type: String, default: 'force' },
  title: { type: String, default: 'RELATION GRAPH' }
})

const emit = defineEmits(['select-node'])

const containerRef = ref(null)
let graph = null
let renderSeq = 0
let disposed = false
let resizeObserver = null
let resizeFrame = 0
let lastResizeKey = ''

const hasGraphData = computed(() => props.nodes.length > 0)

const graphData = computed(() => ({
  nodes: props.nodes.map((node) => ({
    id: String(node.id),
    data: node,
    style: {
      labelText: node.label || node.id,
      size: node.size || 34,
      fill: toneColor(node.tone || node.status),
      stroke: toneStroke(node.tone || node.status),
      lineWidth: node.lineWidth || 1.5,
      labelPlacement: node.labelPlacement || 'bottom'
    }
  })),
  edges: props.edges.map((edge, index) => ({
    id: edge.id || `edge-${index}`,
    source: String(edge.source),
    target: String(edge.target),
    data: edge,
    style: {
      endArrow: true,
      stroke: edge.tone === 'danger' ? '#b96a61' : edge.tone === 'warning' ? '#b28b5a' : '#65717d',
      lineWidth: edge.weight ? Math.max(1, Math.min(5, Number(edge.weight))) : 1.3,
      labelText: edge.label || '',
      opacity: edge.opacity ?? 0.9
    }
  }))
}))

function toneColor(tone) {
  if (tone === 'danger' || tone === 'critical' || tone === 'error' || tone === 'red') return '#3a1d1b'
  if (tone === 'warning' || tone === 'high' || tone === 'amber') return '#332719'
  if (tone === 'success' || tone === 'healthy' || tone === 'green') return '#1c2b25'
  if (tone === 'slate' || tone === 'muted') return '#20262d'
  return '#17272d'
}

function toneStroke(tone) {
  if (tone === 'danger' || tone === 'critical' || tone === 'error' || tone === 'red') return '#b96a61'
  if (tone === 'warning' || tone === 'high' || tone === 'amber') return '#b28b5a'
  if (tone === 'success' || tone === 'healthy' || tone === 'green') return '#6d9482'
  if (tone === 'slate' || tone === 'muted') return '#7b8793'
  return '#6f9eac'
}

function destroyGraph() {
  renderSeq += 1
  try {
    graph?.destroy()
  } catch {
    // G6 may already be mid-disposal during route switches.
  }
  graph = null
  lastResizeKey = ''
}

function readContainerSize() {
  const el = containerRef.value
  if (!el) return null
  const width = Math.floor(el.clientWidth)
  const height = Math.floor(el.clientHeight)
  if (width < 1 || height < 1) return null
  return { width, height }
}

async function resizeGraphToContainer() {
  if (!graph || !containerRef.value) return
  const size = readContainerSize()
  if (!size) return
  const resizeKey = `${size.width}x${size.height}`
  if (resizeKey === lastResizeKey) return
  lastResizeKey = resizeKey
  try {
    graph.resize(size.width, size.height)
    await graph.fitView()
  } catch {
    // Ignore resize races during teardown or mid-render.
  }
}

function scheduleResize() {
  if (resizeFrame) cancelAnimationFrame(resizeFrame)
  resizeFrame = requestAnimationFrame(() => {
    resizeFrame = 0
    resizeGraphToContainer()
  })
}

function bindResizeObserver() {
  resizeObserver?.disconnect()
  if (!containerRef.value || typeof ResizeObserver === 'undefined') return
  resizeObserver = new ResizeObserver(scheduleResize)
  resizeObserver.observe(containerRef.value)
}

async function renderGraph() {
  if (disposed) return
  const seq = renderSeq + 1
  renderSeq = seq
  await nextTick()
  if (disposed || seq !== renderSeq) return
  if (!containerRef.value || !hasGraphData.value) {
    destroyGraph()
    return
  }

  try {
    graph?.destroy()
  } catch {
    // Ignore stale G6 disposal while a previous render promise is settling.
  }
  graph = null
  let size = readContainerSize()
  if (!size) {
    await new Promise((resolve) => requestAnimationFrame(resolve))
    size = readContainerSize()
  }
  if (!size) size = { width: 320, height: 280 }

  const nextGraph = new Graph({
    container: containerRef.value,
    width: size.width,
    height: size.height,
    data: graphData.value,
    autoFit: 'view',
    background: 'transparent',
    layout: {
      type: props.layout,
      preventOverlap: true,
      nodeSize: 40,
      linkDistance: 112
    },
    node: {
      style: {
        labelFill: '#dce4eb',
        labelFontSize: 10,
        labelFontWeight: 800,
        halo: true,
        haloStroke: '#6f9eac',
        haloLineWidth: 5,
        haloStrokeOpacity: 0.1
      }
    },
    edge: {
      style: {
        labelFill: '#aab4bf',
        labelFontSize: 9,
        labelBackground: true,
        labelBackgroundFill: 'rgba(8, 11, 15, 0.88)',
        labelBackgroundRadius: 2
      }
    },
    behaviors: ['drag-canvas', 'zoom-canvas', 'drag-element', 'click-select']
  })

  nextGraph.on('node:click', (event) => {
    const id = event.target?.id
    const node = props.nodes.find((item) => String(item.id) === String(id))
    if (node) emit('select-node', node)
  })

  try {
    await nextGraph.render()
  } catch (error) {
    try {
      nextGraph.destroy()
    } catch {
      // no-op
    }
    if (!disposed && seq === renderSeq) {
      throw error
    }
    return
  }
  if (disposed || seq !== renderSeq) {
    try {
      nextGraph.destroy()
    } catch {
      // no-op
    }
    return
  }
  graph = nextGraph
  bindResizeObserver()
  scheduleResize()
}

watch(graphData, renderGraph, { deep: true })
onMounted(() => {
  disposed = false
  bindResizeObserver()
  renderGraph()
})
onBeforeUnmount(() => {
  disposed = true
  if (resizeFrame) cancelAnimationFrame(resizeFrame)
  resizeObserver?.disconnect()
  resizeObserver = null
  destroyGraph()
})
</script>

<style scoped>
.g6-graph {
  position: relative;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 280px;
  max-height: 100%;
  min-width: 0;
  overflow: hidden;
  background:
    linear-gradient(90deg, rgba(111, 158, 172, 0.06) 0 1px, transparent 1px 28px),
    linear-gradient(180deg, rgba(255, 255, 255, 0.04) 0 1px, transparent 1px 28px),
    rgba(6, 9, 13, 0.54);
  background-size: 28px 28px;
  border: 1px solid rgba(185, 196, 207, 0.16);
  border-radius: 3px;
}

.g6-graph__hud {
  position: absolute;
  z-index: 2;
  top: 8px;
  left: 8px;
  right: 8px;
  display: flex;
  justify-content: space-between;
  gap: 8px;
  color: #8e9aa6;
  font-size: 10px;
  font-weight: 900;
  pointer-events: none;
}

.g6-graph__hud strong {
  color: #8fb4bd;
}

.g6-graph__canvas {
  flex: 1 1 auto;
  width: 100%;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
}

.g6-graph__empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8e9aa6;
  font-size: 12px;
}
</style>
