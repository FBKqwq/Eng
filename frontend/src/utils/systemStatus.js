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

export const buildDeveloperServices = ({ apiHealth, systemStatus, frontendReady }) => {
  const containers = systemStatus?.containers || systemStatus?.docker?.containers || {}
  const services = systemStatus?.services || systemStatus?.docker?.containers || {}
  const kafkaContainer = containers.kafka || services.kafka || {}
  const elasticsearchContainer = containers.elasticsearch || services.elasticsearch || {}
  const elasticsearchHealthStatus = systemStatus?.elasticsearch?.cluster_status
  const hasElasticsearchHealth = ['green', 'yellow', 'red'].includes(String(elasticsearchHealthStatus || '').toLowerCase())

  return [
    {
      key: 'frontend',
      name: 'Frontend',
      type: 'Vue / Vite',
      status: frontendReady ? 'running' : 'unknown',
      endpoint: window.location.origin,
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
      status: normalizeStatus(hasElasticsearchHealth ? elasticsearchHealthStatus : elasticsearchContainer.status),
      endpoint: systemStatus?.elasticsearch_hosts || '-',
      detail: hasElasticsearchHealth
        ? `cluster: ${elasticsearchHealthStatus}`
        : elasticsearchContainer.detail || elasticsearchContainer.raw_status || systemStatus?.elasticsearch?.error || '等待后端提供 Elasticsearch 运行状态'
    },
    {
      key: 'logstash',
      name: 'Logstash',
      type: 'Container / Pipeline',
      status: normalizeStatus(containers.logstash?.status || services.logstash?.status),
      endpoint: containers.logstash?.endpoint || '-',
      detail: containers.logstash?.detail || '等待后端提供 Logstash 容器状态'
    },
    {
      key: 'kibana',
      name: 'Kibana',
      type: 'Container / Dashboard',
      status: normalizeStatus(containers.kibana?.status || services.kibana?.status),
      endpoint: systemStatus?.kibana_url || import.meta.env.VITE_KIBANA_URL || '-',
      detail: containers.kibana?.detail || '等待后端提供 Kibana 容器状态'
    }
  ]
}
