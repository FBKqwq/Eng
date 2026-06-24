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
      <button
        type="button"
        class="theme-btn"
        :aria-label="isDark ? '切换到亮色模式' : '切换到暗色模式'"
        :title="isDark ? '切换到亮色模式' : '切换到暗色模式'"
        @click="theme.toggle()"
      >
        <svg v-if="isDark" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="5" />
          <line x1="12" y1="1" x2="12" y2="3" />
          <line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" />
          <line x1="21" y1="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      </button>
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
import { useTheme } from '../../composables/useTheme.js'
import { usePolling } from '../../composables/usePolling.js'
import { getActiveAlerts } from '../../api/alerts.js'

const route = useRoute()
const { presets, preset, setPreset } = useTimeRange()
const theme = useTheme()
const isDark = theme.isDark
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
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
  min-height: 64px;
  padding: 14px var(--spacing-lg);
  background: color-mix(in srgb, var(--color-surface) 86%, transparent);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--color-border);
  z-index: 10;
}
.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: var(--color-text);
}
.top-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}
.time-range {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 13px;
  color: var(--color-text-secondary);
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
.alert-badge:hover {
  border-color: rgba(220, 38, 38, 0.28);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}
.alert-badge.active {
  color: var(--color-danger);
  border-color: rgba(220, 38, 38, 0.24);
  background: var(--color-danger-bg);
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

.theme-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface-subtle);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition:
    color var(--transition-fast),
    border-color var(--transition-fast),
    background var(--transition-fast);
}

.theme-btn:hover {
  color: var(--color-primary);
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}
</style>
