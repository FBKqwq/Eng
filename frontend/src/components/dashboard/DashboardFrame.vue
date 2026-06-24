<template>
  <section class="dash-frame" :class="[`dash-frame--${tone}`, { 'dash-frame--flush': flush }]">
    <header class="dash-frame__header">
      <div class="dash-frame__title-wrap">
        <span class="dash-frame__mark" aria-hidden="true">///</span>
        <h2>{{ title }}</h2>
        <span v-if="subtitle" class="dash-frame__subtitle">{{ subtitle }}</span>
      </div>
      <slot name="actions" />
    </header>
    <div class="dash-frame__body">
      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  tone: { type: String, default: 'blue' },
  flush: { type: Boolean, default: false }
})
</script>

<style scoped>
.dash-frame {
  --frame-accent: #2563eb;
  position: relative;
  min-width: 0;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.82);
  border-radius: 16px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.82), rgba(247, 250, 253, 0.64));
  box-shadow:
    0 12px 32px rgba(40, 58, 78, 0.1),
    0 2px 8px rgba(40, 58, 78, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(28px) saturate(160%);
  -webkit-backdrop-filter: blur(28px) saturate(160%);
}

.dash-frame::after {
  display: none;
}

.dash-frame--red { --frame-accent: #ef4444; }
.dash-frame--cyan { --frame-accent: #0891b2; }
.dash-frame--amber { --frame-accent: #f59e0b; }

.dash-frame__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 34px;
  padding: 5px 10px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.44);
}

.dash-frame__title-wrap {
  display: flex;
  align-items: baseline;
  min-width: 0;
  gap: 7px;
}

.dash-frame__mark {
  color: var(--frame-accent);
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 950;
  letter-spacing: -0.2em;
}

.dash-frame h2 {
  margin: 0;
  color: #162033;
  font-size: 13px;
  font-weight: 900;
  letter-spacing: 0.04em;
}

.dash-frame__subtitle {
  overflow: hidden;
  color: #8a96a8;
  font-family: var(--font-mono);
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dash-frame__body {
  min-height: 0;
  padding: 8px 10px;
}

.dash-frame--flush .dash-frame__body {
  padding: 0;
}
</style>
