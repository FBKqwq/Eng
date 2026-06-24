<template>
  <div
    ref="host"
    class="dashboard-webgl-flow"
    :class="{ 'dashboard-webgl-flow--fallback': fallback }"
    aria-hidden="true"
  >
    <div class="dashboard-webgl-flow__weather" />
    <div class="dashboard-webgl-flow__grid" />
  </div>
</template>

<script setup>
import * as THREE from 'three'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  telemetry: { type: Object, required: true },
  sources: { type: Array, default: () => [] }
})

const LOG_COLORS = {
  application: '#38bdf8',
  behavior: '#22d3ee',
  web_server: '#818cf8',
  performance: '#34d399',
  security: '#fb7185',
  infrastructure: '#fbbf24',
  audit: '#c084fc'
}

const host = ref(null)
const fallback = ref(false)
const reducedMotion = ref(false)
let renderer
let scene
let camera
let geometry
let material
let particles
let animationFrame
let resizeObserver
let motionQuery
let lastFrame = 0

const sourceSignature = computed(() =>
  props.sources
    .map((item) => `${item?.key ?? 'unknown'}:${Number(item?.count ?? 0)}`)
    .join('|')
)

const particleCount = computed(() => {
  const intensity = Number(props.telemetry?.intensity ?? 0.5)
  const flow = Number(props.telemetry?.flowRate ?? 0)
  return Math.round(Math.min(2200, 620 + intensity * 720 + flow * 760))
})

function buildPalette() {
  const weighted = []
  for (const source of props.sources) {
    const key = String(source?.key ?? '').toLowerCase()
    const color = LOG_COLORS[key]
    if (!color) continue
    const weight = Math.max(1, Math.min(12, Math.round(Number(source?.count ?? 1) / 50)))
    for (let i = 0; i < weight; i += 1) weighted.push(color)
  }
  return weighted.length ? weighted : Object.values(LOG_COLORS)
}

function disposeParticles() {
  if (particles) scene?.remove(particles)
  geometry?.dispose()
  material?.dispose()
  particles = null
  geometry = null
  material = null
}

function buildParticles() {
  if (!scene || reducedMotion.value) return
  disposeParticles()

  const count = particleCount.value
  const positions = new Float32Array(count * 3)
  const colors = new Float32Array(count * 3)
  const sizes = new Float32Array(count)
  const speeds = new Float32Array(count)
  const phases = new Float32Array(count)
  const palette = buildPalette()

  for (let i = 0; i < count; i += 1) {
    const depth = Math.random()
    positions[i * 3] = THREE.MathUtils.randFloatSpread(2.7)
    positions[i * 3 + 1] = THREE.MathUtils.randFloatSpread(2.7)
    positions[i * 3 + 2] = THREE.MathUtils.lerp(-0.7, 0.7, depth)

    const color = new THREE.Color(palette[Math.floor(Math.random() * palette.length)])
    colors[i * 3] = color.r
    colors[i * 3 + 1] = color.g
    colors[i * 3 + 2] = color.b
    sizes[i] = THREE.MathUtils.lerp(4.2, 14.5, depth)
    speeds[i] = THREE.MathUtils.randFloat(0.62, 1.55)
    phases[i] = Math.random() * Math.PI * 2
  }

  geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
  geometry.setAttribute('aSize', new THREE.BufferAttribute(sizes, 1))
  geometry.setAttribute('aSpeed', new THREE.BufferAttribute(speeds, 1))
  geometry.setAttribute('aPhase', new THREE.BufferAttribute(phases, 1))

  material = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.NormalBlending,
    vertexColors: true,
    uniforms: {
      uTime: { value: 0 },
      uFlow: { value: 0.4 },
      uAnomaly: { value: 0 },
      uAcceleration: { value: 0 },
      uPixelRatio: { value: Math.min(window.devicePixelRatio, 1.8) }
    },
    vertexShader: `
      attribute float aSize;
      attribute float aSpeed;
      attribute float aPhase;
      varying vec3 vColor;
      varying float vAlpha;
      uniform float uTime;
      uniform float uFlow;
      uniform float uAnomaly;
      uniform float uAcceleration;
      uniform float uPixelRatio;

      void main() {
        float pace = 0.075 + uFlow * 0.16 + uAcceleration * 0.055;
        float travel = uTime * pace * aSpeed;
        float turbulence = (0.012 + uAnomaly * 0.095);
        vec3 p = position;
        p.x = mod(p.x + travel + 1.35, 2.7) - 1.35;
        p.y = mod(p.y - travel * 0.72 + sin(uTime * 0.75 + aPhase + p.x * 4.0) * turbulence + 1.35, 2.7) - 1.35;
        p.x += cos(uTime * 0.44 + aPhase + p.y * 3.0) * turbulence * 0.55;

        vec4 mvPosition = modelViewMatrix * vec4(p, 1.0);
        gl_Position = projectionMatrix * mvPosition;
        gl_PointSize = aSize * uPixelRatio * (1.0 + uFlow * 0.45);
        vColor = color;
        vAlpha = 0.48 + (position.z + 0.7) * 0.32;
      }
    `,
    fragmentShader: `
      varying vec3 vColor;
      varying float vAlpha;

      void main() {
        vec2 uv = gl_PointCoord - vec2(0.5);
        mat2 rotation = mat2(0.707, -0.707, 0.707, 0.707);
        uv = rotation * uv;
        uv.x *= 0.27;
        float core = smoothstep(0.26, 0.0, length(uv));
        float glow = smoothstep(0.5, 0.04, length(uv)) * 0.68;
        float alpha = (core + glow) * vAlpha;
        if (alpha < 0.025) discard;
        gl_FragColor = vec4(vColor, alpha);
      }
    `
  })

  particles = new THREE.Points(geometry, material)
  scene.add(particles)
}

function resize() {
  if (!host.value || !renderer || !camera) return
  const { width, height } = host.value.getBoundingClientRect()
  if (!width || !height) return
  renderer.setSize(width, height, false)
  camera.aspect = width / height
  camera.updateProjectionMatrix()
}

function render(time = 0) {
  animationFrame = window.requestAnimationFrame(render)
  if (!renderer || !material || reducedMotion.value) return
  if (time - lastFrame < 16) return
  lastFrame = time
  material.uniforms.uTime.value = time / 1000
  material.uniforms.uFlow.value = Number(props.telemetry?.flowRate ?? 0)
  material.uniforms.uAnomaly.value = Number(props.telemetry?.anomalyRate ?? 0)
  material.uniforms.uAcceleration.value = Number(props.telemetry?.acceleration ?? 0)
  renderer.render(scene, camera)
}

function handleMotionChange(event) {
  reducedMotion.value = event.matches
  if (event.matches) {
    disposeParticles()
    renderer?.clear()
  } else {
    buildParticles()
  }
}

onMounted(() => {
  motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  reducedMotion.value = motionQuery.matches
  motionQuery.addEventListener('change', handleMotionChange)

  try {
    renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: false,
      powerPreference: 'high-performance'
    })
    renderer.setClearColor(0x000000, 0)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.8))
    renderer.domElement.className = 'dashboard-webgl-flow__canvas'
    host.value.prepend(renderer.domElement)

    scene = new THREE.Scene()
    camera = new THREE.PerspectiveCamera(42, 1, 0.1, 10)
    camera.position.z = 2.7
    buildParticles()
    resizeObserver = new ResizeObserver(resize)
    resizeObserver.observe(host.value)
    resize()
    render()
  } catch {
    fallback.value = true
  }
})

watch([sourceSignature, particleCount], () => {
  if (scene && !reducedMotion.value) buildParticles()
})

onUnmounted(() => {
  window.cancelAnimationFrame(animationFrame)
  resizeObserver?.disconnect()
  motionQuery?.removeEventListener('change', handleMotionChange)
  disposeParticles()
  renderer?.dispose()
  renderer?.domElement?.remove()
})
</script>

<style scoped>
.dashboard-webgl-flow {
  position: absolute;
  z-index: 0;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  background:
    radial-gradient(circle at 8% 4%, rgba(56, 189, 248, 0.16), transparent 31%),
    radial-gradient(circle at 88% 22%, rgba(99, 102, 241, 0.11), transparent 34%),
    linear-gradient(145deg, #ffffff 0%, #f7fbfe 48%, #edf5fa 100%);
}

.dashboard-webgl-flow :deep(.dashboard-webgl-flow__canvas) {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0.82;
}

.dashboard-webgl-flow__weather {
  position: absolute;
  inset: -15%;
  background:
    linear-gradient(135deg, transparent 18%, rgba(14, 165, 233, 0.08) 42%, transparent 66%),
    radial-gradient(ellipse at 25% 15%, rgba(255, 255, 255, 0.72), transparent 42%);
  filter: blur(28px);
}

.dashboard-webgl-flow__grid {
  position: absolute;
  inset: 0;
  opacity: 0.12;
  background-image:
    linear-gradient(rgba(148, 213, 235, 0.16) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 213, 235, 0.12) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: linear-gradient(135deg, #000 0%, transparent 72%);
}

.dashboard-webgl-flow--fallback::after {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(circle at 10% 10%, #38bdf8 0 1px, transparent 2px),
    radial-gradient(circle at 45% 35%, #34d399 0 1px, transparent 2px),
    radial-gradient(circle at 78% 65%, #fb7185 0 1px, transparent 2px);
  background-size: 38px 38px, 56px 56px, 72px 72px;
  content: '';
}

@media (prefers-reduced-motion: reduce) {
  .dashboard-webgl-flow::after {
    position: absolute;
    inset: 0;
    background-image:
      radial-gradient(circle at 10% 10%, rgba(56, 189, 248, 0.8) 0 1px, transparent 2px),
      radial-gradient(circle at 45% 35%, rgba(52, 211, 153, 0.7) 0 1px, transparent 2px),
      radial-gradient(circle at 78% 65%, rgba(251, 113, 133, 0.7) 0 1px, transparent 2px);
    background-size: 38px 38px, 56px 56px, 72px 72px;
    content: '';
  }
}
</style>
