<template>
  <section class="page-section alert-digest">
    <header class="alert-digest__header">
      <h2>活跃预警摘要</h2>
    </header>

    <EmptyState
      v-if="error"
      compact
      title="预警摘要加载失败"
      :description="error"
    >
      <button type="button" class="alert-digest__retry" @click="fetchAlerts">重试</button>
    </EmptyState>

    <div v-else-if="loading && !displayItems.length" class="alert-digest__loading">
      <span class="alert-digest__skeleton" v-for="n in 3" :key="n" />
    </div>

    <EmptyState
      v-else-if="!displayItems.length"
      compact
      title="暂无活跃预警"
      description="当前无 active 状态预警"
    >
      <router-link to="/analysis/alerts" class="alert-digest__link">前往预警中心</router-link>
    </EmptyState>

    <ul v-else class="alert-digest__list" role="list">
      <li
        v-for="item in displayItems"
        :key="item.alert_id"
        class="alert-digest__row"
        role="button"
        tabindex="0"
        @click="goAlerts"
        @keydown.enter="goAlerts"
      >
        <SeverityBadge :level="item.severity" :label="formatAlertType(item.alert_type)" />
        <span class="alert-digest__service">{{ item.affected_service || '未知服务' }}</span>
        <time class="alert-digest__time tabular-nums">{{ formatTime(item.created_at) }}</time>
      </li>
    </ul>

    <footer v-if="displayItems.length" class="alert-digest__footer">
      <router-link to="/analysis/alerts" class="alert-digest__link">查看全部预警</router-link>
    </footer>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import EmptyState from '../common/EmptyState.vue'
import SeverityBadge from '../common/SeverityBadge.vue'
import { getActiveAlerts } from '../../api/alerts.js'
import { usePolling } from '../../composables/usePolling.js'
import { formatTime } from '../../utils/format.js'

const router = useRouter()

const items = ref([])
const loading = ref(false)
const error = ref('')

const ALERT_TYPE_LABELS = {
  error_rate_spike: '错误率',
  latency_degradation: '耗时',
  security_risk: '安全',
  infra_health: '基础设施',
  traffic_anomaly: '流量'
}

const displayItems = computed(() => items.value.slice(0, 5))

function formatAlertType(type) {
  if (!type) return '预警'
  return ALERT_TYPE_LABELS[type] ?? String(type).replace(/_/g, ' ')
}

function goAlerts() {
  router.push('/analysis/alerts')
}

async function fetchAlerts() {
  loading.value = true
  error.value = ''
  try {
    const res = await getActiveAlerts({ limit: 5 })
    items.value = Array.isArray(res?.data?.items) ? res.data.items : []
  } catch (err) {
    items.value = []
    error.value = err?.error?.message || err?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

usePolling(fetchAlerts, 30000, true)
</script>

<style scoped>
.alert-digest__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.alert-digest__header h2 {
  margin: 0;
}

.alert-digest__list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.alert-digest__row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  cursor: pointer;
  transition: box-shadow 180ms ease, transform 180ms ease;
}

.alert-digest__row:hover,
.alert-digest__row:focus-visible {
  box-shadow: var(--shadow-sm);
  transform: translateY(-1px);
  outline: none;
}

.alert-digest__service {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  color: var(--color-text);
}

.alert-digest__time {
  font-size: 12px;
  color: var(--color-text-muted);
  white-space: nowrap;
}

.alert-digest__footer {
  margin-top: var(--spacing-sm);
  text-align: right;
}

.alert-digest__link {
  font-size: 13px;
  color: var(--color-primary);
  text-decoration: none;
}

.alert-digest__link:hover {
  text-decoration: underline;
}

.alert-digest__retry {
  margin-top: var(--spacing-xs);
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-size: 13px;
  cursor: pointer;
}

.alert-digest__loading {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.alert-digest__skeleton {
  display: block;
  height: 40px;
  border-radius: var(--radius-sm);
  background: linear-gradient(
    90deg,
    var(--color-bg) 25%,
    var(--color-border) 50%,
    var(--color-bg) 75%
  );
  background-size: 200% 100%;
  animation: alert-digest-shimmer 1.2s ease-in-out infinite;
}

@keyframes alert-digest-shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .alert-digest__row {
    transition: none;
  }

  .alert-digest__skeleton {
    animation: none;
    background: var(--color-bg);
  }
}
</style>
