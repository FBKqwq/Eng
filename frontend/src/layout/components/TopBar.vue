<template>
  <header class="top-bar">
    <h1 class="page-title">{{ title }}</h1>
    <div class="top-actions">
      <div class="time-range">
        <label>时间范围</label>
        <select :value="preset" @change="onPresetChange">
          <option v-for="item in presets" :key="item.value" :value="item.value">
            {{ item.label }}
          </option>
        </select>
      </div>
      <router-link to="/analysis/alerts" class="alert-badge" :class="{ active: alertCount > 0 }">
        预警
        <span v-if="alertCount > 0" class="count">{{ alertCount }}</span>
      </router-link>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTimeRange } from '../../composables/useTimeRange.js'
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
    const data = res?.data
    alertCount.value = Array.isArray(data) ? data.length : data?.count ?? 0
  } catch {
    alertCount.value = 0
  }
}

onMounted(() => {
  fetchAlerts()
  setInterval(fetchAlerts, 30000)
})
</script>

<style scoped>
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 24px;
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
  gap: 16px;
}
.time-range {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}
.time-range select {
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: #fff;
}
.alert-badge {
  position: relative;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  font-size: 13px;
  color: var(--color-text-secondary);
}
.alert-badge.active {
  color: var(--color-danger);
}
.alert-badge .count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  margin-left: 4px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--color-danger);
  color: #fff;
  font-size: 11px;
}
</style>
