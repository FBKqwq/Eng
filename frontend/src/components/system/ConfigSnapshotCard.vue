<template>
  <section class="page-section config-snapshot">
    <header class="snapshot-header">
      <h2>配置快照</h2>
      <span class="pending-tag">待接入：{{ pendingApi }}</span>
    </header>

    <div class="snapshot-groups">
      <article
        v-for="group in displayGroups"
        :key="group.title"
        class="snapshot-group"
      >
        <h3>{{ group.title }}</h3>
        <dl class="kv-list">
          <div v-for="item in group.items" :key="item.key" class="kv-row">
            <dt>{{ item.key }}</dt>
            <dd :class="{ masked: item.sensitive }">{{ formatValue(item) }}</dd>
          </div>
        </dl>
      </article>
    </div>

    <div v-if="kibanaUrl" class="kibana-row">
      <a :href="kibanaUrl" target="_blank" rel="noopener noreferrer" class="kibana-btn">
        打开 Kibana
      </a>
    </div>
    <p v-else class="kibana-hint">Kibana 入口：配置 VITE_KIBANA_URL 后显示（F3 阶段接入）</p>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const PLACEHOLDER_GROUPS = [
  {
    title: 'Kafka',
    items: [
      { key: 'bootstrap_servers', value: '—' },
      { key: 'topic', value: '—' }
    ]
  },
  {
    title: 'Elasticsearch',
    items: [
      { key: 'hosts', value: '—' },
      { key: 'cluster_name', value: '—' }
    ]
  },
  {
    title: '索引模式',
    items: [
      { key: 'index_pattern', value: 'app-logs-*-*' },
      { key: 'log_types', value: '7 大类日志索引' }
    ]
  },
  {
    title: 'LLM',
    items: [
      { key: 'provider', value: '—' },
      { key: 'model', value: '—' },
      { key: 'api_key', value: '***', sensitive: true }
    ]
  }
]

const props = defineProps({
  groups: { type: Array, default: () => [] },
  pendingApi: { type: String, default: 'GET /system/status' },
  kibanaUrl: { type: String, default: '' }
})

const displayGroups = computed(() =>
  props.groups.length > 0 ? props.groups : PLACEHOLDER_GROUPS
)

function formatValue(item) {
  if (item.sensitive) return '***'
  return item.value ?? '—'
}
</script>

<style scoped>
.config-snapshot {
  margin-bottom: 0;
}

.snapshot-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.snapshot-header h2 {
  margin: 0;
}

.pending-tag {
  flex-shrink: 0;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 12px;
  font-weight: 500;
}

.snapshot-groups {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
}

.snapshot-group {
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
}

.snapshot-group h3 {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
}

.kv-list {
  margin: 0;
}

.kv-row {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: 6px 0;
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
}

.kv-row:last-child {
  border-bottom: none;
}

.kv-row dt {
  margin: 0;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.kv-row dd {
  margin: 0;
  text-align: right;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
  word-break: break-all;
}

.kv-row dd.masked {
  letter-spacing: 2px;
  color: var(--color-text-secondary);
}

.kibana-row {
  margin-top: var(--spacing-md);
}

.kibana-btn {
  display: inline-flex;
  align-items: center;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  transition: opacity 0.15s ease;
}

.kibana-btn:hover {
  opacity: 0.9;
}

.kibana-hint {
  margin: var(--spacing-md) 0 0;
  font-size: 12px;
  color: var(--color-text-secondary);
}

@media (max-width: 768px) {
  .snapshot-groups {
    grid-template-columns: 1fr;
  }
}
</style>
