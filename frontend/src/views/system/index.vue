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
      <div class="config-header">
        <div>
          <p class="panel-kicker">Pipeline Check</p>
          <h2>全链路验证</h2>
          <p>基于后端验证任务，检查多线程日志生产到 Elasticsearch 检索的完整传输链路。</p>
        </div>
        <button class="verify-button" :disabled="pipelineLoading" @click="runPipelineCheck">
          {{ pipelineLoading ? '检测中...' : '快速检测' }}
        </button>
      </div>

      <div class="pipeline-flow" aria-label="全链路验证节点">
        <div
          v-for="(node, index) in pipelineNodes"
          :key="node.key"
          class="pipeline-step"
          :class="`node-${node.status}`"
        >
          <div class="node-icon" :title="nodeStatusLabel(node.status)">
            {{ nodeIcon(node.status, index) }}
          </div>
          <div class="node-copy">
            <strong>{{ node.label }}</strong>
            <span>{{ node.detail }}</span>
          </div>
        </div>
      </div>

      <div v-if="pipelineError" class="inline-error">
        {{ pipelineError }}
      </div>

      <div class="terminal-panel">
        <div class="terminal-heading">
          <strong>验证输出</strong>
          <span>{{ pipelineSummary }}</span>
        </div>
        <pre>{{ pipelineOutput }}</pre>
      </div>

      <dl class="config-snapshot">
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
import { getApiHealth, getSystemStatus, verifyPipeline } from '../../api/system'
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
const pipelineLoading = ref(false)
const pipelineError = ref('')
const pipelineResult = ref(null)

const DEFAULT_PIPELINE_NODES = [
  { key: 'producer', label: '日志生产', status: 'pending', detail: '等待检测' },
  { key: 'kafka', label: 'Kafka 接收', status: 'pending', detail: '等待检测' },
  { key: 'logstash', label: 'Logstash 处理', status: 'pending', detail: '等待检测' },
  { key: 'elasticsearch', label: 'Elasticsearch 检索', status: 'pending', detail: '等待检测' }
]

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

const pipelineNodes = computed(() => pipelineResult.value?.nodes?.length ? pipelineResult.value.nodes : DEFAULT_PIPELINE_NODES)
const pipelineSummary = computed(() => {
  if (pipelineLoading.value) {
    return '正在执行多线程 verify_log_pipeline_full'
  }

  if (!pipelineResult.value) {
    return '尚未执行'
  }

  const status = pipelineResult.value.success ? '通过' : '失败'
  return `${status} / exit=${pipelineResult.value.exit_code} / ${pipelineResult.value.duration_ms}ms`
})
const pipelineOutput = computed(() => {
  if (pipelineLoading.value && !pipelineResult.value) {
    return '正在启动全链路验证，请稍候...'
  }

  if (!pipelineResult.value) {
    return '点击“快速检测”后，这里会展示多线程 verify_log_pipeline_full 的终端输出。'
  }

  const stdout = pipelineResult.value.stdout || ''
  const stderr = pipelineResult.value.stderr || ''
  return [stdout.trim(), stderr.trim()].filter(Boolean).join('\n\n[stderr]\n') || '验证命令未返回输出。'
})

const nodeStatusLabel = (status) => {
  const map = {
    success: '通过',
    failed: '失败',
    running: '检测中',
    pending: '等待检测'
  }
  return map[status] || '未知'
}

const nodeIcon = (status, index) => {
  const map = {
    success: '✓',
    failed: '!',
    running: '…',
    pending: String(index + 1)
  }
  return map[status] || String(index + 1)
}

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

const runPipelineCheck = async () => {
  pipelineLoading.value = true
  pipelineError.value = ''

  try {
    const result = await verifyPipeline({
      count: 4,
      workers: 2,
      kafka_wait: 45,
      es_wait: 120
    })
    pipelineResult.value = result.data
    if (!result.data?.success) {
      pipelineError.value = result.data?.error || '全链路验证未通过，请查看验证输出。'
    }
  } catch (error) {
    pipelineError.value = error.response?.data?.detail || error.message || '全链路验证请求失败。'
    pipelineResult.value = {
      success: false,
      exit_code: -1,
      duration_ms: 0,
      nodes: DEFAULT_PIPELINE_NODES.map((node, index) => ({
        ...node,
        status: index === 0 ? 'failed' : 'pending',
        detail: index === 0 ? '验证请求失败' : '未执行'
      })),
      stdout: '',
      stderr: pipelineError.value
    }
  } finally {
    pipelineLoading.value = false
  }
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

.config-header,
.terminal-heading {
  align-items: flex-start;
  display: flex;
  gap: 16px;
  justify-content: space-between;
}

.verify-button {
  flex: 0 0 auto;
}

.pipeline-flow {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.pipeline-step {
  align-items: center;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  display: flex;
  gap: 10px;
  min-height: 76px;
  padding: 12px;
}

.node-icon {
  align-items: center;
  border-radius: 999px;
  display: flex;
  flex: 0 0 34px;
  font-size: 16px;
  font-weight: 900;
  height: 34px;
  justify-content: center;
  width: 34px;
}

.node-copy {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.node-copy strong {
  color: #111827;
  font-size: 14px;
}

.node-copy span {
  color: #6b7280;
  font-size: 12px;
  line-height: 1.35;
}

.node-success {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.node-success .node-icon {
  background: #16a34a;
  color: #ffffff;
}

.node-failed {
  background: #fef2f2;
  border-color: #fecaca;
}

.node-failed .node-icon {
  background: #dc2626;
  color: #ffffff;
}

.node-running {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.node-running .node-icon {
  background: #2563eb;
  color: #ffffff;
}

.node-pending .node-icon {
  background: #f3f4f6;
  color: #4b5563;
}

.terminal-panel {
  background: #111827;
  border-radius: 8px;
  overflow: hidden;
}

.terminal-heading {
  background: #1f2937;
  color: #f9fafb;
  padding: 10px 12px;
}

.terminal-heading span {
  color: #cbd5e1;
  font-size: 12px;
}

.terminal-panel pre {
  color: #e5e7eb;
  font-family: Consolas, 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.55;
  margin: 0;
  max-height: 340px;
  overflow: auto;
  padding: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}

.config-snapshot {
  border-top: 1px solid #e5e7eb;
  padding-top: 16px;
}

@media (max-width: 760px) {
  .page-header,
  .panel-heading,
  .config-header,
  .terminal-heading {
    align-items: stretch;
    flex-direction: column;
  }

  .overview,
  .detail-list,
  .config-panel dl,
  .pipeline-flow {
    grid-template-columns: 1fr;
  }
}
</style>
