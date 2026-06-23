<template>
  <div class="dynamic-filter-bar">
    <p v-if="isFallback" class="fallback-tag">字段目录兜底</p>

    <div v-if="loading" class="filter-skeleton" aria-busy="true" aria-label="加载筛选字段">
      <div v-for="n in 4" :key="n" class="skeleton-field" />
    </div>

    <template v-else>
      <div class="filter-grid">
        <div
          v-for="field in visibleFields"
          :key="field.key"
          class="filter-field"
        >
          <label class="filter-label" :for="inputId(field)">{{ field.label }}</label>

          <!-- 枚举 terms：下拉 -->
          <select
            v-if="field.type === 'terms' && field.options?.length"
            :id="inputId(field)"
            class="filter-control"
            :multiple="field.multiple"
            :value="selectValue(field)"
            @change="onSelectChange(field, $event)"
          >
            <option v-if="!field.multiple" value="">全部</option>
            <option v-for="opt in field.options" :key="opt" :value="opt">{{ opt }}</option>
          </select>

          <!-- 自由 terms：逗号分隔 -->
          <input
            v-else-if="field.type === 'terms'"
            :id="inputId(field)"
            class="filter-control"
            type="text"
            :value="termsText(field)"
            placeholder="多个值用逗号分隔"
            @input="onTermsInput(field, $event)"
          />

          <!-- 数值范围 -->
          <div v-else-if="field.type === 'range'" class="range-row">
            <input
              :id="inputId(field)"
              class="filter-control range-input"
              type="number"
              :value="rangePart(field, 'gte')"
              placeholder="最小"
              @input="onRangeInput(field, 'gte', $event)"
            />
            <span class="range-sep">—</span>
            <input
              class="filter-control range-input"
              type="number"
              :value="rangePart(field, 'lte')"
              placeholder="最大"
              @input="onRangeInput(field, 'lte', $event)"
            />
          </div>

          <!-- 关键字 / 单值 -->
          <input
            v-else
            :id="inputId(field)"
            class="filter-control"
            type="text"
            :value="scalarValue(field)"
            :placeholder="field.placeholder || '输入筛选值'"
            @input="onKeywordFieldInput(field, $event)"
          />
        </div>

        <div class="filter-field filter-field--keyword">
          <label class="filter-label" for="filter-keyword">关键字</label>
          <input
            id="filter-keyword"
            class="filter-control"
            type="search"
            :value="keyword"
            placeholder="搜索 message、服务名等"
            @input="onKeywordChange"
          />
        </div>
      </div>

      <div class="filter-actions">
        <button type="button" class="btn-reset" @click="resetFilters">重置筛选</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { getLogFields } from '../../api/logs.js'
import { getLogTypeMeta } from '../../utils/logTypeMeta.js'

const props = defineProps({
  logType: { type: String, required: true },
  modelValue: { type: Object, default: () => ({}) },
  keyword: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue', 'update:keyword'])

const loading = ref(true)
const isFallback = ref(false)
const visibleFields = ref([])

const MAX_VISIBLE = 8

const EXCLUDED_FIELDS = new Set([
  'timestamp',
  'log_type',
  'log_id',
  'message',
  'span_id',
  'source_type',
  'service_instance',
  'user_agent'
])

const DISPLAY_PRIORITY = [
  'service_name',
  'log_level',
  'event_type',
  'error_code',
  'status_code',
  'trace_id',
  'user_id',
  'session_id',
  'env',
  'host',
  'action',
  'page',
  'product_id',
  'http_method',
  'request_path',
  'client_ip',
  'status',
  'risk_level',
  'component',
  'resource_type'
]

const FIELD_LABELS = {
  service_name: '服务',
  log_level: '日志级别',
  event_type: '事件类型',
  error_code: '错误码',
  status_code: '状态码',
  trace_id: '链路 ID',
  request_id: '请求 ID',
  user_id: '用户 ID',
  session_id: '会话 ID',
  order_id: '订单 ID',
  env: '环境',
  host: '主机',
  action: '行为',
  page: '页面',
  product_id: '商品 ID',
  product_name: '商品名称',
  http_method: 'HTTP 方法',
  request_path: '请求路径',
  client_ip: '客户端 IP',
  status: '状态',
  tags: '标签',
  risk_level: '风险等级',
  component: '组件',
  resource_type: '资源类型',
  keyword: '关键字',
  operator: '操作人',
  operation: '操作',
  target: '对象'
}

const TERM_OPTIONS = {
  log_level: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
  env: ['dev', 'test', 'staging', 'prod']
}

/** catalog 字段名 → LogQueryRequest 键与控件类型 */
const QUERY_FIELD_MAP = {
  service_name: { key: 'service_names', type: 'terms' },
  log_level: { key: 'log_levels', type: 'terms', options: TERM_OPTIONS.log_level },
  event_type: { key: 'event_types', type: 'terms' },
  error_code: { key: 'error_codes', type: 'terms' },
  status_code: { key: 'status_codes', type: 'range' },
  trace_id: { key: 'trace_id', type: 'keyword' },
  request_id: { key: 'request_id', type: 'keyword' },
  user_id: { key: 'user_id', type: 'keyword' },
  session_id: { key: 'session_id', type: 'keyword' },
  order_id: { key: 'order_id', type: 'keyword' },
  env: { key: 'envs', type: 'terms', options: TERM_OPTIONS.env },
  status: { key: 'statuses', type: 'terms' },
  tags: { key: 'tags', type: 'terms' }
}

function inputId(field) {
  return `filter-${field.key}`
}

function labelFor(fieldName) {
  return FIELD_LABELS[fieldName] || fieldName.replace(/_/g, ' ')
}

function inferType(fieldName, termsSet, metricSet) {
  const mapped = QUERY_FIELD_MAP[fieldName]
  if (mapped?.type) return mapped.type
  if (metricSet.has(fieldName)) return 'range'
  if (termsSet.has(fieldName)) return 'terms'
  return 'keyword'
}

function normalizeDescriptor(raw) {
  const fieldName = raw.field || raw.name || raw.key
  const mapped = QUERY_FIELD_MAP[fieldName]
  const key = raw.key || mapped?.key || fieldName
  const type = raw.type || mapped?.type || 'keyword'
  const options = raw.options || mapped?.options || TERM_OPTIONS[fieldName]

  return {
    field: fieldName,
    key,
    label: raw.label || labelFor(fieldName),
    type,
    options: type === 'terms' ? options : undefined,
    multiple: raw.multiple ?? (type === 'terms' && Boolean(options?.length)),
    placeholder: raw.placeholder
  }
}

function catalogToDescriptors(catalog) {
  const filterFields = catalog?.filter_fields || []
  const termsFields = catalog?.terms_fields || []
  const metricFields = catalog?.metric_fields || []
  const termsSet = new Set(termsFields)
  const metricSet = new Set(metricFields)

  const candidates = filterFields
    .filter((name) => !EXCLUDED_FIELDS.has(name))
    .sort((a, b) => {
      const pa = DISPLAY_PRIORITY.indexOf(a)
      const pb = DISPLAY_PRIORITY.indexOf(b)
      return (pa === -1 ? 999 : pa) - (pb === -1 ? 999 : pb)
    })
    .slice(0, MAX_VISIBLE)

  return candidates.map((fieldName) => {
    const mapped = QUERY_FIELD_MAP[fieldName]
    const type = inferType(fieldName, termsSet, metricSet)
    const options = mapped?.options || TERM_OPTIONS[fieldName]

    return {
      field: fieldName,
      key: mapped?.key || fieldName,
      label: labelFor(fieldName),
      type,
      options: type === 'terms' ? options : undefined,
      multiple: type === 'terms' && Boolean(options?.length)
    }
  })
}

function fallbackToDescriptors(logType) {
  const meta = getLogTypeMeta(logType)
  const list = meta?.fallbackFilters
  if (!Array.isArray(list)) return []
  return list.map(normalizeDescriptor)
}

async function loadFields() {
  loading.value = true
  isFallback.value = false

  try {
    const res = await getLogFields(props.logType)
    const catalog = res?.data?.catalog
    if (!catalog?.filter_fields?.length) {
      throw new Error('empty catalog')
    }
    visibleFields.value = catalogToDescriptors(catalog)
  } catch {
    isFallback.value = true
    visibleFields.value = fallbackToDescriptors(props.logType)
  } finally {
    loading.value = false
  }
}

function patchModel(patch) {
  const next = { ...props.modelValue }
  for (const [key, value] of Object.entries(patch)) {
    if (
      value === '' ||
      value == null ||
      (Array.isArray(value) && value.length === 0) ||
      (typeof value === 'object' && !Array.isArray(value) && !Object.keys(value).length)
    ) {
      delete next[key]
    } else {
      next[key] = value
    }
  }
  emit('update:modelValue', next)
}

function scalarValue(field) {
  const val = props.modelValue[field.key]
  return val == null ? '' : String(val)
}

function termsText(field) {
  const val = props.modelValue[field.key]
  if (!val) return ''
  return Array.isArray(val) ? val.join(', ') : String(val)
}

function rangePart(field, part) {
  const val = props.modelValue[field.key]
  if (!val || typeof val !== 'object') return ''
  const num = val[part]
  return num == null ? '' : num
}

function selectValue(field) {
  const val = props.modelValue[field.key]
  if (!val) return field.multiple ? [] : ''
  if (field.multiple) return Array.isArray(val) ? val : [val]
  return Array.isArray(val) ? val[0] : val
}

function onKeywordFieldInput(field, event) {
  patchModel({ [field.key]: event.target.value })
}

function onTermsInput(field, event) {
  const text = event.target.value.trim()
  if (!text) {
    patchModel({ [field.key]: undefined })
    return
  }
  const parts = text
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
  patchModel({ [field.key]: parts })
}

function onSelectChange(field, event) {
  const el = event.target
  if (field.multiple) {
    const selected = Array.from(el.selectedOptions).map((opt) => opt.value)
    patchModel({ [field.key]: selected })
    return
  }
  const value = el.value
  patchModel({ [field.key]: value ? [value] : undefined })
}

function onRangeInput(field, part, event) {
  const raw = event.target.value
  const current = { ...(props.modelValue[field.key] || {}) }
  if (raw === '') {
    delete current[part]
  } else {
    const num = Number(raw)
    if (!Number.isFinite(num)) return
    current[part] = num
  }
  patchModel({ [field.key]: Object.keys(current).length ? current : undefined })
}

function onKeywordChange(event) {
  emit('update:keyword', event.target.value)
}

function resetFilters() {
  emit('update:modelValue', {})
  emit('update:keyword', '')
}

onMounted(loadFields)
watch(() => props.logType, loadFields)
</script>

<style scoped>
.dynamic-filter-bar {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.fallback-tag {
  display: inline-flex;
  align-self: flex-start;
  margin: 0;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 12px;
}

.filter-skeleton {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--spacing-sm);
}

.skeleton-field {
  height: 56px;
  border-radius: var(--radius-sm);
  background: linear-gradient(
    90deg,
    var(--color-bg) 25%,
    var(--color-border) 50%,
    var(--color-bg) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.2s ease-in-out infinite;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton-field {
    animation: none;
    background: var(--color-bg);
  }
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--spacing-sm);
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.filter-field--keyword {
  grid-column: 1 / -1;
}

@media (min-width: 900px) {
  .filter-field--keyword {
    grid-column: span 2;
  }
}

.filter-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.filter-control {
  width: 100%;
  padding: 7px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-size: 13px;
  color: var(--color-text);
  transition: border-color 0.15s ease-out, box-shadow 0.15s ease-out;
  box-sizing: border-box;
}

.filter-control:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.filter-control:hover {
  border-color: #cbd5e1;
}

.range-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.range-input {
  flex: 1;
  min-width: 0;
}

.range-sep {
  color: var(--color-text-muted);
  font-size: 12px;
}

.filter-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 2px;
}

.btn-reset {
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: border-color 0.15s ease-out, color 0.15s ease-out, box-shadow 0.15s ease-out;
}

.btn-reset:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

@media (prefers-reduced-motion: reduce) {
  .filter-control,
  .btn-reset {
    transition: none;
  }
}
</style>
