<template>
  <section class="system-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">System Console</p>
        <h1>系统状态</h1>
        <p class="summary">集中查看后端 API、Kafka 与 ELK 相关服务的健康状态和配置快照。</p>
      </div>
      <button :disabled="loading" @click="loadStatus">
        {{ loading ? '刷新中...' : '刷新状态' }}
      </button>
    </header>

    <div v-if="errorMessage" class="alert">
      {{ errorMessage }}
    </div>

    <div class="overview">
      <div>
        <span class="metric-value">{{ runningCount }}</span>
        <span class="metric-label">正常服务</span>
      </div>
      <div>
        <span class="metric-value">{{ attentionCount }}</span>
        <span class="metric-label">需关注服务</span>
      </div>
      <div>
        <span class="metric-value">{{ lastUpdatedText }}</span>
        <span class="metric-label">最近刷新</span>
      </div>
    </div>

    <div class="service-grid">
      <ServiceStatusCard v-for="service in services" :key="service.key" :service="service" />
    </div>

    <section class="infra-grid">
      <article class="detail-panel">
        <div class="panel-heading">
          <div>
            <p class="panel-kicker">Elasticsearch</p>
            <h2>集群健康状态</h2>
          </div>
          <span class="health-badge" :class="`status-${esHealthMeta.tone}`">{{ esHealthMeta.label }}</span>
        </div>
        <p class="panel-note">{{ esHealthMeta.description }}</p>

        <dl class="detail-list">
          <div>
            <dt>可访问</dt>
            <dd>{{ formatBoolean(elasticsearchStatus.available) }}</dd>
          </div>
          <div>
            <dt>Endpoint</dt>
            <dd>{{ formatValue(elasticsearchStatus.endpoint || systemStatus.elasticsearch_hosts) }}</dd>
          </div>
          <div>
            <dt>Container</dt>
            <dd>{{ formatValue(elasticsearchStatus.name) }}</dd>
          </div>
          <div>
            <dt>Image</dt>
            <dd>{{ formatValue(elasticsearchStatus.image) }}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>{{ formatValue(elasticsearchStatus.raw_status || elasticsearchStatus.status) }}</dd>
          </div>
          <div>
            <dt>CPU</dt>
            <dd>{{ formatValue(elasticsearchStatus.cpu_percent) }}</dd>
          </div>
          <div>
            <dt>Memory</dt>
            <dd>{{ formatValue(elasticsearchStatus.memory_usage) }}</dd>
          </div>
          <div>
            <dt>PIDs</dt>
            <dd>{{ formatValue(elasticsearchStatus.pids) }}</dd>
          </div>
          <div>
            <dt>Index Pattern</dt>
            <dd>{{ formatValue(systemStatus.elasticsearch_index_pattern) }}</dd>
          </div>
          <div>
            <dt>Ports</dt>
            <dd>{{ formatValue(elasticsearchStatus.ports) }}</dd>
          </div>
        </dl>

        <div v-if="elasticsearchStatus.error" class="inline-error">
          {{ elasticsearchStatus.error }}
        </div>
      </article>

      <article class="detail-panel">
        <div class="panel-heading">
          <div>
            <p class="panel-kicker">Kafka</p>
            <h2>Broker 与 Topic 快照</h2>
          </div>
          <span class="health-badge" :class="`status-${kafkaMeta.tone}`">{{ kafkaMeta.label }}</span>
        </div>
        <p class="panel-note">展示后端返回的 Kafka 配置与容器快照；若接口提供 AdminClient 详情，则优先展示 broker 与 topic 状态。</p>

        <dl class="detail-list">
          <div>
            <dt>可访问</dt>
            <dd>{{ formatBoolean(kafkaStatus.available) }}</dd>
          </div>
          <div>
            <dt>Bootstrap Servers</dt>
            <dd>{{ kafkaBootstrapServers }}</dd>
          </div>
          <div>
            <dt>Configured Topic</dt>
            <dd>{{ formatValue(kafkaStatus.topic || systemStatus.kafka_topic) }}</dd>
          </div>
          <div>
            <dt>Container</dt>
            <dd>{{ formatValue(kafkaStatus.name) }}</dd>
          </div>
          <div>
            <dt>Image</dt>
            <dd>{{ formatValue(kafkaStatus.image) }}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>{{ formatValue(kafkaStatus.raw_status || kafkaStatus.status) }}</dd>
          </div>
          <div>
            <dt>CPU</dt>
            <dd>{{ formatValue(kafkaStatus.cpu_percent) }}</dd>
          </div>
          <div>
            <dt>Memory</dt>
            <dd>{{ formatValue(kafkaStatus.memory_usage) }}</dd>
          </div>
          <div>
            <dt>Ports</dt>
            <dd>{{ formatValue(kafkaStatus.ports) }}</dd>
          </div>
        </dl>

        <div v-if="kafkaStatus.error" class="inline-error">
          {{ kafkaStatus.error }}
        </div>
      </article>
    </section>

    <section class="config-panel">
      <div>
        <h2>配置快照</h2>
        <p>来自后端系统状态接口，保留基础配置字段，便于排查当前环境指向。</p>
      </div>
      <dl>
        <div>
          <dt>Kafka Bootstrap Servers</dt>
          <dd>{{ formatValue(systemStatus.kafka_bootstrap_servers) }}</dd>
        </div>
        <div>
          <dt>Kafka Topic</dt>
          <dd>{{ formatValue(systemStatus.kafka_topic) }}</dd>
        </div>
        <div>
          <dt>Elasticsearch Hosts</dt>
          <dd>{{ formatValue(systemStatus.elasticsearch_hosts) }}</dd>
        </div>
        <div>
          <dt>Elasticsearch Index Pattern</dt>
          <dd>{{ formatValue(systemStatus.elasticsearch_index_pattern) }}</dd>
        </div>
      </dl>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getApiHealth, getSystemStatus } from '../../api/system'
import ServiceStatusCard from '../../components/system/ServiceStatusCard.vue'
import {
  buildDeveloperServices,
  formatBoolean,
  formatValue,
  getClusterHealthMeta,
  getStatusMeta
} from '../../utils/systemStatus'

const loading = ref(false)
const errorMessage = ref('')
const apiHealth = ref(null)
const systemStatus = ref({})
const lastUpdatedAt = ref(null)

const getContainerStatus = (key) =>
  systemStatus.value.containers?.[key] ||
  systemStatus.value.services?.[key] ||
  systemStatus.value.docker?.containers?.[key] ||
  {}

const isAvailable = (status) => ['running', 'ok', 'up', 'healthy'].includes(String(status || '').toLowerCase())

const services = computed(() =>
  buildDeveloperServices({
    apiHealth: apiHealth.value,
    systemStatus: systemStatus.value,
    frontendReady: true
  })
)

const elasticsearchStatus = computed(() => {
  const container = getContainerStatus('elasticsearch')
  const elasticsearch = systemStatus.value.elasticsearch || {}
  const hasClusterHealth = ['green', 'yellow', 'red'].includes(String(elasticsearch.cluster_status || '').toLowerCase())

  return {
    ...container,
    ...elasticsearch,
    available: elasticsearch.available || isAvailable(container.status),
    cluster_status: hasClusterHealth ? elasticsearch.cluster_status : container.status,
    cluster_error: elasticsearch.error
  }
})

const kafkaStatus = computed(() => {
  const container = getContainerStatus('kafka')
  const kafka = systemStatus.value.kafka || {}

  return {
    ...container,
    ...kafka,
    available: kafka.available ?? isAvailable(container.status),
    bootstrap_servers: kafka.bootstrap_servers || systemStatus.value.kafka_bootstrap_servers,
    topic: kafka.topic || systemStatus.value.kafka_topic
  }
})

const esHealthMeta = computed(() => getClusterHealthMeta(elasticsearchStatus.value.cluster_status))
const kafkaMeta = computed(() => getStatusMeta(kafkaStatus.value.available ? 'running' : kafkaStatus.value.status))
const kafkaBootstrapServers = computed(() => {
  const servers = kafkaStatus.value.bootstrap_servers
  return Array.isArray(servers) && servers.length ? servers.join(', ') : formatValue(servers)
})

const runningCount = computed(() => services.value.filter((service) => service.status === 'running').length)
const attentionCount = computed(() =>
  services.value.filter((service) => ['down', 'pending', 'unknown'].includes(service.status)).length
)
const lastUpdatedText = computed(() => {
  if (!lastUpdatedAt.value) {
    return '-'
  }

  return lastUpdatedAt.value.toLocaleTimeString()
})

const loadStatus = async () => {
  loading.value = true
  errorMessage.value = ''

  const [healthResult, systemResult] = await Promise.allSettled([getApiHealth(), getSystemStatus()])
  const systemStatusOk = systemResult.status === 'fulfilled'

  if (healthResult.status === 'fulfilled') {
    apiHealth.value = healthResult.value.data || { status: 'ok' }
  } else if (systemStatusOk) {
    apiHealth.value = { status: 'ok' }
  } else {
    apiHealth.value = { status: 'down' }
  }

  if (systemStatusOk) {
    systemStatus.value = {
      ...(systemResult.value.data || {}),
      backend_api_status: 'ok'
    }
  } else {
    systemStatus.value = {}
    errorMessage.value = systemResult.reason?.message || '系统状态接口失败，请确认后端 /system/status 是否可用。'
  }

  lastUpdatedAt.value = new Date()
  loading.value = false
}

onMounted(loadStatus)
</script>

<style scoped>
.system-page {
  display: grid;
  gap: 22px;
}

.page-header {
  align-items: center;
  display: flex;
  gap: 24px;
  justify-content: space-between;
}

.eyebrow,
.panel-kicker {
  color: #2563eb;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0;
  margin: 0 0 8px;
}

h1 {
  color: #111827;
  font-size: 30px;
  margin: 0;
}

.summary {
  color: #4b5563;
  line-height: 1.6;
  margin: 10px 0 0;
}

button {
  background: #2563eb;
  border: 0;
  border-radius: 6px;
  color: #ffffff;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  min-width: 104px;
  padding: 10px 16px;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.alert,
.inline-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #991b1b;
  line-height: 1.5;
  padding: 12px 14px;
}

.overview {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.overview > div,
.detail-panel,
.config-panel {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.overview > div {
  padding: 16px;
}

.metric-value {
  color: #111827;
  display: block;
  font-size: 24px;
  font-weight: 800;
  min-height: 30px;
}

.metric-label {
  color: #6b7280;
  display: block;
  font-size: 13px;
  margin-top: 6px;
}

.service-grid,
.infra-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

.detail-panel,
.config-panel {
  display: grid;
  gap: 16px;
  padding: 20px;
}

.panel-heading {
  align-items: flex-start;
  display: flex;
  gap: 16px;
  justify-content: space-between;
}

h2 {
  color: #111827;
  font-size: 20px;
  margin: 0;
}

.panel-note,
.config-panel p {
  color: #6b7280;
  line-height: 1.6;
  margin: 0;
}

.health-badge {
  border-radius: 999px;
  font-size: 13px;
  font-weight: 800;
  padding: 6px 11px;
  white-space: nowrap;
}

.status-success {
  background: #dcfce7;
  color: #166534;
}

.status-danger {
  background: #fee2e2;
  color: #991b1b;
}

.status-warning {
  background: #fef3c7;
  color: #92400e;
}

.status-neutral {
  background: #f3f4f6;
  color: #4b5563;
}

.detail-list,
.config-panel dl {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 0;
}

.config-panel dl {
  margin-top: 2px;
}

dt {
  color: #6b7280;
  font-size: 12px;
  margin-bottom: 5px;
}

dd {
  color: #1f2937;
  margin: 0;
  overflow-wrap: anywhere;
}

@media (max-width: 760px) {
  .page-header,
  .panel-heading {
    align-items: stretch;
    flex-direction: column;
  }

  .overview,
  .detail-list,
  .config-panel dl {
    grid-template-columns: 1fr;
  }
}
</style>
