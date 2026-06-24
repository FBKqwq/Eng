/** 系统状态请求离线/超时等可识别错误码（供 UI 展示） */
export const SYSTEM_STATUS_ERROR_CODES = {
  OFFLINE: 'system_status_offline',
  TIMEOUT: 'system_status_timeout',
  FAILED: 'system_status_failed',
  UNKNOWN: 'system_status_unknown'
}

const COMPONENT_LABELS = {
  backend: 'Backend',
  kafka: 'Kafka',
  elasticsearch: 'Elasticsearch',
  logstash: 'Logstash',
  kibana: 'Kibana',
  llm: 'LLM'
}

const PIPELINE_NODE_DEFS = [
  { key: 'producer', label: '日志生产' },
  { key: 'kafka', label: 'Kafka' },
  { key: 'logstash', label: 'Logstash' },
  { key: 'es', label: 'Elasticsearch' }
]

const normalizeStatus = (value, fallback = 'unknown') => {
  const status = String(value || fallback).toLowerCase()

  if (['ok', 'up', 'healthy', 'running', 'online', 'active', 'success', 'green'].includes(status)) {
    return 'running'
  }

  if (['error', 'down', 'failed', 'unhealthy', 'offline', 'stopped', 'red'].includes(status)) {
    return 'down'
  }

  if (['pending', 'checking', 'loading', 'yellow'].includes(status)) {
    return 'pending'
  }

  return 'unknown'
}

/**
 * 将内部运行态映射为组件/链路统一展示态。
 * @param {'running'|'pending'|'down'|'unknown'} internalStatus
 * @returns {'healthy'|'degraded'|'down'|'unknown'|'offline'}
 */
const toDisplayStatus = (internalStatus) => {
  const map = {
    running: 'healthy',
    pending: 'degraded',
    down: 'down',
    unknown: 'unknown',
    offline: 'offline'
  }
  return map[internalStatus] || 'unknown'
}

/**
 * 从 containers / services / docker.containers 互备读取单组件容器快照。
 * @param {object|null|undefined} status getSystemStatus 解包后的业务负载
 * @param {string} key 组件键，如 kafka、elasticsearch
 */
export const getContainerEntry = (status, key) => {
  if (!status) return {}
  return (
    status.containers?.[key] ||
    status.services?.[key] ||
    status.docker?.containers?.[key] ||
    {}
  )
}

/**
 * 合并 containers 与 services（及 docker.containers）为统一映射，缺失方由另一方补齐。
 * @param {object|null|undefined} status
 */
export const resolveContainersMap = (status) => {
  if (!status) return {}

  const primary = status.containers || {}
  const fallback = status.services || status.docker?.containers || {}
  const keys = new Set([...Object.keys(primary), ...Object.keys(fallback)])

  return [...keys].reduce((acc, key) => {
    acc[key] = { ...fallback[key], ...primary[key] }
    return acc
  }, {})
}

/** 判断关键容器是否为 running */
export const isContainerRunning = (status, key) => {
  const container = getContainerEntry(status, key)
  return normalizeStatus(container.status) === 'running'
}

/** 从容器 ports 字段提取展示用端口 */
const extractPort = (container) => {
  const ports = container?.ports
  if (!ports) return undefined
  if (typeof ports === 'string') {
    const match = ports.match(/:(\d+)->/)
    return match?.[1] || ports
  }
  return String(ports)
}

/** 解析 Elasticsearch 集群健康与容器态兜底 */
const resolveElasticsearchHealth = (status) => {
  const container = getContainerEntry(status, 'elasticsearch')
  const es = status?.elasticsearch || {}
  const clusterStatus = String(es.cluster_status || '').toLowerCase()
  const hasShardHealth = ['green', 'yellow', 'red'].includes(clusterStatus)
  const containerRunning = isContainerRunning(status, 'elasticsearch')

  if (hasShardHealth) {
    const internal =
      clusterStatus === 'green' ? 'running' : clusterStatus === 'yellow' ? 'pending' : 'down'
    return {
      internal,
      display: toDisplayStatus(internal),
      detail: `cluster: ${clusterStatus}`,
      usedContainerFallback: false
    }
  }

  if (clusterStatus === 'unknown' && containerRunning) {
    return {
      internal: 'running',
      display: 'degraded',
      detail: '健康未知，按容器态展示',
      usedContainerFallback: true
    }
  }

  const internal = normalizeStatus(es.available ? 'running' : container.status)
  return {
    internal,
    display: toDisplayStatus(internal),
    detail:
      es.error ||
      container.detail ||
      container.raw_status ||
      '等待后端提供 Elasticsearch 集群健康状态',
    usedContainerFallback: clusterStatus === 'unknown' && internal === 'running'
  }
}

/** 解析 Kafka 可用性与容器态 */
const resolveKafkaHealth = (status) => {
  const container = getContainerEntry(status, 'kafka')
  const kafka = status?.kafka || {}
  const containerRunning = isContainerRunning(status, 'kafka')

  let internal = 'unknown'
  if (kafka.available === true) {
    internal = 'running'
  } else if (containerRunning) {
    internal = 'pending'
  } else if (kafka.available === false && !containerRunning) {
    internal = 'down'
  } else {
    internal = normalizeStatus(container.status)
  }

  const brokers = kafka.brokers_count
  const topic = kafka.topic || status?.kafka_topic
  const detail = kafka.available !== undefined
    ? `broker: ${brokers ?? '-'} / topic: ${topic ?? '-'}`
    : container.detail || container.raw_status || '等待后端提供 Kafka 运行状态'

  return { internal, display: toDisplayStatus(internal), detail }
}

/**
 * 将 getSystemStatus 原始响应归一化为六组件统一结构。
 * @param {object|null|undefined} status 解包后的 res.data；拉取失败时可传 null 并配合 error
 * @param {{ apiHealth?: object, frontendReady?: boolean, error?: Error }} [options]
 * @returns {Array<{ key: string, label: string, status: string, detail: string, port?: string, container?: string }>}
 */
export const normalizeComponents = (status, options = {}) => {
  const { apiHealth = null, frontendReady = true, error = null } = options

  if (!status && error) {
    const err = resolveSystemStatusError(error)
    return Object.keys(COMPONENT_LABELS).map((key) => ({
      key,
      label: COMPONENT_LABELS[key],
      status: 'offline',
      detail: err.message,
      port: undefined,
      container: undefined,
      errorCode: err.code
    }))
  }

  const containers = resolveContainersMap(status)
  const kafkaResolved = resolveKafkaHealth(status)
  const esResolved = resolveElasticsearchHealth(status)

  const backendInternal = normalizeStatus(
    status?.backend_api_status ||
      (status?.kafka_topic ? 'ok' : apiHealth?.status)
  )
  const backendContainer = getContainerEntry(status, 'backend')

  const logstashContainer = containers.logstash || {}
  const kibanaContainer = containers.kibana || {}

  const llmSnapshot = status?.llm || {}
  const llmInternal =
    llmSnapshot.available === true
      ? 'running'
      : llmSnapshot.available === false
        ? 'down'
        : 'unknown'

  return [
    {
      key: 'backend',
      label: COMPONENT_LABELS.backend,
      status: toDisplayStatus(backendInternal),
      detail: status?.backend_api_status
        ? 'system/status: ok'
        : status?.kafka_topic
          ? 'system/status: ok'
          : apiHealth?.status
            ? `health: ${apiHealth.status}`
            : '后端健康检查未返回',
      port: extractPort(backendContainer),
      container: backendContainer.name || backendContainer.service
    },
    {
      key: 'kafka',
      label: COMPONENT_LABELS.kafka,
      status: kafkaResolved.display,
      detail: kafkaResolved.detail,
      port: extractPort(containers.kafka),
      container: containers.kafka?.name || containers.kafka?.service
    },
    {
      key: 'elasticsearch',
      label: COMPONENT_LABELS.elasticsearch,
      status: esResolved.display,
      detail: esResolved.detail,
      port: extractPort(containers.elasticsearch),
      container: containers.elasticsearch?.name || containers.elasticsearch?.service
    },
    {
      key: 'logstash',
      label: COMPONENT_LABELS.logstash,
      status: toDisplayStatus(normalizeStatus(logstashContainer.status)),
      detail: logstashContainer.detail || logstashContainer.raw_status || '等待后端提供 Logstash 容器状态',
      port: extractPort(logstashContainer),
      container: logstashContainer.name || logstashContainer.service
    },
    {
      key: 'kibana',
      label: COMPONENT_LABELS.kibana,
      status: toDisplayStatus(normalizeStatus(kibanaContainer.status)),
      detail: kibanaContainer.detail || kibanaContainer.raw_status || '等待后端提供 Kibana 容器状态',
      port: extractPort(kibanaContainer),
      container: kibanaContainer.name || kibanaContainer.service
    },
    {
      key: 'llm',
      label: COMPONENT_LABELS.llm,
      status: toDisplayStatus(llmInternal),
      detail:
        llmSnapshot.detail ||
        llmSnapshot.error ||
        (llmSnapshot.provider ? `provider: ${llmSnapshot.provider}` : '后端暂未返回 LLM 连通性状态'),
      port: undefined,
      container: undefined
    }
  ]
}

/**
 * 生成日志链路四节点着色数据：生产 → Kafka → Logstash → ES。
 * @param {object|null|undefined} status getSystemStatus 解包后的业务负载
 * @returns {Array<{ key: string, label: string, status: 'healthy'|'degraded'|'down'|'unknown', detail?: string }>}
 */
export const getPipelineNodes = (status) => {
  if (!status) {
    return PIPELINE_NODE_DEFS.map((node) => ({
      ...node,
      status: 'unknown',
      detail: '尚未获取系统状态'
    }))
  }

  const kafkaResolved = resolveKafkaHealth(status)
  const esResolved = resolveElasticsearchHealth(status)
  const logstashContainer = getContainerEntry(status, 'logstash')
  const logstashInternal = normalizeStatus(logstashContainer.status)

  const producerInternal =
    status.backend_api_status === 'ok' || status.kafka?.available !== undefined
      ? status.kafka?.available === false
        ? 'pending'
        : 'running'
      : 'unknown'

  const toPipelineStatus = (internal) => {
    if (internal === 'running') return 'healthy'
    if (internal === 'pending') return 'degraded'
    if (internal === 'down') return 'down'
    return 'unknown'
  }

  return [
    {
      key: 'producer',
      label: '日志生产',
      status: toPipelineStatus(producerInternal),
      detail:
        producerInternal === 'running'
          ? '后端可生产模拟日志'
          : '等待后端或 Kafka 就绪'
    },
    {
      key: 'kafka',
      label: 'Kafka',
      status: toPipelineStatus(kafkaResolved.internal),
      detail: kafkaResolved.detail
    },
    {
      key: 'logstash',
      label: 'Logstash',
      status: toPipelineStatus(logstashInternal),
      detail:
        logstashContainer.detail ||
        logstashContainer.raw_status ||
        (logstashInternal === 'unknown' ? '等待容器状态' : undefined)
    },
    {
      key: 'es',
      label: 'Elasticsearch',
      status: esResolved.usedContainerFallback
        ? 'degraded'
        : toPipelineStatus(esResolved.internal),
      detail: esResolved.detail
    }
  ]
}

/**
 * 综合嵌套字段折算链路健康四态（禁止读 overall / pipeline_healthy）。
 * @param {object|null|undefined} status getSystemStatus 解包后的 res.data
 * @returns {'success'|'warning'|'danger'|'unknown'}
 */
export const derivePipelineHealthTone = (status) => {
  if (!status) return 'unknown'

  const dockerAvailable = status.docker?.available
  const kafkaAvailable = status.kafka?.available
  const esAvailable = status.elasticsearch?.available
  const esCluster = String(status.elasticsearch?.cluster_status || '').toLowerCase()
  const kafkaRunning = isContainerRunning(status, 'kafka')
  const esRunning = isContainerRunning(status, 'elasticsearch')

  const kafkaRed = kafkaAvailable === false && !kafkaRunning
  const esRed = esAvailable === false && !esRunning
  if (kafkaRed || esRed || esCluster === 'red') {
    return 'danger'
  }

  if (esCluster === 'yellow') return 'warning'

  if (dockerAvailable === false) {
    const kafkaHealthy = kafkaAvailable === true && kafkaRunning
    const esHealthy = esAvailable === true && esRunning
    if (kafkaHealthy && esHealthy) return 'warning'
    if (kafkaAvailable === true || esAvailable === true || kafkaRunning || esRunning) {
      return 'warning'
    }
    return 'unknown'
  }

  const kafkaHealthy = kafkaAvailable === true && kafkaRunning
  const esHealthy = esAvailable === true && esRunning
  if (kafkaHealthy && esHealthy) {
    return 'success'
  }

  if (
    kafkaAvailable === true ||
    esAvailable === true ||
    kafkaRunning ||
    esRunning
  ) {
    return 'warning'
  }

  return 'unknown'
}

/**
 * 将拉取系统状态失败时的 Error 转为可展示错误码与文案。
 * @param {Error|unknown} error axios / 业务 reject 对象
 */
export const resolveSystemStatusError = (error) => {
  if (!error) {
    return { code: SYSTEM_STATUS_ERROR_CODES.UNKNOWN, message: '未知错误' }
  }

  if (error.error?.code) {
    return {
      code: error.error.code,
      message: error.error.message || error.message || '获取系统状态失败'
    }
  }

  if (error.code === 'ECONNABORTED' || /timeout/i.test(String(error.message || ''))) {
    return {
      code: SYSTEM_STATUS_ERROR_CODES.TIMEOUT,
      message: '系统状态请求超时，请稍后重试'
    }
  }

  if (error.code === 'ERR_NETWORK' || !error.response) {
    return {
      code: SYSTEM_STATUS_ERROR_CODES.OFFLINE,
      message: '无法连接后端服务，请确认 API 是否启动'
    }
  }

  return {
    code: SYSTEM_STATUS_ERROR_CODES.FAILED,
    message: error.message || '获取系统状态失败'
  }
}

export const getStatusMeta = (status) => {
  const normalized = normalizeStatus(status)
  const metaMap = {
    running: { label: '正常', tone: 'success' },
    down: { label: '异常', tone: 'danger' },
    pending: { label: '需关注', tone: 'warning' },
    unknown: { label: '未知', tone: 'neutral' }
  }

  return metaMap[normalized]
}

export const getClusterHealthMeta = (status) => {
  const health = String(status || 'unknown').toLowerCase()
  const metaMap = {
    green: { label: 'Green', tone: 'success', description: '集群健康，主分片与副本分片均已分配。' },
    yellow: { label: 'Yellow', tone: 'warning', description: '主分片可用，但存在未分配副本分片。' },
    red: { label: 'Red', tone: 'danger', description: '存在未分配主分片，检索或写入可能受影响。' },
    running: { label: 'Running', tone: 'success', description: 'Elasticsearch 容器正在运行；当前接口未返回集群分片级健康详情。' },
    up: { label: 'Running', tone: 'success', description: 'Elasticsearch 服务可访问；当前未返回集群分片级健康详情。' },
    ok: { label: 'Running', tone: 'success', description: 'Elasticsearch 服务可访问；当前未返回集群分片级健康详情。' },
    unknown: { label: 'Unknown', tone: 'neutral', description: '后端暂未获取到 Elasticsearch 集群健康状态。' }
  }

  return metaMap[health] || metaMap.unknown
}

export const formatBoolean = (value) => {
  if (value === true) {
    return '是'
  }

  if (value === false) {
    return '否'
  }

  return '-'
}

export const formatValue = (value, suffix = '') => {
  if (value === null || value === undefined || value === '') {
    return '-'
  }

  return `${value}${suffix}`
}

/** 遗留开发者页使用；新页面请用 normalizeComponents */
export const buildDeveloperServices = ({ apiHealth, systemStatus, frontendReady }) => {
  const kafkaContainer = getContainerEntry(systemStatus, 'kafka')
  const elasticsearchContainer = getContainerEntry(systemStatus, 'elasticsearch')
  const logstashContainer = getContainerEntry(systemStatus, 'logstash')
  const kibanaContainer = getContainerEntry(systemStatus, 'kibana')
  const elasticsearchHealthStatus = systemStatus?.elasticsearch?.cluster_status
  const hasElasticsearchHealth = ['green', 'yellow', 'red'].includes(
    String(elasticsearchHealthStatus || '').toLowerCase()
  )

  return [
    {
      key: 'frontend',
      name: 'Frontend',
      type: 'Vue / Vite',
      status: frontendReady ? 'running' : 'unknown',
      endpoint: typeof window !== 'undefined' ? window.location.origin : '-',
      detail: '当前开发者状态监控页面已加载'
    },
    {
      key: 'backend',
      name: 'Backend',
      type: 'FastAPI',
      status: normalizeStatus(
        systemStatus?.backend_api_status || (systemStatus?.kafka_topic ? 'ok' : apiHealth?.status)
      ),
      endpoint: '/api/v1/system/status',
      detail: systemStatus?.backend_api_status
        ? 'system/status: ok'
        : systemStatus?.kafka_topic
          ? 'system/status: ok'
          : apiHealth?.status
            ? `health: ${apiHealth.status}`
            : '后端健康检查未返回'
    },
    {
      key: 'kafka',
      name: 'Kafka',
      type: 'Container / Broker',
      status: normalizeStatus(systemStatus?.kafka?.available ? 'running' : kafkaContainer.status),
      endpoint: systemStatus?.kafka_bootstrap_servers || '-',
      detail: systemStatus?.kafka
        ? `broker: ${formatValue(systemStatus.kafka.brokers_count)} / topic: ${systemStatus.kafka.topic}`
        : kafkaContainer.detail || kafkaContainer.raw_status || '等待后端提供 Kafka 运行状态'
    },
    {
      key: 'elasticsearch',
      name: 'Elasticsearch',
      type: 'Container / Search',
      status: normalizeStatus(
        hasElasticsearchHealth ? elasticsearchHealthStatus : elasticsearchContainer.status
      ),
      endpoint: systemStatus?.elasticsearch_hosts || '-',
      detail: hasElasticsearchHealth
        ? `cluster: ${elasticsearchHealthStatus}`
        : elasticsearchContainer.detail ||
            elasticsearchContainer.raw_status ||
            systemStatus?.elasticsearch?.error ||
            '等待后端提供 Elasticsearch 运行状态'
    },
    {
      key: 'logstash',
      name: 'Logstash',
      type: 'Container / Pipeline',
      status: normalizeStatus(logstashContainer.status),
      endpoint: logstashContainer.endpoint || '-',
      detail: logstashContainer.detail || '等待后端提供 Logstash 容器状态'
    },
    {
      key: 'kibana',
      name: 'Kibana',
      type: 'Container / Dashboard',
      status: normalizeStatus(kibanaContainer.status),
      endpoint: systemStatus?.kibana_url || import.meta.env.VITE_KIBANA_URL || '-',
      detail: kibanaContainer.detail || '等待后端提供 Kibana 容器状态'
    }
  ]
}
