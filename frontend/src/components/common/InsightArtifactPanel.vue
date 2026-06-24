<template>
  <section class="insight-panel">
    <article
      v-for="item in normalizedItems"
      :key="item.key"
      class="insight-panel__item"
      :class="`insight-panel__item--${item.tone}`"
    >
      <span class="insight-panel__metric tabular-nums">{{ item.metric }}</span>
      <div>
        <strong>{{ item.title }}</strong>
        <p>{{ item.description }}</p>
      </div>
    </article>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] }
})

const normalizedItems = computed(() =>
  props.items.map((item, index) => ({
    key: item.key || `${item.title}-${index}`,
    title: item.title || '-',
    metric: item.metric ?? '-',
    description: item.description || '',
    tone: item.tone || 'blue'
  }))
)
</script>

<style scoped>
.insight-panel {
  display: grid;
  gap: 7px;
}

.insight-panel__item {
  --insight-accent: #6f9eac;
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  gap: 10px;
  min-height: 68px;
  padding: 9px;
  background: rgba(7, 10, 14, 0.58);
  border: 1px solid rgba(185, 196, 207, 0.16);
  border-left: 3px solid var(--insight-accent);
  border-radius: 2px;
}

.insight-panel__item--red {
  --insight-accent: #b96a61;
}

.insight-panel__item--amber {
  --insight-accent: #b28b5a;
}

.insight-panel__item--green {
  --insight-accent: #6d9482;
}

.insight-panel__metric {
  color: var(--insight-accent);
  font-size: 18px;
  font-weight: 950;
}

.insight-panel__item strong {
  display: block;
  color: #f2f5f7;
  font-size: 12px;
}

.insight-panel__item p {
  margin: 5px 0 0;
  color: #aab4bf;
  font-size: 11px;
  line-height: 1.45;
}
</style>
