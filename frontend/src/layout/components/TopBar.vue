<template>
  <header class="top-bar">
    <h1 class="page-title">{{ title }}</h1>
    <div class="top-actions">
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
import { getActiveAlerts } from '../../api/alerts.js'

const route = useRoute()
const { presets, preset, setPreset } = useTimeRange()
const alertCount = ref(0)

const title = computed(() => route.meta?.title || '页面')

function onPresetChange(event) {
  setPreset(event.target.value)
}

async function fetchAlerts() {
  try {
    const res = await getActiveAlerts()
    const d = res?.data
    alertCount.value = d?.total ?? d?.items?.length ?? 0
  } catch {
    alertCount.value = 0
  }
}

usePolling(fetchAlerts, 30000, true)
</script>

<style scoped>
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}
.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}
.top-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}
.time-range {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 13px;
  color: var(--color-text-secondary);
}
.time-range select {
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
}
.alert-badge {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  font-size: 13px;
  color: var(--color-text-secondary);
  transition: color 150ms ease, box-shadow 150ms ease;
}
.alert-badge:hover {
  box-shadow: var(--shadow-sm);
}
.alert-badge.active {
  color: var(--color-danger);
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
</style>
