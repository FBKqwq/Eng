<template>
  <div class="filter-field" :class="{ 'filter-field--active': isActive }">
    <label class="filter-label" :for="inputId">{{ field.label }}</label>

    <!-- 枚举：单行下拉 -->
    <select
      v-if="field.type === 'terms' && field.options?.length"
      :id="inputId"
      class="filter-control filter-control--select"
      :value="selectValue"
      @change="onSelectChange"
    >
      <option value="">全部</option>
      <option v-for="opt in field.options" :key="opt" :value="opt">{{ opt }}</option>
    </select>

    <!-- 自由 terms：逗号分隔 -->
    <input
      v-else-if="field.type === 'terms'"
      :id="inputId"
      class="filter-control"
      type="text"
      :value="termsText"
      :placeholder="field.numeric ? '如 400,500' : '多个值用逗号分隔'"
      @input="onTermsInput"
    />

    <!-- 单值精确匹配 -->
    <input
      v-else
      :id="inputId"
      class="filter-control"
      type="text"
      :value="scalarValue"
      :placeholder="field.placeholder || '精确匹配'"
      @input="onScalarInput"
    />

    <button
      v-if="isActive"
      type="button"
      class="filter-field__clear"
      :aria-label="`清除 ${field.label}`"
      @click="clearField"
    >
      清除
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  field: { type: Object, required: true },
  modelValue: { type: Object, default: () => ({}) }
})

const emit = defineEmits(['patch'])

const inputId = computed(() => `filter-${props.field.key}`)

const rawValue = computed(() => props.modelValue[props.field.key])

const isActive = computed(() => {
  const val = rawValue.value
  if (val == null || val === '') return false
  if (Array.isArray(val)) return val.length > 0
  return true
})

const selectValue = computed(() => {
  const val = rawValue.value
  if (!val) return ''
  if (Array.isArray(val)) return val[0] ?? ''
  return String(val)
})

const termsText = computed(() => {
  const val = rawValue.value
  if (!val) return ''
  return Array.isArray(val) ? val.join(', ') : String(val)
})

const scalarValue = computed(() => {
  const val = rawValue.value
  return val == null ? '' : String(val)
})

function onSelectChange(event) {
  const value = event.target.value
  emit('patch', { [props.field.key]: value ? [value] : undefined })
}

function onTermsInput(event) {
  const text = event.target.value.trim()
  if (!text) {
    emit('patch', { [props.field.key]: undefined })
    return
  }
  const parts = text
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)

  if (props.field.numeric) {
    const nums = parts.map((p) => Number(p)).filter((n) => Number.isFinite(n))
    emit('patch', { [props.field.key]: nums.length ? nums : undefined })
    return
  }
  emit('patch', { [props.field.key]: parts })
}

function onScalarInput(event) {
  const value = event.target.value
  emit('patch', { [props.field.key]: value || undefined })
}

function clearField() {
  emit('patch', { [props.field.key]: undefined })
}
</script>

<style scoped>
.filter-field {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.filter-field--active .filter-control {
  border-color: rgba(37, 99, 235, 0.45);
  background: var(--color-primary-soft);
}

.filter-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.filter-control {
  width: 100%;
  height: 36px;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: 0;
  background: var(--color-surface);
  font-size: 13px;
  color: var(--color-text);
  box-sizing: border-box;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast), background var(--transition-fast);
}

.filter-control--select {
  padding-right: 28px;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2394a3b8' d='M3 4.5 6 7.5 9 4.5'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
}

.filter-control:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
  background-color: var(--color-surface);
}

.filter-field__clear {
  align-self: flex-start;
  margin-top: 2px;
  padding: 0;
  border: none;
  background: none;
  color: var(--color-primary);
  font-size: 11px;
  cursor: pointer;
  line-height: 1.2;
}

.filter-field__clear:hover {
  text-decoration: underline;
}
</style>
