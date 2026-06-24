<template>
  <div ref="hostRef" class="digital-twin">
    <canvas ref="canvasRef" class="digital-twin__canvas" />
    <div class="digital-twin__hud">
      <span class="digital-twin__label">{{ title }}</span>
      <span class="digital-twin__count tabular-nums">{{ projectedPoints.length }} points</span>
    </div>
    <div class="digital-twin__legend">
      <span>X 时间</span>
      <span>Y 风险</span>
      <span>Z 类型/次数</span>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as THREE from 'three'

const props = defineProps({
  services: { type: Array, default: () => [] },
  points: { type: Array, default: () => [] },
  activeService: { type: String, default: '' },
  title: { type: String, default: '3D PCA PROJECTION' }
})

const hostRef = ref(null)
const canvasRef = ref(null)
let renderer = null
let scene = null
let camera = null
let frameId = 0
let resizeObserver = null
let pointGroup = null
let lastResizeKey = ''

const rawPoints = computed(() => {
  if (props.points?.length) return props.points
  const raw = props.services?.length ? props.services : ['gateway', 'order-service', 'payment-service']
  return raw.map((item, index) => {
    if (typeof item === 'string') {
      return {
        id: item,
        label: item,
        type: 'service',
        severity: index === 1 ? 'high' : 'medium',
        count: index + 1,
        time: index
      }
    }
    return {
      id: item.id || item.service || item.name || `point-${index}`,
      label: item.label || item.service || item.name || `point-${index}`,
      type: item.type || item.category || 'service',
      severity: item.severity || item.tone || item.status || 'medium',
      count: Number(item.count ?? item.value ?? index + 1),
      time: item.time || item.created_at || index
    }
  })
})

const projectedPoints = computed(() => {
  const points = rawPoints.value
  const times = points.map((item, index) => toTimeNumber(item.time, index))
  const counts = points.map((item) => Number(item.count || 1))
  const minTime = Math.min(...times)
  const maxTime = Math.max(...times)
  const minCount = Math.min(...counts)
  const maxCount = Math.max(...counts)

  return points.map((item, index) => {
    const severity = severityScore(item.severity)
    const timeNorm = normalize(times[index], minTime, maxTime)
    const countNorm = normalize(Number(item.count || 1), minCount, maxCount)
    const typeNorm = typeScore(item.type || item.label)
    return {
      id: item.id || `point-${index}`,
      label: item.label || item.id || `point-${index}`,
      severity,
      count: Number(item.count || 1),
      tone: item.tone || item.severity,
      active: item.label === props.activeService || item.id === props.activeService,
      x: (timeNorm - 0.5) * 7,
      y: (severity - 0.5) * 3 + countNorm * 0.55,
      z: (typeNorm - 0.5) * 5 + (countNorm - 0.5) * 1.4,
      size: 0.18 + countNorm * 0.2 + severity * 0.14
    }
  })
})

function init() {
  if (!canvasRef.value || renderer) return

  renderer = new THREE.WebGLRenderer({
    canvas: canvasRef.value,
    antialias: true,
    alpha: true
  })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))

  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(44, 1, 0.1, 100)
  camera.position.set(5.2, 4.4, 8.4)
  camera.lookAt(0, 0, 0)

  const ambient = new THREE.AmbientLight(0xb8c4ce, 1.25)
  const key = new THREE.PointLight(0x7aaeb3, 1.7, 30)
  key.position.set(4, 5, 5)
  scene.add(ambient, key)

  const grid = new THREE.GridHelper(10, 10, 0x33414b, 0x1f262d)
  grid.position.y = -1.4
  scene.add(grid)
  addAxis('X', 0xb8c4ce, new THREE.Vector3(-4.3, -1.15, -3.6), new THREE.Vector3(4.3, -1.15, -3.6))
  addAxis('Y', 0xb96a61, new THREE.Vector3(-4.3, -1.15, -3.6), new THREE.Vector3(-4.3, 2.8, -3.6))
  addAxis('Z', 0xb28b5a, new THREE.Vector3(-4.3, -1.15, -3.6), new THREE.Vector3(-4.3, -1.15, 3.6))

  pointGroup = new THREE.Group()
  scene.add(pointGroup)

  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(hostRef.value)
  rebuildPoints()
  resize()
  animate()
}

function addAxis(name, color, start, end) {
  const geometry = new THREE.BufferGeometry().setFromPoints([start, end])
  const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.54 })
  const line = new THREE.Line(geometry, material)
  line.userData.axis = name
  scene.add(line)
}

function resize() {
  if (!hostRef.value || !renderer || !camera) return
  const rect = hostRef.value.getBoundingClientRect()
  const width = Math.max(1, Math.floor(rect.width))
  const height = Math.max(1, Math.floor(rect.height))
  const resizeKey = `${width}x${height}`
  if (resizeKey === lastResizeKey) return
  lastResizeKey = resizeKey
  renderer.setSize(width, height, false)
  camera.aspect = width / height
  camera.updateProjectionMatrix()
}

function rebuildPoints() {
  if (!pointGroup) return
  pointGroup.clear()

  const materialLine = new THREE.LineBasicMaterial({ color: 0x65717d, transparent: true, opacity: 0.34 })
  const sorted = [...projectedPoints.value].sort((a, b) => a.x - b.x)

  sorted.forEach((point, index) => {
    const geometry = new THREE.IcosahedronGeometry(point.active ? point.size * 1.28 : point.size, 1)
    const color = resolveColor(point)
    const material = new THREE.MeshStandardMaterial({
      color,
      emissive: color,
      emissiveIntensity: point.active ? 0.46 : 0.2,
      roughness: 0.48,
      metalness: 0.28
    })
    const mesh = new THREE.Mesh(geometry, material)
    mesh.position.set(point.x, point.y, point.z)
    mesh.userData.baseY = point.y
    mesh.userData.index = index
    pointGroup.add(mesh)

    if (index > 0) {
      const prev = sorted[index - 1]
      const lineGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(prev.x, prev.y, prev.z),
        new THREE.Vector3(point.x, point.y, point.z)
      ])
      pointGroup.add(new THREE.Line(lineGeo, materialLine))
    }
  })
}

function resolveColor(point) {
  if (point.active || point.severity >= 0.76) return 0xb96a61
  if (point.severity >= 0.52) return 0xb28b5a
  if (point.severity <= 0.26) return 0x6d9482
  return 0x6f9eac
}

function toTimeNumber(value, fallback) {
  if (value == null || value === '') return fallback
  if (typeof value === 'number') return value < 1e12 ? value * 1000 : value
  const ms = Date.parse(value)
  return Number.isFinite(ms) ? ms : fallback
}

function normalize(value, min, max) {
  if (!Number.isFinite(value) || max === min) return 0.5
  return (value - min) / (max - min)
}

function severityScore(value) {
  const text = String(value || '').toLowerCase()
  if (['critical', 'fatal', 'danger', 'red'].includes(text)) return 1
  if (['high', 'error'].includes(text)) return 0.78
  if (['medium', 'warning', 'amber'].includes(text)) return 0.56
  if (['low', 'success', 'healthy', 'green'].includes(text)) return 0.22
  const num = Number(value)
  if (Number.isFinite(num)) return Math.max(0, Math.min(1, num > 1 ? num / 100 : num))
  return 0.45
}

function typeScore(value) {
  const text = String(value || '')
  let hash = 0
  for (let i = 0; i < text.length; i += 1) hash = (hash * 31 + text.charCodeAt(i)) % 997
  return hash / 997
}

function animate() {
  if (!renderer || !scene || !camera || !pointGroup) return
  const time = performance.now() * 0.001
  pointGroup.rotation.y = Math.sin(time * 0.28) * 0.16
  pointGroup.children.forEach((child) => {
    if (child.isMesh) {
      child.position.y = child.userData.baseY + Math.sin(time * 1.5 + child.userData.index) * 0.045
      child.rotation.x += 0.004
      child.rotation.y += 0.006
    }
  })
  renderer.render(scene, camera)
  frameId = requestAnimationFrame(animate)
}

function destroy() {
  cancelAnimationFrame(frameId)
  resizeObserver?.disconnect()
  scene?.traverse((child) => {
    child.geometry?.dispose?.()
    child.material?.dispose?.()
  })
  renderer?.dispose()
  renderer = null
  scene = null
  camera = null
  pointGroup = null
}

watch(projectedPoints, async () => {
  await nextTick()
  rebuildPoints()
}, { deep: true })

watch(() => props.activeService, rebuildPoints)
onMounted(init)
onBeforeUnmount(destroy)
</script>

<style scoped>
.digital-twin {
  position: relative;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 270px;
  max-height: 100%;
  min-width: 0;
  overflow: hidden;
  background:
    linear-gradient(90deg, rgba(111, 158, 172, 0.05) 0 1px, transparent 1px 26px),
    linear-gradient(180deg, rgba(255, 255, 255, 0.035) 0 1px, transparent 1px 26px),
    linear-gradient(180deg, rgba(7, 10, 14, 0.28), rgba(7, 10, 14, 0.78));
  background-size: 26px 26px;
  border: 1px solid rgba(185, 196, 207, 0.16);
  border-radius: 3px;
}

.digital-twin__canvas {
  display: block;
  flex: 1 1 auto;
  width: 100%;
  min-height: 0;
  min-width: 0;
}

.digital-twin__hud,
.digital-twin__legend {
  position: absolute;
  left: 9px;
  right: 9px;
  display: flex;
  justify-content: space-between;
  gap: 8px;
  color: #8e9aa6;
  font-size: 10px;
  pointer-events: none;
}

.digital-twin__hud {
  top: 8px;
}

.digital-twin__legend {
  bottom: 8px;
}

.digital-twin__label {
  color: #8fb4bd;
  font-weight: 950;
  text-transform: uppercase;
}

@media (prefers-reduced-motion: reduce) {
  .digital-twin__canvas {
    opacity: 0.72;
  }
}
</style>
