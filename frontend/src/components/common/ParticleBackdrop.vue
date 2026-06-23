<template>
  <div
    class="particle-backdrop"
    :class="[
      `particle-backdrop--${variant}`,
      { 'particle-backdrop--static': reducedMotion }
    ]"
    aria-hidden="true"
  >
    <div class="particle-backdrop__base" />
    <VueParticles
      v-if="!reducedMotion"
      :id="particleId"
      class="particle-backdrop__particles"
      :options="particleOptions"
    />
    <div v-else class="particle-backdrop__static" />
    <div class="particle-backdrop__veil" />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'dashboard',
    validator: (v) => ['dashboard', 'pipeline', 'diagnosis'].includes(v)
  },
  intensity: {
    type: Number,
    default: 0.5,
    validator: (v) => v >= 0 && v <= 1
  },
  accentColor: {
    type: String,
    default: ''
  }
})

const reducedMotion = ref(false)
let motionQuery = null
let motionHandler = null

const particleId = computed(() => `particles-${props.variant}-${Math.round(props.intensity * 100)}`)

const accent = computed(() => {
  if (props.accentColor && !props.accentColor.startsWith('var(')) return props.accentColor
  if (props.variant === 'diagnosis') return '#2563eb'
  if (props.variant === 'pipeline') return '#06b6d4'
  return '#2563eb'
})

const particleOptions = computed(() => {
  const density = Math.round(42 + props.intensity * 76)
  const linkOpacity = 0.08 + props.intensity * 0.16
  const particleOpacity = 0.16 + props.intensity * 0.2

  return {
    fullScreen: { enable: false },
    fpsLimit: 60,
    detectRetina: true,
    background: { color: { value: 'transparent' } },
    particles: {
      number: {
        value: density,
        density: { enable: true, width: 900, height: 520 }
      },
      color: { value: [accent.value, '#06b6d4', '#7c3aed'] },
      shape: { type: 'circle' },
      opacity: {
        value: { min: 0.08, max: particleOpacity },
        animation: { enable: true, speed: 0.35, sync: false }
      },
      size: {
        value: { min: 0.7, max: props.variant === 'diagnosis' ? 2.4 : 2 },
        animation: { enable: true, speed: 1.2, sync: false }
      },
      links: {
        enable: true,
        color: accent.value,
        distance: props.variant === 'pipeline' ? 142 : 118,
        opacity: linkOpacity,
        width: 0.8
      },
      move: {
        enable: true,
        direction: props.variant === 'pipeline' ? 'right' : 'none',
        speed: 0.24 + props.intensity * 0.42,
        outModes: { default: 'out' },
        random: false,
        straight: false
      }
    },
    interactivity: {
      detectsOn: 'canvas',
      events: {
        onHover: {
          enable: true,
          mode: props.variant === 'diagnosis' ? 'grab' : 'connect'
        },
        resize: { enable: true }
      },
      modes: {
        connect: { distance: 110, links: { opacity: 0.26 } },
        grab: { distance: 120, links: { opacity: 0.28 } }
      }
    }
  }
})

onMounted(() => {
  motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  reducedMotion.value = motionQuery.matches
  motionHandler = (event) => {
    reducedMotion.value = event.matches
  }
  motionQuery.addEventListener('change', motionHandler)
})

onUnmounted(() => {
  if (motionQuery && motionHandler) {
    motionQuery.removeEventListener('change', motionHandler)
  }
})
</script>

<style scoped>
.particle-backdrop {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
  border-radius: inherit;
}

.particle-backdrop__base {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 70% 56% at 48% 18%, rgba(37, 99, 235, 0.1), transparent 68%),
    radial-gradient(ellipse 54% 42% at 78% 34%, rgba(6, 182, 212, 0.08), transparent 68%),
    linear-gradient(160deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.86));
}

.particle-backdrop--pipeline .particle-backdrop__base {
  background:
    radial-gradient(ellipse 80% 45% at 30% 45%, rgba(6, 182, 212, 0.1), transparent 68%),
    radial-gradient(ellipse 62% 48% at 76% 42%, rgba(37, 99, 235, 0.08), transparent 62%),
    linear-gradient(180deg, rgba(248, 250, 252, 0.9), rgba(255, 255, 255, 0.96));
}

.particle-backdrop--diagnosis .particle-backdrop__base {
  background:
    radial-gradient(ellipse 66% 52% at 45% 40%, rgba(37, 99, 235, 0.11), transparent 70%),
    radial-gradient(ellipse 42% 36% at 72% 22%, rgba(124, 58, 237, 0.07), transparent 66%),
    linear-gradient(150deg, rgba(255, 255, 255, 0.94), rgba(248, 250, 252, 0.88));
}

.particle-backdrop__particles,
.particle-backdrop__static {
  position: absolute;
  inset: 0;
}

.particle-backdrop__static {
  background-image:
    radial-gradient(circle at 18% 22%, rgba(37, 99, 235, 0.16) 0 1px, transparent 1.5px),
    radial-gradient(circle at 72% 38%, rgba(6, 182, 212, 0.12) 0 1px, transparent 1.5px),
    linear-gradient(90deg, rgba(37, 99, 235, 0.06) 1px, transparent 1px),
    linear-gradient(rgba(37, 99, 235, 0.05) 1px, transparent 1px);
  background-size: 42px 42px, 58px 58px, 28px 28px, 28px 28px;
}

.particle-backdrop__veil {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0.12) 0%,
    rgba(255, 255, 255, 0.54) 56%,
    var(--color-surface) 100%
  );
  pointer-events: none;
}

.particle-backdrop--static .particle-backdrop__veil {
  background: linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0.2) 0%,
    rgba(255, 255, 255, 0.74) 60%,
    var(--color-surface) 100%
  );
}
</style>
