<template>
  <div class="dynamic-filter-bar">
    <div v-if="isFallback" class="fallback-banner" role="status">
      <strong>字段目录兜底</strong>
      <span>未能加载后端字段目录，已使用本地契约筛选项；仅展示后端支持的精确筛选字段。</span>
    </div>

    <div v-if="loading" class="filter-skeleton" aria-busy="true" aria-label="加载筛选字段">
      <div v-for="n in 4" :key="n" class="skeleton-field" />
    </div>

    <template v-else>
      <div class="filter-toolbar">
        <span class="filter-toolbar__title">筛选</span>
        <button
          v-if="advancedFields.length"
          type="button"
          class="filter-toolbar__toggle"
          @click="showAdvanced = !showAdvanced"
        >
          {{ showAdvanced ? '收起高级筛选' : '展开高级筛选' }}
          <span v-if="advancedActiveCount" class="filter-toolbar__badge">{{ advancedActiveCount }}</span>
        </button>
      </div>

      <div class="filter-grid filter-grid--common">
        <FilterFieldControl
          v-for="field in commonFields"
          :key="field.key"
          :field="field"
          :model-value="modelValue"
          @patch="patchModel"
        />

        <div class="filter-field filter-field--keyword">
          <label class="filter-label" for="filter-keyword">关键字</label>
          <input
            id="filter-keyword"
            class="filter-control"
            type="search"
            :value="keyword"
            placeholder="模糊搜索 message、request_path、trace_id 等"
            @input="onKeywordChange"
          />
          <p class="filter-hint">不支持精确筛选的字段（如 action、URI、IP）请在此搜索</p>
        </div>
      </div>

      <div v-show="showAdvanced && advancedFields.length" class="filter-grid filter-grid--advanced">
        <FilterFieldControl
          v-for="field in advancedFields"
          :key="field.key"
          :field="field"
          :model-value="modelValue"
          @patch="patchModel"
        />
      </div>

      <div class="filter-actions">
        <button type="button" class="btn-reset" @click="resetFilters">重置全部</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, defineComponent, h } from 'vue'
import { getLogFields } from '../../api/logs.js'
import { getLogTypeMeta } from '../../utils/logTypeMeta.js'
import {
  buildFilterDescriptorsFromCatalog,
  buildFilterDescriptorsFromFallback
} from '../../utils/logQueryContract.js'

const props = defineProps({
  logType: { type: String, required: true },
  modelValue: { type: Object, default: () => ({}) },
  keyword: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue', 'update:keyword', 'catalog-fallback'])

const loading = ref(true)
const isFallback = ref(false)
const showAdvanced = ref(false)
const commonFields = ref([])
const advancedFields = ref([])

const advancedActiveCount = computed(() =>
  advancedFields.value.filter((field) => hasValue(props.modelValue[field.key])).length
)

function hasValue(val) {
  return !(
    val == null ||
    val === '' ||
    (Array.isArray(val) && val.length === 0) ||
    (typeof val === 'object' && !Array.isArray(val) && !Object.keys(val).length)
  )
}

const FilterFieldControl = defineComponent({
  name: 'FilterFieldControl',
  props: {
    field: { type: Object, required: true },
    modelValue: { type: Object, default: () => ({}) }
  },
  emits: ['patch'],
  setup(fieldProps, { emit: fieldEmit }) {
    return () => {
      const field = fieldProps.field
      const id = `filter-${field.key}`
      const val = fieldProps.modelValue[field.key]

      if (field.type === 'terms' && field.options?.length) {
        return h('div', { class: 'filter-field' }, [
          h('label', { class: 'filter-label', for: id }, field.label),
          h(
            'select',
            {
              id,
              class: 'filter-control',
              multiple: field.multiple,
              value: selectValue(field, val),
              onChange: (e) => onSelectChange(field, e, fieldEmit)
            },
            [
              !field.multiple ? h('option', { value: '' }, '全部') : null,
              ...field.options.map((opt) => h('option', { key: opt, value: opt }, opt))
            ]
          )
        ])
      }

      if (field.type === 'terms') {
        const text = !val ? '' : Array.isArray(val) ? val.join(', ') : String(val)
        return h('div', { class: 'filter-field' }, [
          h('label', { class: 'filter-label', for: id }, field.label),
          h('input', {
            id,
            class: 'filter-control',
            type: 'text',
            value: text,
            placeholder: field.numeric ? '如 400,500' : '多个值用逗号分隔',
            onInput: (e) => onTermsInput(field, e, fieldEmit)
          })
        ])
      }

      return h('div', { class: 'filter-field' }, [
        h('label', { class: 'filter-label', for: id }, field.label),
        h('input', {
          id,
          class: 'filter-control',
          type: 'text',
          value: val == null ? '' : String(val),
          placeholder: field.placeholder || '精确匹配',
          onInput: (e) => fieldEmit('patch', { [field.key]: e.target.value })
        })
      ])
    }
  }
})

function selectValue(field, val) {
  if (!val) return field.multiple ? [] : ''
  if (field.multiple) return Array.isArray(val) ? val : [val]
  return Array.isArray(val) ? val[0] : val
}

function onTermsInput(field, event, fieldEmit) {
  const text = event.target.value.trim()
  if (!text) {
    fieldEmit('patch', { [field.key]: undefined })
    return
  }
  const parts = text
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
  if (field.numeric) {
    const nums = parts.map((p) => Number(p)).filter((n) => Number.isFinite(n))
    fieldEmit('patch', { [field.key]: nums.length ? nums : undefined })
    return
  }
  fieldEmit('patch', { [field.key]: parts })
}

function onSelectChange(field, event, fieldEmit) {
  const el = event.target
  if (field.multiple) {
    const selected = Array.from(el.selectedOptions).map((opt) => opt.value)
    fieldEmit('patch', { [field.key]: selected.length ? selected : undefined })
    return
  }
  fieldEmit('patch', { [field.key]: el.value ? [el.value] : undefined })
}

async function loadFields() {
  loading.value = true
  isFallback.value = false

  try {
    const res = await getLogFields(props.logType)
    const catalog = res?.data?.catalog
    if (!catalog?.filter_fields?.length) throw new Error('empty catalog')
    const groups = buildFilterDescriptorsFromCatalog(catalog)
    commonFields.value = groups.common
    advancedFields.value = groups.advanced
  } catch {
    isFallback.value = true
    const meta = getLogTypeMeta(props.logType)
    const groups = buildFilterDescriptorsFromFallback(meta.fallbackFilters)
    commonFields.value = groups.common
    advancedFields.value = groups.advanced
  } finally {
    loading.value = false
    emit('catalog-fallback', isFallback.value)
  }
}

function patchModel(patch) {
  const next = { ...props.modelValue }
  for (const [key, value] of Object.entries(patch)) {
    if (!hasValue(value)) {
      delete next[key]
    } else {
      next[key] = value
    }
  }
  emit('update:modelValue', next)
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
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.fallback-banner {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 12px;
  line-height: 1.45;
}

.fallback-banner strong {
  font-size: 13px;
}

.filter-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
}

.filter-toolbar__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
}

.filter-toolbar__toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text-secondary);
  font-size: 12px;
  cursor: pointer;
}

.filter-toolbar__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--color-primary);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
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

.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--spacing-sm);
}

.filter-grid--advanced {
  padding-top: var(--spacing-sm);
  border-top: 1px dashed var(--color-border);
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
  box-sizing: border-box;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.filter-control:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.filter-hint {
  margin: 0;
  font-size: 11px;
  color: var(--color-text-muted);
  line-height: 1.4;
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
  transition: border-color var(--transition-fast), color var(--transition-fast);
}

.btn-reset:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

@media (prefers-reduced-motion: reduce) {
  .skeleton-field {
    animation: none;
    background: var(--color-bg);
  }
}
</style>
