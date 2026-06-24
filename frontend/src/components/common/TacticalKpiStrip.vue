<template>
  <div class="kpi-strip">
    <article
      v-for="item in normalizedItems"
      :key="item.key"
      class="kpi-strip__item"
      :class="`kpi-strip__item--${item.tone}`"
    >
      <span class="kpi-strip__label">{{ item.label }}</span>
      <strong class="kpi-strip__value tabular-nums">{{ item.value }}</strong>
      <span v-if="item.hint" class="kpi-strip__hint">{{ item.hint }}</span>
    </article>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] }
})

const normalizedItems = computed(() =>
  props.items.map((item, index) => ({
    key: item.key || `${item.label}-${index}`,
    label: item.label || '-',
    value: item.value ?? '-',
    hint: item.hint || '',
    tone: item.tone || 'blue'
  }))
)
</script>

<style scoped>
.kpi-strip {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 7px;
  margin: 10px 0;
}

.kpi-strip__item {
  --kpi-accent: #6f9eac;
  position: relative;
  min-height: 64px;
  padding: 9px 11px 8px 13px;
  overflow: hidden;
  background: rgba(15, 18, 23, 0.88);
  border: 1px solid rgba(185, 196, 207, 0.18);
  border-radius: 3px;
  clip-path: polygon(0 0, calc(100% - 13px) 0, 100% 13px, 100% 100%, 0 100%);
}

.kpi-strip__item::before {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: var(--kpi-accent);
  box-shadow: 0 0 14px color-mix(in srgb, var(--kpi-accent) 40%, transparent);
}

.kpi-strip__item::after {
  content: '';
  position: absolute;
  right: -22px;
  top: -28px;
  width: 82px;
  height: 82px;
  border: 1px solid color-mix(in srgb, var(--kpi-accent) 24%, transparent);
  transform: rotate(24deg);
}

.kpi-strip__item--red {
  --kpi-accent: #b96a61;
}

.kpi-strip__item--amber {
  --kpi-accent: #b28b5a;
}

.kpi-strip__item--green {
  --kpi-accent: #6d9482;
}

.kpi-strip__item--violet,
.kpi-strip__item--blue {
  --kpi-accent: #6f9eac;
}

.kpi-strip__label,
.kpi-strip__hint {
  display: block;
  overflow: hidden;
  color: #8e9aa6;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kpi-strip__value {
  display: block;
  margin: 4px 0 3px;
  overflow: hidden;
  color: #f2f5f7;
  font-size: 21px;
  line-height: 1.08;
  font-weight: 950;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kpi-strip__hint {
  color: color-mix(in srgb, var(--kpi-accent) 75%, #cbd5df);
  font-weight: 800;
}

@media (max-width: 1280px) {
  .kpi-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .kpi-strip {
    grid-template-columns: 1fr;
  }
}
</style>
