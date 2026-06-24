<template>
  <div class="dynamic-filter-bar">
    <div v-if="isFallback" class="fallback-banner" role="status">
      <strong>字段目录兜底</strong>
      <span>未能加载后端字段目录，已使用本地契约筛选项；仅展示后端支持的精确筛选字段。</span>
    </div>

    <div v-if="loading" class="filter-skeleton" aria-busy="true" aria-label="加载筛选字段">
      <div v-for="n in 5" :key="n" class="skeleton-field" />
    </div>

    <template v-else>
      <header class="filter-toolbar">
        <span class="filter-toolbar__title">筛选</span>
        <div class="filter-toolbar__actions">
          <button
            v-if="advancedFields.length"
            type="button"
            class="filter-toolbar__toggle"
            :aria-expanded="showAdvanced"
            @click="showAdvanced = !showAdvanced"
          >
            {{ showAdvanced ? '收起高级筛选' : '展开高级筛选' }}
            <span v-if="advancedActiveCount" class="filter-toolbar__badge">{{ advancedActiveCount }}</span>
          </button>
          <button type="button" class="btn-reset" @click="resetFilters">重置全部</button>
        </div>
      </header>

      <section class="filter-section" aria-label="常用筛选">
        <p class="filter-section__label">常用筛选</p>
        <div class="filter-grid filter-grid--5">
          <FilterFieldControl
            v-for="field in commonFields"
            :key="field.key"
            :field="field"
            :model-value="modelValue"
            @patch="patchModel"
          />
        </div>

        <div class="filter-keyword-row">
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
      </section>

      <section
        v-if="advancedFields.length && showAdvanced"
        class="filter-section filter-section--advanced"
        aria-label="高级筛选"
      >
        <p class="filter-section__label">高级筛选</p>
        <div class="filter-grid filter-grid--4">
          <FilterFieldControl
            v-for="field in advancedFields"
            :key="field.key"
            :field="field"
            :model-value="modelValue"
            @patch="patchModel"
          />
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { getLogFields } from '../../api/logs.js'
import { getLogTypeMeta } from '../../utils/logTypeMeta.js'
import {
  buildFilterDescriptorsFromCatalog,
  buildFilterDescriptorsFromFallback
} from '../../utils/logQueryContract.js'
import FilterFieldControl from './FilterFieldControl.vue'

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
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border: 1px solid #111827;
  border-radius: 0;
  background: var(--color-surface);
  box-shadow: 6px 6px 0 rgba(15, 23, 42, 0.06);
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
  flex-wrap: wrap;
}

.filter-toolbar__title {
  position: relative;
  padding-left: 14px;
  font-size: 14px;
  font-weight: 900;
  letter-spacing: 0.08em;
  color: var(--color-text);
}

.filter-toolbar__title::before {
  position: absolute;
  inset: 1px auto 1px 0;
  width: 7px;
  background: #111827;
  transform: skewX(-18deg);
  content: '';
}

.filter-toolbar__actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-toolbar__toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: 0;
  background: var(--color-bg);
  color: var(--color-text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: border-color var(--transition-fast), color var(--transition-fast);
}

.filter-toolbar__toggle:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
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

.filter-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.filter-section--advanced {
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--color-border);
}

.filter-section__label {
  margin: 0;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.filter-grid {
  display: grid;
  gap: 10px 12px;
  align-items: start;
}

.filter-grid--5 {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.filter-grid--4 {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.filter-keyword-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 4px;
  border-top: 1px dashed var(--color-border);
}

.filter-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  line-height: 1.2;
}

.filter-hint {
  margin: 0;
  font-size: 11px;
  color: var(--color-text-muted);
  line-height: 1.4;
}

.btn-reset {
  height: 32px;
  padding: 0 14px;
  border: 1px solid var(--color-border);
  border-radius: 0;
  background: var(--color-bg);
  color: var(--color-text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: border-color var(--transition-fast), color var(--transition-fast);
}

.btn-reset:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.filter-skeleton {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.skeleton-field {
  height: 52px;
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

@media (max-width: 1100px) {
  .filter-grid--5 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .filter-grid--4 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .filter-skeleton {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .filter-grid--5,
  .filter-grid--4,
  .filter-skeleton {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton-field {
    animation: none;
    background: var(--color-bg);
  }
}
</style>
