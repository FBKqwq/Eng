<template>
  <div class="trace-search">
    <form class="search-row" @submit.prevent="handleSearch">
      <input
        v-model="inputValue"
        class="trace-input"
        type="text"
        placeholder="输入 trace_id（支持从监控/诊断页带参跳入）"
        :disabled="loading"
        spellcheck="false"
        autocomplete="off"
      />
      <button type="submit" class="search-btn" :disabled="loading || !inputValue.trim()">
        {{ loading ? '检索中…' : '检索' }}
      </button>
    </form>
    <div v-if="recentIds.length" class="history-row">
      <span class="history-label">最近查询：</span>
      <button
        v-for="id in recentIds"
        :key="id"
        type="button"
        class="history-tag"
        :disabled="loading"
        :title="`复用 ${id}`"
        @click="selectHistory(id)"
      >
        {{ id }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const STORAGE_KEY = 'elk.trace.recent_ids'
const MAX_HISTORY = 10

const props = defineProps({
  /** 路由 query 预填 trace_id */
  traceId: { type: String, default: '' },
  loading: { type: Boolean, default: false }
})

const emit = defineEmits(['search'])

const inputValue = ref('')
const recentIds = ref(loadHistory())

watch(
  () => props.traceId,
  (value) => {
    if (value != null && value !== '') {
      inputValue.value = String(value)
    }
  },
  { immediate: true }
)

function loadHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.map((item) => String(item).trim()).filter(Boolean).slice(0, MAX_HISTORY)
  } catch {
    return []
  }
}

function saveHistory(ids) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(ids))
  } catch {
    /* 隐私模式等场景忽略 */
  }
}

function pushHistory(traceId) {
  const trimmed = String(traceId).trim()
  if (!trimmed) return
  const next = [trimmed, ...recentIds.value.filter((item) => item !== trimmed)].slice(0, MAX_HISTORY)
  recentIds.value = next
  saveHistory(next)
}

function handleSearch() {
  const trimmed = inputValue.value.trim()
  if (!trimmed || props.loading) return
  pushHistory(trimmed)
  emit('search', trimmed)
}

function selectHistory(id) {
  if (props.loading) return
  inputValue.value = id
  pushHistory(id)
  emit('search', id)
}
</script>

<style scoped>
.search-row {
  display: flex;
  gap: 8px;
}

.trace-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font-size: 13px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  color: var(--color-text);
  transition: border-color 150ms ease, box-shadow 150ms ease;
}

.trace-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.trace-input:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.search-btn {
  padding: 8px 20px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 150ms ease, transform 150ms ease;
}

.search-btn:hover:not(:disabled) {
  opacity: 0.92;
}

.search-btn:active:not(:disabled) {
  transform: translateY(1px);
}

.search-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.history-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: var(--spacing-sm);
}

.history-label {
  font-size: 12px;
  color: var(--color-text-muted);
}

.history-tag {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  font-size: 11px;
  color: var(--color-text-secondary);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  cursor: pointer;
  transition: border-color 150ms ease, background 150ms ease;
}

.history-tag:hover:not(:disabled) {
  border-color: var(--color-primary);
  background: var(--color-info-bg);
  color: var(--color-text);
}

.history-tag:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (prefers-reduced-motion: reduce) {
  .trace-input,
  .search-btn,
  .history-tag {
    transition: none;
  }
}
</style>
