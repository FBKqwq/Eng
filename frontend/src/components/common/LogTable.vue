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
            <th class="col-expand" scope="col" aria-label="展开原始 JSON" />
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
              <span v-if="col.unit && col.unit !== 'auto'" class="th-unit">({{ col.unit }})</span>
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
                  :aria-label="isExpanded(rowIndex) ? '收起 JSON' : '展开 JSON'"
                  @click="toggleExpand(rowIndex)"
                >
                  <span class="expand-icon" :class="{ open: isExpanded(rowIndex) }" />
                </button>
              </td>
              <td
                v-for="col in columns"
                :key="`${rowKey(row, rowIndex)}-${col.key}`"
                :class="cellClass(col, row)"
                @click.stop="handleCellClick(col, row, $event)"
              >
                <CellRenderer
                  :row="row"
                  :col="col"
                  :copied-key="copiedKey"
                  @copy="handleCopy"
                  @trace="handleTraceNavigate(row)"
                  @drill="handleDrill(col, row)"
                />
              </td>
            </tr>
            <tr v-if="isExpanded(rowIndex)" class="expand-row">
              <td :colspan="expandColspan">
                <div class="expand-panel">
                  <p class="expand-panel__hint">原始 JSON（辅助调试，非常规阅读入口）</p>
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
        <span class="page-info tabular-nums">第 {{ page }} / {{ totalPages }} 页</span>
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
import { computed, ref, defineComponent, h } from 'vue'
import EmptyState from './EmptyState.vue'
import SeverityBadge from './SeverityBadge.vue'
import { formatNumber } from '../../utils/format.js'
import {
  formatCellDisplay,
  getRowField,
  httpStatusTone,
  copyText
} from '../../utils/logTableCells.js'

const props = defineProps({
  columns: { type: Array, default: () => [] },
  items: { type: Array, default: () => [] },
  total: { type: Number, default: 0 },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 20 },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  logType: { type: String, default: '' },
  drillableFields: { type: Array, default: () => [] },
  sort: {
    type: Object,
    default: () => ({ field: 'timestamp', order: 'desc' })
  }
})

const emit = defineEmits([
  'update:page',
  'update:pageSize',
  'sort-change',
  'trace-navigate',
  'drill',
  'retry'
])

const pageSizeOptions = [10, 20, 50, 100]
const skeletonRowCount = 6
const copiedKey = ref('')
let copiedTimer = null

const expandedRows = ref(new Set())

const CellRenderer = defineComponent({
  name: 'CellRenderer',
  props: {
    row: { type: Object, required: true },
    col: { type: Object, required: true },
    copiedKey: { type: String, default: '' }
  },
  emits: ['copy', 'trace', 'drill'],
  setup(cellProps, { emit: cellEmit }) {
    return () => {
      const { row, col } = cellProps
      const renderType = col.renderType || inferRenderType(col.key)
      const value = getRowField(row, col.key)
      const display = formatCellDisplay(row, { ...col, renderType })

      if (renderType === 'log_level' || renderType === 'risk_level') {
        return h(SeverityBadge, { level: String(value ?? ''), label: display })
      }

      if (renderType === 'http_status') {
        return h('span', { class: ['http-status-pill', `tone-${httpStatusTone(value)}`] }, display)
      }

      if (renderType === 'trace') {
        if (!value) return h('span', { class: 'cell-muted' }, '—')
        return h('div', { class: 'cell-inline-actions' }, [
          h('span', { class: 'cell-mono cell-ellipsis' }, display),
          h(
            'button',
            {
              type: 'button',
              class: 'cell-action-btn',
              onClick: (e) => {
                e.stopPropagation()
                cellEmit('trace')
              }
            },
            '追踪'
          )
        ])
      }

      if (renderType === 'copyable' && value) {
        const copyId = `${col.key}-${String(value)}`
        return h('div', { class: 'cell-inline-actions' }, [
          h('span', { class: 'cell-mono cell-ellipsis', title: display }, display),
          h(
            'button',
            {
              type: 'button',
              class: 'cell-action-btn',
              onClick: (e) => {
                e.stopPropagation()
                cellEmit('copy', { key: copyId, text: value })
              }
            },
            cellProps.copiedKey === copyId ? '已复制' : '复制'
          ),
          col.drillable
            ? h(
                'button',
                {
                  type: 'button',
                  class: 'cell-action-btn cell-action-btn--ghost',
                  onClick: (e) => {
                    e.stopPropagation()
                    cellEmit('drill')
                  }
                },
                '筛选'
              )
            : null
        ])
      }

      if (renderType === 'change_summary') {
        return h('span', { class: 'cell-ellipsis cell-pre-wrap', title: display }, display)
      }

      return h(
        'span',
        {
          class: ['cell-text', renderType === 'duration' || renderType === 'metric' ? 'tabular-nums' : ''],
          title: display.length > 40 ? display : undefined
        },
        display
      )
    }
  }
})

function inferRenderType(key) {
  if (key === 'log_level') return 'log_level'
  if (key === 'status_code') return 'http_status'
  if (key === 'risk_level') return 'risk_level'
  if (key === 'trace_id') return 'trace'
  if (['client_ip', 'request_uri', 'request_path', 'upstream_addr'].includes(key)) return 'copyable'
  if (key === 'response_time_ms' || key === 'duration_ms') return 'duration'
  if (key === 'metric_value') return 'metric'
  if (key === 'change_summary') return 'change_summary'
  return 'text'
}

const totalPages = computed(() => {
  const size = Math.max(1, props.pageSize)
  return Math.max(1, Math.ceil(props.total / size))
})

const showPagination = computed(() => !props.error && (props.total > 0 || props.items.length > 0))
const expandColspan = computed(() => Math.max(props.columns.length + 1, 1))

function columnStyle(col) {
  if (!col.width) return undefined
  return { width: col.width, minWidth: col.width, maxWidth: col.width }
}

function skeletonWidth(col) {
  if (col.renderType === 'trace' || col.key === 'trace_id') return '72%'
  if (col.renderType === 'timestamp') return '88%'
  return '64%'
}

function rowKey(row, index) {
  return row?.log_id ?? row?.id ?? row?._id ?? `row-${index}`
}

function isExpanded(index) {
  return expandedRows.value.has(index)
}

function toggleExpand(index) {
  const next = new Set(expandedRows.value)
  if (next.has(index)) next.delete(index)
  else next.add(index)
  expandedRows.value = next
}

function cellClass(col, row) {
  const value = getRowField(row, col.key)
  return {
    'cell-level': col.renderType === 'log_level' || col.renderType === 'risk_level',
    'cell-numeric': col.renderType === 'duration' || col.renderType === 'metric' || col.renderType === 'http_status',
    'cell-actions': col.renderType === 'copyable' || col.renderType === 'trace',
    'tabular-nums': typeof value === 'number'
  }
}

function formatRowJson(row) {
  const source = row?.payload && typeof row.payload === 'object' ? row.payload : row
  try {
    return JSON.stringify(source, null, 2)
  } catch {
    return String(source)
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
  if (props.page !== 1) emit('update:page', 1)
}

function handleTraceNavigate(row) {
  const traceId = getRowField(row, 'trace_id')
  if (!traceId) return
  emit('trace-navigate', String(traceId))
}

function handleDrill(col, row) {
  const value = getRowField(row, col.key)
  if (!value) return
  emit('drill', { target: col.drillTarget || 'keyword', value: String(value), field: col.key })
}

async function handleCopy({ key, text }) {
  const ok = await copyText(text)
  if (!ok) return
  copiedKey.value = key
  if (copiedTimer) clearTimeout(copiedTimer)
  copiedTimer = setTimeout(() => {
    copiedKey.value = ''
  }, 1500)
}

function handleCellClick(col, row, event) {
  if (col.drillable && col.drillTarget === 'trace') {
    event.stopPropagation()
    handleTraceNavigate(row)
  }
}
</script>

<style scoped>
.log-table {
  margin-top: 0;
  border: 1px solid #111827;
  border-radius: 0;
  background: #ffffff;
  overflow: hidden;
  box-shadow: 6px 6px 0 rgba(15, 23, 42, 0.08);
}

.log-table-header {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  min-height: 42px;
  padding: 8px 14px 8px 30px;
  border-bottom: 2px solid #111827;
  background: #f8fafc;
}

.log-table-header::before {
  position: absolute;
  inset: 0 auto 0 0;
  width: 18px;
  background: #111827;
  clip-path: polygon(0 0, 100% 0, 58% 100%, 0 100%);
  content: '';
}

.log-table-header h3 {
  margin: 0;
  font-size: 13px;
  font-weight: 900;
  letter-spacing: 0.08em;
  color: #111827;
}

.log-table-meta {
  padding: 2px 8px;
  border-left: 3px solid #111827;
  background: #e5e7eb;
  font-size: 11px;
  font-weight: 800;
  color: #374151;
}

.log-table-scroll {
  overflow: auto;
  -webkit-overflow-scrolling: touch;
  transition: opacity 180ms ease;
  background:
    linear-gradient(90deg, rgba(15, 23, 42, 0.025) 0 1px, transparent 1px 32px),
    #ffffff;
  background-size: 32px 32px;
}

.log-table-scroll::-webkit-scrollbar,
.expand-json::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.log-table-scroll::-webkit-scrollbar-track,
.expand-json::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.log-table-scroll::-webkit-scrollbar-thumb,
.expand-json::-webkit-scrollbar-thumb {
  background: #94a3b8;
  border: 2px solid #f1f5f9;
}

.log-table-scroll.is-refreshing {
  opacity: 0.72;
  pointer-events: none;
}

.log-table-grid {
  width: 100%;
  min-width: 640px;
  border-collapse: collapse;
  font-size: 11px;
  table-layout: fixed;
}

.log-table-grid th {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: 8px 10px;
  text-align: left;
  font-weight: 900;
  letter-spacing: 0.04em;
  color: #111827;
  border-right: 1px solid #d1d5db;
  border-bottom: 1px solid #111827;
  background: #e5e7eb;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-transform: uppercase;
}

.log-table-grid th:last-child {
  border-right: 0;
}

.log-table-grid th.sortable {
  cursor: pointer;
}

.log-table-grid th.sortable:hover {
  color: #000000;
  background: #cbd5e1;
}

.log-table-grid th.sorted {
  color: #000000;
  box-shadow: inset 0 -3px 0 #111827;
}

.th-unit {
  margin-left: 2px;
  font-size: 11px;
  color: #64748b;
  font-weight: 800;
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
  padding: 7px 10px;
  border-right: 1px solid #edf0f3;
  border-bottom: 1px solid #d8dee6;
  color: #1f2937;
  vertical-align: middle;
  overflow: hidden;
}

.log-table-grid td:last-child {
  border-right: 0;
}

.data-row {
  cursor: pointer;
  transition: background-color 160ms ease;
}

.data-row:nth-child(even) {
  background: #f8fafc;
}

.data-row:hover {
  background: #eef2f6;
  box-shadow: inset 3px 0 0 #111827;
}

.data-row.expanded {
  background: #e5e7eb;
  box-shadow: inset 3px 0 0 #111827;
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
  border: 1px solid #9ca3af;
  border-radius: 0;
  background: #ffffff;
  color: #111827;
  cursor: pointer;
}

.expand-btn:hover {
  border-color: #111827;
  background: #111827;
  color: #ffffff;
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

.cell-text,
.cell-ellipsis {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-pre-wrap {
  white-space: normal;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.cell-mono {
  font-family: var(--font-mono);
  font-size: 11px;
}

.cell-muted {
  color: #94a3b8;
}

.cell-inline-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.cell-action-btn {
  flex-shrink: 0;
  padding: 2px 6px;
  border: 1px solid #64748b;
  border-radius: 0;
  background: #ffffff;
  color: #334155;
  font-size: 11px;
  font-weight: 900;
  cursor: pointer;
}

.cell-action-btn--ghost {
  color: #64748b;
}

.cell-action-btn:hover {
  border-color: #111827;
  background: #111827;
  color: #ffffff;
}

.http-status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  padding: 2px 8px;
  border-radius: 0;
  font-size: 12px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.http-status-pill.tone-success {
  background: #dcfce7;
  color: #166534;
}

.http-status-pill.tone-warning {
  background: #fef3c7;
  color: #92400e;
}

.http-status-pill.tone-danger {
  background: #fee2e2;
  color: #991b1b;
}

.http-status-pill.tone-info {
  background: #e0f2fe;
  color: #075985;
}

.http-status-pill.tone-muted {
  background: #e5e7eb;
  color: #475569;
}

.expand-row td {
  padding: 0;
  background: #f8fafc;
}

.expand-panel {
  padding: var(--spacing-sm) var(--spacing-md) var(--spacing-md);
}

.expand-panel__hint {
  margin: 0 0 8px;
  font-size: 11px;
  color: #64748b;
}

.expand-json {
  margin: 0;
  padding: 12px;
  border: 1px solid #cbd5e1;
  border-left: 4px solid #111827;
  border-radius: 0;
  background: #ffffff;
  color: #0f172a;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.5;
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
  border-radius: 0;
  background: linear-gradient(90deg, #e5e7eb 0%, #f8fafc 50%, #e5e7eb 100%);
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
  border-top: 2px solid #111827;
  background: #f8fafc;
}

.page-size-control {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #475569;
}

.page-size-select {
  padding: 4px 8px;
  border: 1px solid #64748b;
  border-radius: 0;
  background: #ffffff;
  color: #111827;
  font-size: 13px;
}

.pagination-controls {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.page-btn {
  padding: 6px 12px;
  border: 1px solid #64748b;
  border-radius: 0;
  background: #ffffff;
  color: #111827;
  font-size: 13px;
  cursor: pointer;
}

.page-btn:hover:not(:disabled) {
  border-color: #111827;
  background: #111827;
  color: #ffffff;
}

.page-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: #475569;
}

.retry-btn {
  margin-top: var(--spacing-sm);
  padding: 6px 16px;
  border: 1px solid #111827;
  border-radius: 0;
  background: #111827;
  color: #ffffff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

@keyframes skeleton-shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

@media (max-width: 640px) {
  .log-table-grid {
    min-width: 520px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .log-table-scroll,
  .data-row,
  .expand-icon,
  .skeleton-block {
    transition: none;
    animation: none;
  }
}
</style>
