<template>
  <section class="alert-table" aria-label="预警列表" :aria-busy="loading">
    <header class="alert-table__header">
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
            <th v-for="col in columns" :key="col.key" scope="col">{{ col.label }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in items"
            :key="row.alert_id"
            class="alert-row"
            :class="{
              'is-selected': row.alert_id === selectedId,
              'is-active': row.status === 'active'
            }"
            tabindex="0"
            @click="emit('select', row)"
            @keydown.enter="emit('select', row)"
          >
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
import EmptyState from '../common/EmptyState.vue'
import SeverityBadge from '../common/SeverityBadge.vue'
import { formatTime, formatNumber } from '../../utils/format.js'

defineProps({
  items: { type: Array, default: () => [] },
  total: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  selectedId: { type: String, default: '' },
  ackingId: { type: String, default: '' }
})

const emit = defineEmits(['select', 'ack', 'retry'])

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
  color: #dce4eb;
}

.alert-table__header {
  display: flex;
  justify-content: flex-end;
}

.alert-table__meta {
  font-size: 12px;
  color: #8e9aa6;
}

.alert-table__scroll {
  max-height: 430px;
  overflow: auto;
  border: 1px solid rgba(185, 196, 207, 0.16);
  border-radius: 2px;
  background:
    linear-gradient(90deg, rgba(111, 158, 172, 0.035) 0 1px, transparent 1px 28px),
    linear-gradient(180deg, rgba(255, 255, 255, 0.026) 0 1px, transparent 1px 28px),
    rgba(7, 10, 14, 0.58);
  background-size: 28px 28px;
}

.alert-table__scroll::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.alert-table__scroll::-webkit-scrollbar-track {
  background: rgba(7, 10, 14, 0.72);
}

.alert-table__scroll::-webkit-scrollbar-thumb {
  background: rgba(185, 196, 207, 0.22);
  border: 2px solid rgba(7, 10, 14, 0.72);
}

.alert-table__scroll.is-refreshing {
  opacity: 0.72;
  transition: opacity 200ms ease;
}

.alert-table__grid {
  width: 100%;
  min-width: 720px;
  border-collapse: collapse;
  font-size: 12px;
}

.alert-table__grid th {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 9px 11px;
  text-align: left;
  font-weight: 900;
  color: #9fb0ba;
  border-bottom: 1px solid rgba(185, 196, 207, 0.18);
  background: rgba(12, 15, 20, 0.96);
  white-space: nowrap;
  text-transform: uppercase;
}

.alert-table__grid td {
  padding: 9px 11px;
  border-bottom: 1px solid rgba(185, 196, 207, 0.1);
  color: #dce4eb;
  vertical-align: middle;
}

.alert-row {
  cursor: pointer;
  transition: background 150ms ease, box-shadow 150ms ease;
}

.alert-row:hover,
.alert-row:focus-visible {
  background: rgba(111, 158, 172, 0.08);
  outline: none;
}

.alert-row.is-selected {
  background: rgba(111, 158, 172, 0.12);
  box-shadow: inset 3px 0 0 #6f9eac;
}

.alert-row.is-active td:first-child {
  box-shadow: inset 3px 0 0 #b96a61;
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
  padding: 4px 10px;
  border: 1px solid rgba(111, 158, 172, 0.48);
  border-radius: 2px;
  background: rgba(111, 158, 172, 0.1);
  color: #c9dde2;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 150ms ease, color 150ms ease;
  clip-path: polygon(0 0, calc(100% - 8px) 0, 100% 100%, 0 100%);
}

.ack-btn:hover:not(:disabled) {
  background: rgba(111, 158, 172, 0.2);
  color: #f2f5f7;
}

.ack-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.status-tag {
  font-size: 12px;
  color: #8e9aa6;
}

.status-tag--acknowledged {
  color: #c3a06d;
}

.status-tag--resolved {
  color: #8ab49f;
}

.alert-table__retry {
  margin-top: var(--spacing-xs);
  padding: 6px 12px;
  border: 1px solid rgba(111, 158, 172, 0.48);
  border-radius: 2px;
  background: rgba(111, 158, 172, 0.1);
  color: #c9dde2;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
}

.alert-table__retry:hover {
  background: rgba(111, 158, 172, 0.18);
  color: #f2f5f7;
}

.skeleton-row td {
  padding: 12px;
}

.skeleton-block {
  display: block;
  height: 14px;
  border-radius: 2px;
  background: linear-gradient(
    90deg,
    rgba(185, 196, 207, 0.08) 25%,
    rgba(185, 196, 207, 0.18) 50%,
    rgba(185, 196, 207, 0.08) 75%
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
