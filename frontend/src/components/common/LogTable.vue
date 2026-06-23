<template>
  <section class="log-table" aria-label="日志明细表" :aria-busy="loading">
    <header class="log-table-header">
      <h3>日志明细</h3>
      <span v-if="!error && total > 0" class="log-table-meta tabular-nums">
        共 {{ formatNumber(total) }} 条
      </span>
    </header>

    <EmptyState
      v-if="error && !loading"
      title="查询失败"
      :description="error"
      compact
    >
      <button type="button" class="retry-btn" @click="emit('retry')">重试</button>
    </EmptyState>

    <div v-else-if="loading && !items.length" class="log-table-scroll">
      <table class="log-table-grid">
        <thead>
          <tr>
            <th class="col-expand" scope="col" aria-hidden="true" />
            <th
              v-for="col in columns"
              :key="`sk-head-${col.key}`"
              scope="col"
              :style="columnStyle(col)"
            >
              {{ col.label }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="n in skeletonRowCount" :key="`sk-${n}`" class="skeleton-row">
            <td class="col-expand"><span class="skeleton-block skeleton-block--sm" /></td>
            <td v-for="col in columns" :key="`sk-cell-${n}-${col.key}`">
              <span class="skeleton-block" :style="{ width: skeletonWidth(col) }" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <EmptyState
      v-else-if="!items.length"
      title="暂无日志"
      description="当前筛选条件下没有匹配的日志记录"
      compact
    />

    <div v-else class="log-table-scroll" :class="{ 'is-refreshing': loading }">
      <table class="log-table-grid">
        <thead>
          <tr>
            <th class="col-expand" scope="col" aria-label="展开行" />
            <th
              v-for="col in columns"
              :key="col.key"
              scope="col"
              :style="columnStyle(col)"
              :class="{
                sortable: col.sortable,
                sorted: col.sortable && sort?.field === col.key
              }"
              :aria-sort="ariaSort(col)"
              @click="col.sortable && handleSort(col.key)"
            >
              <span class="th-label">{{ col.label }}</span>
              <span v-if="col.sortable" class="sort-indicator" aria-hidden="true">
                <span
                  class="sort-caret sort-caret--up"
                  :class="{ active: sort?.field === col.key && sort?.order === 'asc' }"
                />
                <span
                  class="sort-caret sort-caret--down"
                  :class="{ active: sort?.field === col.key && sort?.order === 'desc' }"
                />
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <template v-for="(row, rowIndex) in items" :key="rowKey(row, rowIndex)">
            <tr
              class="data-row"
              :class="{ expanded: isExpanded(rowIndex) }"
              @click="toggleExpand(rowIndex)"
            >
              <td class="col-expand" @click.stop>
                <button
                  type="button"
                  class="expand-btn"
                  :aria-expanded="isExpanded(rowIndex)"
                  :aria-label="isExpanded(rowIndex) ? '收起行详情' : '展开行详情'"
                  @click="toggleExpand(rowIndex)"
                >
                  <span class="expand-icon" :class="{ open: isExpanded(rowIndex) }" />
                </button>
              </td>
              <td
                v-for="col in columns"
                :key="`${rowKey(row, rowIndex)}-${col.key}`"
                :class="cellClass(col, row)"
                @click="col.key === 'trace_id' && stopRowToggle($event)"
              >
                <SeverityBadge
                  v-if="isLevelColumn(col.key)"
                  :level="String(getCellValue(row, col.key) ?? '')"
                />
                <template v-else-if="col.key === 'trace_id'">
                  <span class="trace-id tabular-nums">{{ displayCell(row, col) }}</span>
                  <button
                    v-if="getCellValue(row, 'trace_id')"
                    type="button"
                    class="trace-btn"
                    @click.stop="handleTraceNavigate(row)"
                  >
                    追踪
                  </button>
                </template>
                <span v-else class="cell-text">{{ displayCell(row, col) }}</span>
              </td>
            </tr>
            <tr v-if="isExpanded(rowIndex)" class="expand-row">
              <td :colspan="expandColspan">
                <div class="expand-panel">
                  <pre class="expand-json">{{ formatRowJson(row) }}</pre>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <footer v-if="showPagination" class="log-table-footer">
      <label class="page-size-control">
        <span class="page-size-label">每页</span>
        <select
          class="page-size-select tabular-nums"
          :value="pageSize"
          :disabled="loading"
          @change="handlePageSizeChange"
        >
          <option v-for="size in pageSizeOptions" :key="size" :value="size">
            {{ size }}
          </option>
        </select>
        <span class="page-size-label">条</span>
      </label>

      <div class="pagination-controls">
        <button
          type="button"
          class="page-btn"
          :disabled="loading || page <= 1"
          @click="goPage(page - 1)"
        >
          上一页
        </button>
        <span class="page-info tabular-nums">
          第 {{ page }} / {{ totalPages }} 页
        </span>
        <button
          type="button"
          class="page-btn"
          :disabled="loading || page >= totalPages"
          @click="goPage(page + 1)"
        >
          下一页
        </button>
      </div>
    </footer>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import EmptyState from './EmptyState.vue'
import SeverityBadge from './SeverityBadge.vue'
import { formatDuration, formatNumber, formatTime } from '../../utils/format.js'

const props = defineProps({
  columns: { type: Array, default: () => [] },
  items: { type: Array, default: () => [] },
  total: { type: Number, default: 0 },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 20 },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  sort: {
    type: Object,
    default: () => ({ field: '@timestamp', order: 'desc' })
  }
})

const emit = defineEmits([
  'update:page',
  'update:pageSize',
  'sort-change',
  'trace-navigate',
  'retry'
])

const pageSizeOptions = [10, 20, 50, 100]
const skeletonRowCount = 6

const LEVEL_KEYS = new Set(['log_level', 'level', 'severity', 'risk_level'])
const TIMESTAMP_KEYS = new Set(['@timestamp', 'timestamp', 'time', 'created_at'])
const DURATION_KEYS = new Set([
  'duration_ms',
  'latency_ms',
  'response_time',
  'elapsed_ms',
  'stay_duration'
])
const NUMERIC_KEYS = new Set([
  'status_code',
  'statusCode',
  'error_code',
  'metric_value',
  'evidence_count'
])

const expandedRows = ref(new Set())

const totalPages = computed(() => {
  const size = Math.max(1, props.pageSize)
  return Math.max(1, Math.ceil(props.total / size))
})

const showPagination = computed(() => !props.error && (props.total > 0 || props.items.length > 0))

const expandColspan = computed(() => Math.max(props.columns.length + 1, 1))

function columnStyle(col) {
  if (!col.width) return undefined
  return { width: col.width, minWidth: col.width }
}

function skeletonWidth(col) {
  if (col.key === 'trace_id') return '72%'
  if (TIMESTAMP_KEYS.has(col.key)) return '88%'
  return '64%'
}

function rowKey(row, index) {
  return row?.id ?? row?._id ?? row?.trace_id ?? `row-${index}`
}

function isExpanded(index) {
  return expandedRows.value.has(index)
}

function toggleExpand(index) {
  const next = new Set(expandedRows.value)
  if (next.has(index)) {
    next.delete(index)
  } else {
    next.add(index)
  }
  expandedRows.value = next
}

function stopRowToggle(event) {
  event.stopPropagation()
}

function getCellValue(row, key) {
  if (!row || key == null) return undefined
  return row[key]
}

function isLevelColumn(key) {
  return LEVEL_KEYS.has(key)
}

function isNumericColumn(key, value) {
  if (NUMERIC_KEYS.has(key)) return true
  if (DURATION_KEYS.has(key)) return true
  if (TIMESTAMP_KEYS.has(key)) return true
  return typeof value === 'number' && Number.isFinite(value)
}

function displayCell(row, col) {
  const value = getCellValue(row, col.key)
  if (value == null || value === '') return '—'

  if (TIMESTAMP_KEYS.has(col.key)) {
    return formatTime(value)
  }
  if (DURATION_KEYS.has(col.key)) {
    return formatDuration(value)
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}

function cellClass(col, row) {
  const value = getCellValue(row, col.key)
  return {
    'cell-level': isLevelColumn(col.key),
    'cell-trace': col.key === 'trace_id',
    'tabular-nums': isNumericColumn(col.key, value)
  }
}

function formatRowJson(row) {
  try {
    return JSON.stringify(row, null, 2)
  } catch {
    return String(row)
  }
}

function ariaSort(col) {
  if (!col.sortable) return undefined
  if (props.sort?.field !== col.key) return 'none'
  return props.sort?.order === 'asc' ? 'ascending' : 'descending'
}

function handleSort(field) {
  const currentField = props.sort?.field
  const currentOrder = props.sort?.order === 'asc' ? 'asc' : 'desc'
  const order = currentField === field && currentOrder === 'desc' ? 'asc' : 'desc'
  emit('sort-change', { field, order })
}

function goPage(nextPage) {
  const normalized = Math.floor(Number(nextPage))
  if (!Number.isFinite(normalized)) return
  if (normalized < 1 || normalized > totalPages.value || normalized === props.page) return
  emit('update:page', normalized)
}

function handlePageSizeChange(event) {
  const nextSize = Number(event.target.value)
  if (!Number.isFinite(nextSize) || nextSize < 1) return
  emit('update:pageSize', nextSize)
  if (props.page !== 1) {
    emit('update:page', 1)
  }
}

function handleTraceNavigate(row) {
  const traceId = getCellValue(row, 'trace_id')
  if (!traceId) return
  emit('trace-navigate', String(traceId))
}
</script>

<style scoped>
.log-table {
  margin-top: var(--spacing-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.log-table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
}

.log-table-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.log-table-meta {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.log-table-scroll {
  overflow-x: auto;
  transition: opacity 180ms ease;
}

.log-table-scroll.is-refreshing {
  opacity: 0.72;
  pointer-events: none;
}

.log-table-grid {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.log-table-grid th {
  padding: 10px 12px;
  text-align: left;
  font-weight: 500;
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
  white-space: nowrap;
  user-select: none;
}

.log-table-grid th.sortable {
  cursor: pointer;
}

.log-table-grid th.sortable:hover {
  color: var(--color-text);
  background: #eceff3;
}

.log-table-grid th.sorted {
  color: var(--color-primary);
}

.th-label {
  vertical-align: middle;
}

.sort-indicator {
  display: inline-flex;
  flex-direction: column;
  margin-left: 4px;
  vertical-align: middle;
  gap: 1px;
}

.sort-caret {
  display: block;
  width: 0;
  height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  opacity: 0.25;
}

.sort-caret--up {
  border-bottom: 5px solid currentColor;
}

.sort-caret--down {
  border-top: 5px solid currentColor;
}

.sort-caret.active {
  opacity: 1;
}

.log-table-grid td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text);
  vertical-align: middle;
  max-width: 280px;
}

.data-row {
  cursor: pointer;
  transition: background-color 160ms ease;
}

.data-row:hover {
  background: #f9fafb;
}

.data-row.expanded {
  background: #f3f4f6;
}

.col-expand {
  width: 40px;
  min-width: 40px;
  padding-left: 8px;
  padding-right: 4px;
}

.expand-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition:
    border-color 160ms ease,
    color 160ms ease,
    transform 160ms ease;
}

.expand-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.expand-icon {
  display: block;
  width: 0;
  height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-left: 6px solid currentColor;
  transition: transform 200ms ease;
}

.expand-icon.open {
  transform: rotate(90deg);
}

.cell-text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-trace {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 140px;
}

.trace-id {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.trace-btn {
  flex-shrink: 0;
  padding: 2px 8px;
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-sm);
  background: var(--color-info-bg);
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition:
    background-color 160ms ease,
    color 160ms ease;
}

.trace-btn:hover {
  background: var(--color-primary);
  color: var(--color-surface);
}

.expand-row td {
  padding: 0;
  border-bottom: 1px solid var(--color-border);
  background: #f9fafb;
}

.expand-panel {
  padding: var(--spacing-sm) var(--spacing-md) var(--spacing-md);
  animation: expand-in 220ms ease-out;
}

.expand-json {
  margin: 0;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  line-height: 1.5;
  color: var(--color-text);
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.skeleton-row td {
  padding: 12px;
}

.skeleton-block {
  display: block;
  height: 12px;
  border-radius: 4px;
  background: linear-gradient(90deg, #eceff3 0%, #f5f6f8 50%, #eceff3 100%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.2s ease-in-out infinite;
}

.skeleton-block--sm {
  width: 16px;
  height: 16px;
  margin: 0 auto;
}

.log-table-footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-top: 1px solid var(--color-border);
  background: var(--color-bg);
}

.page-size-control {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.page-size-select {
  padding: 4px 8px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: 13px;
}

.pagination-controls {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.page-btn {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: 13px;
  cursor: pointer;
  transition:
    border-color 160ms ease,
    color 160ms ease;
}

.page-btn:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.page-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.retry-btn {
  margin-top: var(--spacing-sm);
  padding: 6px 16px;
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: var(--color-surface);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 160ms ease;
}

.retry-btn:hover {
  opacity: 0.9;
}

@keyframes expand-in {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes skeleton-shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .log-table-scroll,
  .data-row,
  .expand-btn,
  .expand-icon,
  .trace-btn,
  .page-btn,
  .retry-btn {
    transition: none;
  }

  .expand-panel {
    animation: none;
  }

  .skeleton-block {
    animation: none;
    background: #eceff3;
  }
}
</style>
