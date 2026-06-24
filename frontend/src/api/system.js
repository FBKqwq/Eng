import request from './request'

/** 全链路验证长超时（毫秒），对齐后端脚本耗时 */
const PIPELINE_VERIFY_TIMEOUT_MS = 210000

/** 系统状态探活超时（毫秒）：要探 Kafka + ES + Docker 三个外部依赖，留足缓冲 */
const SYSTEM_STATUS_TIMEOUT_MS = 30000

/** 全链路验证默认参数（与旧 system/index.vue、后端 PipelineVerifyRequest 对齐） */
const DEFAULT_VERIFY_COUNT = 4
const DEFAULT_VERIFY_WORKERS = 2
const DEFAULT_KAFKA_WAIT = 45
const DEFAULT_ES_WAIT = 120
const MIN_VERIFY_WORKERS = 1
const MAX_VERIFY_WORKERS = 8

/**
 * API 健康探活 → GET /health
 * 解包后 res.data：{ status: "ok" }
 * 失败：catch (e) { e.error?.code }
 */
export const getHealth = () => request.get('/health')

/** 兼容 F1 命名，等价于 getHealth */
export const getApiHealth = getHealth

/**
 * 系统运行快照 → GET /system/status
 *
 * 解包后 res.data 关键字段：
 * - kafka_bootstrap_servers, kafka_topic, elasticsearch_hosts, elasticsearch_index_pattern
 * - kafka { available, brokers_count, topics_count, configured_topic, ... }
 * - elasticsearch { available, cluster_status, docs_count, indices_count, ... }
 * - docker { available, ... }
 * - containers { kafka, elasticsearch, logstash, kibana, ... } 各服务容器 status
 * - services { ... }
 *
 * 禁止依赖顶层 available / placeholder（已废弃）；改读 kafka.available /
 * elasticsearch.available / docker.available。失败：catch (e) { e.error?.code }
 */
export const getSystemStatus = () =>
  request.get('/system/status', { timeout: SYSTEM_STATUS_TIMEOUT_MS })

/**
 * Docker 容器状态 → GET /system/containers
 * 解包后 res.data：{ project, available, error, containers }
 */
export const getSystemContainers = () => request.get('/system/containers')

/**
 * 归一化 PipelineVerifyRequest 请求体。
 * workers 默认 2，与旧页一致。
 *
 * @param {Record<string, unknown>} [payload]
 * @returns {{ count: number, workers: number, kafka_wait: number, es_wait: number }}
 */
function buildPipelineVerifyPayload(payload = {}) {
  const count = Number(payload.count ?? DEFAULT_VERIFY_COUNT)
  const workers = Number(payload.workers ?? DEFAULT_VERIFY_WORKERS)
  const kafkaWait = Number(payload.kafka_wait ?? DEFAULT_KAFKA_WAIT)
  const esWait = Number(payload.es_wait ?? DEFAULT_ES_WAIT)

  return {
    count: Number.isFinite(count) ? Math.min(20, Math.max(1, Math.floor(count))) : DEFAULT_VERIFY_COUNT,
    workers: Number.isFinite(workers)
      ? Math.min(MAX_VERIFY_WORKERS, Math.max(MIN_VERIFY_WORKERS, Math.floor(workers)))
      : DEFAULT_VERIFY_WORKERS,
    kafka_wait: Number.isFinite(kafkaWait) ? Math.min(180, Math.max(5, kafkaWait)) : DEFAULT_KAFKA_WAIT,
    es_wait: Number.isFinite(esWait) ? Math.min(300, Math.max(10, esWait)) : DEFAULT_ES_WAIT
  }
}

/**
 * 全链路验证（长耗时）→ POST /system/pipeline/verify
 *
 * @param {Record<string, unknown>} [payload] 支持 count、workers(1~8)、kafka_wait、es_wait
 * 解包后 res.data（PipelineVerifyResponse）：
 * { success, exit_code, duration_ms, command, nodes[], stdout, stderr, error? }
 * nodes[]：{ key, label, status, detail? }，status 为 success/failed/running/pending
 *
 * 失败：catch (e) { e.error?.code } 或 HTTP 422 读 e.response.data.detail
 */
export const verifyPipeline = (payload = {}) =>
  request.post('/system/pipeline/verify', buildPipelineVerifyPayload(payload), {
    timeout: PIPELINE_VERIFY_TIMEOUT_MS
  })
