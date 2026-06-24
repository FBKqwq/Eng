<template>
  <section class="risk-strip" :class="`risk-strip--${tone}`">
    <div class="risk-strip__head">
      <span>{{ title }}</span>
      <strong class="tabular-nums">{{ displayScore }}</strong>
    </div>
    <div class="risk-strip__bar" aria-hidden="true">
      <span
        v-for="segment in segments"
        :key="segment"
        :class="{ active: segment <= activeSegment }"
      />
    </div>
    <div class="risk-strip__body">
      <strong>{{ normalizedLevel }}</strong>
      <p>{{ reason }}</p>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: '风险等级' },
  level: { type: String, default: 'unknown' },
  score: { type: [Number, String], default: null },
  reason: { type: String, default: '等待诊断链路返回风险解释' }
})

const segments = [1, 2, 3, 4, 5]
const normalizedLevel = computed(() => String(props.level || 'unknown').toUpperCase())
const tone = computed(() => {
  const level = String(props.level || '').toLowerCase()
  if (['critical', 'high', 'fatal'].includes(level)) return 'red'
  if (['medium', 'warning'].includes(level)) return 'amber'
  if (['low', 'healthy', 'normal'].includes(level)) return 'green'
  return 'blue'
})
const activeSegment = computed(() => {
  const level = String(props.level || '').toLowerCase()
  if (level === 'critical') return 5
  if (level === 'high') return 4
  if (level === 'medium') return 3
  if (level === 'low') return 2
  const score = Number(props.score)
  if (Number.isFinite(score)) return Math.max(1, Math.min(5, Math.ceil((score > 1 ? score / 100 : score) * 5)))
  return 1
})
const displayScore = computed(() => {
  if (props.score == null || props.score === '') return `${activeSegment.value}/5`
  const value = Number(props.score)
  if (!Number.isFinite(value)) return String(props.score)
  return value <= 1 ? `${Math.round(value * 100)}%` : `${Math.round(value)}`
})
</script>

<style scoped>
.risk-strip {
  --risk-accent: #6f9eac;
  display: grid;
  gap: 10px;
  padding: 10px;
  background: rgba(7, 10, 14, 0.58);
  border: 1px solid rgba(185, 196, 207, 0.18);
  border-radius: 3px;
}

.risk-strip--red {
  --risk-accent: #b96a61;
}

.risk-strip--amber {
  --risk-accent: #b28b5a;
}

.risk-strip--green {
  --risk-accent: #6d9482;
}

.risk-strip__head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  color: #8e9aa6;
  font-size: 11px;
  font-weight: 900;
}

.risk-strip__head strong {
  color: var(--risk-accent);
}

.risk-strip__bar {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 4px;
}

.risk-strip__bar span {
  height: 13px;
  background: rgba(185, 196, 207, 0.12);
  border: 1px solid rgba(185, 196, 207, 0.14);
  clip-path: polygon(0 0, calc(100% - 7px) 0, 100% 100%, 0 100%);
}

.risk-strip__bar span.active {
  background: color-mix(in srgb, var(--risk-accent) 55%, rgba(185, 196, 207, 0.1));
  box-shadow: 0 0 12px color-mix(in srgb, var(--risk-accent) 35%, transparent);
}

.risk-strip__body strong {
  display: block;
  color: #f2f5f7;
  font-size: 22px;
  line-height: 1;
}

.risk-strip__body p {
  margin: 6px 0 0;
  color: #aab4bf;
  font-size: 12px;
  line-height: 1.5;
}
</style>
