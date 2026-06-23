<template>
  <section class="page-section config-snapshot">
    <header class="snapshot-header">
      <h2>配置快照</h2>
      <span v-if="isPlaceholder" class="pending-tag">待接入：GET /system/status</span>
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
            <dd
              :class="{ masked: isSensitiveItem(item) }"
              :aria-label="isSensitiveItem(item) ? `${item.key}（已脱敏）` : undefined"
            >
              {{ formatValue(item) }}
            </dd>
          </div>
        </dl>
      </article>
    </div>

    <div v-if="hasKibana || hasDiscover" class="kibana-row">
      <a
        v-if="hasKibana"
        :href="kibanaUrl"
        target="_blank"
        rel="noopener noreferrer"
        class="kibana-btn"
      >
        {{ kibanaLabel }}
      </a>
      <a
        v-if="hasDiscover"
        :href="discoverUrl"
        target="_blank"
        rel="noopener noreferrer"
        class="kibana-btn kibana-btn--secondary"
      >
        {{ discoverLabel }}
      </a>
    </div>
    <p v-else class="kibana-hint">Kibana 入口：配置 VITE_KIBANA_URL 后显示外链按钮</p>
  </section>
</template>

<script setup>
import { computed } from 'vue'

/** 密钥类字段名模式：无论 value 是否传入，展示层永不泄露 */
const SENSITIVE_KEY_RE = /(?:api[_-]?key|secret|token|password|credential|auth)/i

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
      { key: 'index_pattern', value: '—' }
    ]
  },
  {
    title: 'LLM',
    items: [
      { key: 'provider', value: '—' },
      { key: 'model', value: '—' },
      { key: 'api_key', value: '', sensitive: true }
    ]
  }
]

const props = defineProps({
  /** [{ title, items: [{ key, value, sensitive? }] }] */
  groups: { type: Array, default: () => [] },
  /** 有值时展示外链按钮 */
  kibanaUrl: { type: String, default: '' },
  /** Kibana 按钮文案 */
  kibanaLabel: { type: String, default: '打开 Kibana' },
  /** Discover 深链（F7-03 kibanaLinks 生成） */
  discoverUrl: { type: String, default: '' },
  /** Discover 按钮文案 */
  discoverLabel: { type: String, default: '在 Discover 中打开' }
})

const isPlaceholder = computed(() => props.groups.length === 0)

const displayGroups = computed(() =>
  isPlaceholder.value ? PLACEHOLDER_GROUPS : props.groups
)

const hasKibana = computed(() => Boolean(String(props.kibanaUrl || '').trim()))
const hasDiscover = computed(() => Boolean(String(props.discoverUrl || '').trim()))

function isSensitiveItem(item) {
  if (!item || typeof item !== 'object') return false
  if (item.sensitive === true) return true
  return SENSITIVE_KEY_RE.test(String(item.key || ''))
}

function formatValue(item) {
  if (isSensitiveItem(item)) return '***'
  const raw = item?.value
  if (raw === null || raw === undefined || raw === '') return '—'
  if (Array.isArray(raw)) {
    const text = raw.map((entry) => String(entry)).filter(Boolean).join(', ')
    return text || '—'
  }
  return String(raw)
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
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
}

.snapshot-group {
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
  box-shadow: var(--shadow-sm, 0 1px 2px rgb(15 23 42 / 6%));
  transition: box-shadow 0.18s ease, transform 0.18s ease;
}

.snapshot-group:hover {
  box-shadow: var(--shadow-md, 0 4px 12px rgb(15 23 42 / 8%));
  transform: translateY(-1px);
}

.snapshot-group h3 {
  margin: 0 0 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border);
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
  user-select: none;
}

.kibana-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
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

.kibana-btn--secondary {
  background: var(--color-surface);
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}

.kibana-hint {
  margin: var(--spacing-md) 0 0;
  font-size: 12px;
  color: var(--color-text-secondary);
}

@media (max-width: 1024px) {
  .snapshot-groups {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .snapshot-groups {
    grid-template-columns: 1fr;
  }

  .snapshot-group:hover {
    transform: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .snapshot-group {
    transition: none;
  }

  .snapshot-group:hover {
    transform: none;
  }
}
</style>
