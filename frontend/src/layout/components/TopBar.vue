<template>
  <header class="top-bar" :class="[`top-bar--${pageHeader.tone}`, { 'top-bar--analysis': pageHeader.active }]">
    <div class="page-heading">
      <p v-if="pageHeader.active && pageHeader.eyebrow" class="page-heading__eyebrow">
        {{ pageHeader.eyebrow }}
      </p>
      <h1 class="page-title">{{ headerTitle }}</h1>
      <p v-if="pageHeader.active && pageHeader.subtitle" class="page-heading__subtitle">
        {{ pageHeader.subtitle }}
      </p>
    </div>

    <div class="top-actions">
      <div id="topbar-page-actions" class="topbar-page-actions" />
      <div class="time-range">
        <label for="topbar-time-range">时间范围</label>
        <select
          id="topbar-time-range"
          :value="preset"
          @change="onPresetChange"
        >
          <option v-for="item in presets" :key="item.value" :value="item.value">
            {{ item.label }}
          </option>
        </select>
      </div>
      <router-link
        to="/analysis/alerts"
        class="alert-badge"
        :class="{ active: alertCount > 0 }"
        :aria-label="alertCount > 0 ? `预警 ${alertCount} 条` : '预警'"
      >
        预警
        <span v-if="alertCount > 0" class="alert-dot" aria-hidden="true" />
        <span v-if="alertCount > 0" class="count tabular-nums">{{ alertCount }}</span>
      </router-link>
    </div>
  </header>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useTimeRange } from '../../composables/useTimeRange.js'
import { usePolling } from '../../composables/usePolling.js'
import { usePageHeader } from '../../composables/usePageHeader.js'
import { getActiveAlerts } from '../../api/alerts.js'

const route = useRoute()
const { presets, preset, setPreset } = useTimeRange()
const { pageHeader } = usePageHeader()
const alertCount = ref(0)

const headerTitle = computed(() => pageHeader.value.active ? pageHeader.value.title : route.meta?.title || '页面')

function onPresetChange(event) {
  setPreset(event.target.value)
}

async function fetchAlerts() {
  try {
    const res = await getActiveAlerts()
    const d = res?.data
    alertCount.value = d?.total ?? d?.items?.length ?? 0
  } catch (e) {
    alertCount.value = 0
    const code = e?.error?.code
    if (code) {
      console.warn('[TopBar] getActiveAlerts failed:', code, e?.error?.message ?? e?.message)
    }
  }
}

usePolling(fetchAlerts, 30000, true)
</script>

<style scoped>
.top-bar {
  --topbar-accent: #2563eb;
  --topbar-accent-rgb: 37, 99, 235;
  position: relative;
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  min-height: 64px;
  padding: 14px var(--spacing-lg);
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--color-border);
  z-index: 10;
}

.top-bar--analysis {
  --topbar-accent: #6f9eac;
  --topbar-accent-rgb: 111, 158, 172;
  align-items: stretch;
  min-height: 90px;
  padding: 12px 18px;
  color: #e6edf3;
  background:
    linear-gradient(135deg, rgba(7, 10, 14, 0.98), rgba(18, 23, 30, 0.96) 48%, rgba(8, 11, 15, 0.98)),
    #080b10;
  border-bottom: 1px solid rgba(185, 196, 207, 0.22);
  box-shadow: inset 0 -1px 0 rgba(255, 255, 255, 0.035), 0 12px 30px rgba(0, 0, 0, 0.22);
}

.top-bar--analysis::before {
  content: '';
  position: absolute;
  left: 18px;
  bottom: 0;
  width: 220px;
  height: 3px;
  background: var(--topbar-accent);
  box-shadow: 0 0 18px rgba(var(--topbar-accent-rgb), 0.42);
  clip-path: polygon(0 0, calc(100% - 24px) 0, 100% 100%, 0 100%);
}

.top-bar--red {
  --topbar-accent: #b96a61;
  --topbar-accent-rgb: 185, 106, 97;
}

.top-bar--amber {
  --topbar-accent: #b28b5a;
  --topbar-accent-rgb: 178, 139, 90;
}

.top-bar--green {
  --topbar-accent: #6d9482;
  --topbar-accent-rgb: 109, 148, 130;
}

.page-heading {
  display: grid;
  align-content: center;
  min-width: 0;
}

.page-heading__eyebrow {
  display: inline-block;
  width: fit-content;
  margin: 0 0 5px;
  padding: 2px 10px 2px 7px;
  color: #d9e7ea;
  background: rgba(var(--topbar-accent-rgb), 0.14);
  border-left: 3px solid var(--topbar-accent);
  clip-path: polygon(0 0, calc(100% - 9px) 0, 100% 100%, 0 100%);
  font-size: 10px;
  font-weight: 950;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: var(--color-text);
}

.top-bar--analysis .page-title {
  color: #f2f5f7;
  font-size: 23px;
  line-height: 1.08;
  font-weight: 950;
}

.page-heading__subtitle {
  max-width: 880px;
  margin: 6px 0 0;
  color: #9aa6b2;
  font-size: 12px;
  line-height: 1.42;
}

.top-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--spacing-md);
}

.top-bar--analysis .top-actions {
  align-items: center;
  align-self: center;
  gap: 8px;
}

.topbar-page-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.topbar-page-actions:empty {
  display: none;
}

.time-range {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 13px;
  color: var(--color-text-secondary);
}

.top-bar--analysis .time-range {
  gap: 8px;
  color: #8e9aa6;
  font-size: 12px;
  font-weight: 850;
}

.time-range select {
  min-height: 34px;
  padding: 6px 32px 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  font-weight: 600;
}

.top-bar--analysis .time-range select {
  border-color: rgba(185, 196, 207, 0.2);
  border-radius: 2px;
  background: rgba(7, 10, 14, 0.62);
  color: #e6edf3;
  font-weight: 900;
}

.alert-badge {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-height: 34px;
  padding: 7px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface-subtle);
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-secondary);
  transition:
    color var(--transition-fast),
    box-shadow var(--transition-fast),
    border-color var(--transition-fast),
    background var(--transition-fast);
}

.top-bar--analysis .alert-badge {
  border-color: rgba(185, 196, 207, 0.2);
  border-radius: 2px;
  background: rgba(7, 10, 14, 0.62);
  color: #b8c3cf;
  font-weight: 900;
  clip-path: polygon(0 0, calc(100% - 9px) 0, 100% 100%, 0 100%);
}

.alert-badge:hover {
  border-color: rgba(220, 38, 38, 0.28);
  background: #fff;
  box-shadow: var(--shadow-sm);
}

.top-bar--analysis .alert-badge:hover {
  border-color: rgba(185, 106, 97, 0.46);
  background: rgba(185, 106, 97, 0.12);
  box-shadow: none;
}

.alert-badge.active {
  color: var(--color-danger);
  border-color: rgba(220, 38, 38, 0.24);
  background: var(--color-danger-bg);
}

.top-bar--analysis .alert-badge.active {
  color: #e2b8b2;
  border-color: rgba(185, 106, 97, 0.42);
  background: rgba(185, 106, 97, 0.14);
}

.alert-dot {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-danger);
  border: 2px solid var(--color-surface);
}

.top-bar--analysis .alert-dot {
  background: #b96a61;
  border-color: #080b10;
}

.alert-badge .count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  margin-left: 2px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--color-danger);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}

.top-bar--analysis .alert-badge .count {
  border-radius: 2px;
  background: #b96a61;
  font-weight: 900;
}

.top-bar--analysis :deep(.ak-button) {
  min-height: 34px;
  padding: 7px 12px;
  border: 1px solid rgba(var(--topbar-accent-rgb), 0.5);
  border-radius: 2px;
  background: rgba(var(--topbar-accent-rgb), 0.11);
  color: #e7f2f4;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  clip-path: polygon(0 0, calc(100% - 10px) 0, 100% 100%, 0 100%);
}

.top-bar--analysis :deep(.ak-button:hover:not(:disabled)) {
  border-color: rgba(var(--topbar-accent-rgb), 0.8);
  background: rgba(var(--topbar-accent-rgb), 0.18);
}

.top-bar--analysis :deep(.ak-button:disabled) {
  cursor: not-allowed;
  opacity: 0.5;
}

@media (max-width: 1180px) {
  .top-bar,
  .top-bar--analysis {
    align-items: flex-start;
    flex-direction: column;
  }

  .top-actions,
  .top-bar--analysis .top-actions {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}
</style>
