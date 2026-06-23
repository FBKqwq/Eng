<template>
  <div class="config-page">
    <EmptyState
      v-if="statusError && !statusLoading"
      title="无法加载配置快照"
      :description="statusError"
      icon="!"
    >
      <button type="button" class="retry-btn" @click="loadStatus">重试</button>
    </EmptyState>

    <ConfigSnapshotCard
      v-else
      :groups="configGroups"
      :kibana-url="kibanaUrl"
      :discover-url="discoverUrl"
    />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import ConfigSnapshotCard from '../../components/system/ConfigSnapshotCard.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import { getSystemStatus } from '../../api/system.js'
import { getKibanaBaseUrl, buildDiscoverLink } from '../../utils/kibanaLinks.js'
import { useTimeRange } from '../../composables/useTimeRange.js'

const { range } = useTimeRange()

const UNCONFIGURED = '未配置'

const systemStatus = ref(null)
const statusLoading = ref(false)
const statusError = ref('')

const kibanaUrl = computed(() => getKibanaBaseUrl() || '')

const discoverUrl = computed(() => {
  const index =
    systemStatus.value?.elasticsearch?.index_pattern ||
    import.meta.env.VITE_KIBANA_DEFAULT_INDEX_PATTERN ||
    ''
  return buildDiscoverLink({
    index: String(index).trim(),
    timeRange: range.value
  })
})

/**
 * 从 status 响应提取首个有效标量或数组拼接值；均无则返回「未配置」。
 * @param {...unknown} candidates
 */
function resolveConfigValue(...candidates) {
  for (const candidate of candidates) {
    if (candidate === null || candidate === undefined || candidate === '') continue
    if (Array.isArray(candidate)) {
      const text = candidate.map((entry) => String(entry)).filter(Boolean).join(', ')
      if (text) return text
      continue
    }
    return String(candidate)
  }
  return UNCONFIGURED
}

/**
 * 将 getSystemStatus 解包后的 res.data 映射为 ConfigSnapshotCard groups。
 * @param {object|null|undefined} status
 */
function mapStatusToConfigGroups(status) {
  if (!status || typeof status !== 'object') return []

  const kafka = status.kafka || {}
  const elasticsearch = status.elasticsearch || {}
  const llm = status.llm || {}

  return [
    {
      title: 'Kafka',
      items: [
        {
          key: 'bootstrap_servers',
          value: resolveConfigValue(kafka.bootstrap_servers, status.kafka_bootstrap_servers)
        },
        {
          key: 'topic',
          value: resolveConfigValue(kafka.topic, kafka.configured_topic?.name, status.kafka_topic)
        }
      ]
    },
    {
      title: 'Elasticsearch',
      items: [
        {
          key: 'hosts',
          value: resolveConfigValue(elasticsearch.hosts, status.elasticsearch_hosts)
        },
        {
          key: 'index_pattern',
          value: resolveConfigValue(elasticsearch.index_pattern, status.elasticsearch_index_pattern)
        }
      ]
    },
    {
      title: 'LLM',
      items: [
        {
          key: 'provider',
          value: resolveConfigValue(llm.provider, status.llm_provider)
        },
        {
          key: 'model',
          value: resolveConfigValue(llm.model, llm.default_model, status.llm_default_model, status.llm_analysis_model)
        },
        {
          key: 'api_key',
          value: resolveConfigValue(llm.api_key, status.llm_api_key),
          sensitive: true
        }
      ]
    }
  ]
}

const configGroups = computed(() =>
  systemStatus.value ? mapStatusToConfigGroups(systemStatus.value) : []
)

async function loadStatus() {
  statusLoading.value = true
  statusError.value = ''

  try {
    const res = await getSystemStatus()
    systemStatus.value = res.data || {}
  } catch (err) {
    systemStatus.value = null
    statusError.value =
      err?.message || '系统状态接口失败，请确认后端 /system/status 是否可用。'
  } finally {
    statusLoading.value = false
  }
}

loadStatus()
</script>

<style scoped>
.config-page {
  min-height: 200px;
}

.retry-btn {
  margin-top: 8px;
  padding: 6px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.retry-btn:hover {
  border-color: var(--color-primary);
  background: var(--color-bg);
}

@media (prefers-reduced-motion: reduce) {
  .retry-btn {
    transition: none;
  }
}
</style>
