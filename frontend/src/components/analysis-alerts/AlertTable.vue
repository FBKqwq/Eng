<template>
  <section class="alert-table" aria-label="预警列表" :aria-busy="loading">
    <header class="alert-table__header">
      <div class="alert-table__search">
        <input
          type="text"
          v-model="searchQuery"
          class="alert-table__search-input"
          placeholder="搜索预警标题、服务名..."
          @input="handleSearch"
        />
        <span class="alert-table__search-icon">🔍</span>
      </div>
      <span v-if="total > 0" class="alert-table__meta tabular-nums">共 {{ formatNumber(total) }} 条</span>
    </header>

    <EmptyState
      v-if="error && !loading"
      compact
      title="预警列表加载失败"
      :description="error"
    >
      <button type="button" class="alert-table__retry" @click="emit('retry')">重试</button>
    </EmptyState>

    <div v-else-if="loading && !items.length" class="alert-table__scroll">
      <table class="alert-table__grid">
        <thead>
          <tr>
            <th v-for="col in columns" :key="`sk-${col.key}`">{{ col.label }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="n in 4" :key="n" class="skeleton-row">
            <td v-for="col in columns" :key="`${n}-${col.key}`">
              <span class="skeleton-block" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <EmptyState
      v-else-if="!items.length"
      compact
      title="暂无预警"
      description="当前没有匹配的预警记录"
    />

    <div v-else class="alert-table__scroll" :class="{ 'is-refreshing': loading }">
      <table class="alert-table__grid">
        <thead>
          <tr>
            <th scope="col" class="alert-table__select-header">
              <input
                type="checkbox"
                class="alert-table__select-all"
                :checked="filteredItems.length > 0 && filteredItems.every(item => selectedIds?.has(item.alert_id))"
                @change="handleSelectAll"
              />
            </th>
            <th v-for="col in columns" :key="col.key" scope="col">{{ col.label }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in filteredItems"
            :key="row.alert_id"
            class="alert-row"
            :class="{
              'is-selected': row.alert_id === selectedId,
              'is-active': row.status === 'active',
              'is-multi-selected': selectedIds?.has(row.alert_id)
            }"
            tabindex="0"
            @click="handleRowClick(row)"
            @keydown.enter="emit('select', row)"
          >
            <td class="alert-table__select-cell">
              <input
                type="checkbox"
                class="alert-table__select-box"
                :checked="selectedIds?.has(row.alert_id)"
                @click.stop="emit('toggle-select', row.alert_id)"
              />
            </td>
            <td>{{ formatAlertType(row.alert_type) }}</td>
            <td>
              <SeverityBadge :level="row.severity" :label="formatSeverity(row.severity)" />
            </td>
            <td class="cell-service">{{ row.affected_service || '—' }}</td>
            <td class="tabular-nums">{{ formatTime(row.created_at) }}</td>
            <td class="tabular-nums">{{ formatTime(row.updated_at) }}</td>
            <td class="tabular-nums">{{ formatNumber(row.evidence_count ?? 0) }}</td>
            <td class="cell-actions" @click.stop>
              <button
                v-if="row.status === 'active'"
                type="button"
                class="ack-btn"
                :disabled="ackingId === row.alert_id"
                @click="emit('ack', row.alert_id)"
              >
                {{ ackingId === row.alert_id ? '确认中…' : '确认' }}
              </button>
              <span v-else class="status-tag" :class="`status-tag--${row.status}`">
                {{ formatStatus(row.status) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import EmptyState from '../common/EmptyState.vue'
import SeverityBadge from '../common/SeverityBadge.vue'
import { formatTime, formatNumber } from '../../utils/format.js'

const props = defineProps({
  items: { type: Array, default: () => [] },
  total: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  selectedId: { type: String, default: '' },
  ackingId: { type: String, default: '' },
  selectedIds: { type: Set, default: () => new Set() }
})

const emit = defineEmits(['select', 'ack', 'retry', 'search', 'toggle-select'])

const searchQuery = ref('')

const filteredItems = ref(props.items)

function handleRowClick(row) {
  emit('select', row)
}

function handleSelectAll(event) {
  const checked = event.target.checked
  filteredItems.value.forEach(item => {
    emit('toggle-select', item.alert_id)
  })
}

function handleSearch() {
  const query = searchQuery.value.toLowerCase().trim()
  if (!query) {
    filteredItems.value = props.items
  } else {
    filteredItems.value = props.items.filter(item => {
      const title = (item.title || '').toLowerCase()
      const service = (item.affected_service || '').toLowerCase()
      const type = (item.alert_type || '').toLowerCase()
      return title.includes(query) || service.includes(query) || type.includes(query)
    })
  }
  emit('search', { query, count: filteredItems.value.length })
}

const columns = [
  { key: 'alert_type', label: '类型' },
  { key: 'severity', label: '严重度' },
  { key: 'affected_service', label: '服务' },
  { key: 'created_at', label: '首次时间' },
  { key: 'updated_at', label: '最近时间' },
  { key: 'evidence_count', label: '证据数' },
  { key: 'actions', label: '操作' }
]

const ALERT_TYPE_LABELS = {
  error_rate_spike: '错误率',
  latency_degradation: '耗时',
  security_risk: '安全',
  infra_health: '基础设施',
  traffic_anomaly: '流量',
  pay_fail: '支付失败',
  error_spike: '错误激增',
  latency_spike: '延迟异常'
}

const SEVERITY_LABELS = {
  low: '低',
  medium: '中',
  high: '高',
  critical: '严重'
}

const STATUS_LABELS = {
  active: '活跃',
  acknowledged: '已确认',
  resolved: '已解决'
}

function formatAlertType(type) {
  if (!type) return '—'
  return ALERT_TYPE_LABELS[type] ?? String(type).replace(/_/g, ' ')
}

function formatSeverity(level) {
  if (!level) return '—'
  return SEVERITY_LABELS[level.toLowerCase()] ?? level
}

function formatStatus(status) {
  if (!status) return '—'
  return STATUS_LABELS[status] ?? status
}
</script>

<style scoped>
.alert-table {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.alert-table__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.alert-table__search {
  position: relative;
  flex-shrink: 0;
}

.alert-table__search-input {
  width: 240px;
  padding: 6px 32px 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  font-size: 13px;
  color: var(--color-text);
  outline: none;
  transition: border-color 120ms ease;
}

.alert-table__search-input:focus {
  border-color: var(--color-primary);
}

.alert-table__search-input::placeholder {
  color: var(--color-text-muted);
}

.alert-table__search-icon {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 14px;
  color: var(--color-text-muted);
  pointer-events: none;
}

.alert-table__meta {
  font-size: 12px;
  color: var(--color-text-muted);
}

.alert-table__scroll {
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.alert-table__scroll.is-refreshing {
  opacity: 0.72;
  transition: opacity 200ms ease;
}

.alert-table__grid {
  width: 100%;
  min-width: 720px;
  border-collapse: collapse;
  font-size: 13px;
}

.alert-table__grid th {
  padding: 10px 12px;
  text-align: left;
  font-weight: 500;
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
  white-space: nowrap;
}

.alert-table__grid td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text);
  vertical-align: middle;
}

.alert-row {
  cursor: pointer;
  transition: background 150ms ease;
}

.alert-row:hover,
.alert-row:focus-visible {
  background: color-mix(in srgb, var(--color-primary) 6%, transparent);
  outline: none;
}

.alert-row.is-selected {
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
}

.alert-row.is-multi-selected {
  background: color-mix(in srgb, var(--color-primary) 8%, transparent);
}

.alert-row.is-active td:first-child {
  box-shadow: inset 3px 0 0 var(--color-danger);
}

.cell-service {
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-actions {
  white-space: nowrap;
}

.ack-btn {
  padding: 4px 12px;
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-primary);
  font-size: 12px;
  cursor: pointer;
  transition: background 150ms ease, color 150ms ease;
}

.ack-btn:hover:not(:disabled) {
  background: var(--color-primary);
  color: var(--color-surface);
}

.ack-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.status-tag {
  font-size: 12px;
  color: var(--color-text-muted);
}

.status-tag--acknowledged {
  color: var(--color-warning);
}

.status-tag--resolved {
  color: var(--color-success);
}

.alert-table__select-header {
  width: 40px;
  padding: 10px 8px;
}

.alert-table__select-cell {
  width: 40px;
  padding: 10px 8px;
}

.alert-table__select-all,
.alert-table__select-box {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.alert-table__retry {
  margin-top: var(--spacing-xs);
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-size: 13px;
  cursor: pointer;
}

.skeleton-row td {
  padding: 12px;
}

.skeleton-block {
  display: block;
  height: 14px;
  border-radius: var(--radius-sm);
  background: linear-gradient(
    90deg,
    var(--color-bg) 25%,
    var(--color-border) 50%,
    var(--color-bg) 75%
  );
  background-size: 200% 100%;
  animation: alert-table-shimmer 1.2s ease-in-out infinite;
}

@keyframes alert-table-shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .alert-row,
  .alert-table__scroll.is-refreshing {
    transition: none;
  }

  .skeleton-block {
    animation: none;
    background: var(--color-bg);
  }
}
</style>
