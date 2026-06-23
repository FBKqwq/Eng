/**
 * 7 类日志展示元数据：名称、图标、默认列、兜底筛选项、图表模板、级别配色键
 * 默认列与图表带对齐总体规划 §3.2 监控子页表；chartTemplates 供 F4-03 ChartBand 配置驱动渲染
 */

/**
 * @typedef {'keyword' | 'terms' | 'range'} FilterControlType
 * @typedef {{ field: string, label: string, type: FilterControlType }} FallbackFilter
 * @typedef {'traffic' | 'errors' | 'latency' | 'behavior_funnel' | 'security' | 'infra_health'} AggregateTemplate
 * @typedef {'trend' | 'bar' | 'pie'} ChartType
 * @typedef {{ id: string, template: AggregateTemplate, title: string, chartType: ChartType, options?: Record<string, unknown> }} ChartTemplateConfig
 */

/** @type {Record<string, object>} */
export const logTypeMeta = {
  application: {
    logType: 'application',
    title: '应用服务日志',
    icon: 'app-service',
    route: '/monitor/application',
    defaultColumns: ['时间', '级别', '服务', '接口', '状态码', '耗时', '错误码'],
    fallbackFilters: [
      { field: 'log_level', label: '级别', type: 'terms' },
      { field: 'service_name', label: '服务', type: 'terms' },
      { field: 'status_code', label: '状态码', type: 'terms' },
      { field: 'error_code', label: '错误码', type: 'terms' }
    ],
    chartTemplates: [
      { id: 'app-errors-trend', template: 'errors', title: '错误率趋势', chartType: 'trend' },
      { id: 'app-latency-top', template: 'latency', title: 'Top N 慢接口', chartType: 'bar', options: { top_n: 10 } },
      { id: 'app-error-code-dist', template: 'errors', title: 'error_code 分布', chartType: 'pie', options: { group_by: 'error_code' } }
    ],
    levelColorKey: 'log-level'
  },
  behavior: {
    logType: 'behavior',
    title: '用户行为日志',
    icon: 'user-behavior',
    route: '/monitor/behavior',
    defaultColumns: ['时间', '用户', 'action', '页面', '商品', '停留时长'],
    fallbackFilters: [
      { field: 'action', label: '行为类型', type: 'terms' },
      { field: 'user_id', label: '用户', type: 'keyword' },
      { field: 'page', label: '页面', type: 'terms' },
      { field: 'product_id', label: '商品', type: 'terms' }
    ],
    chartTemplates: [
      { id: 'behavior-action-dist', template: 'traffic', title: '行为类型分布', chartType: 'pie', options: { group_by: 'action' } },
      { id: 'behavior-funnel', template: 'behavior_funnel', title: '转化步骤计数', chartType: 'bar' },
      { id: 'behavior-product-top', template: 'traffic', title: '热门商品 Top N', chartType: 'bar', options: { group_by: 'product_id', top_n: 10 } }
    ],
    levelColorKey: 'default'
  },
  'web-server': {
    logType: 'web_server',
    title: 'Web服务器日志',
    icon: 'web-server',
    route: '/monitor/web-server',
    defaultColumns: ['时间', 'URI', '状态码', '耗时', 'upstream', 'UA'],
    fallbackFilters: [
      { field: 'status_code', label: '状态码', type: 'terms' },
      { field: 'request_uri', label: 'URI', type: 'terms' },
      { field: 'remote_addr', label: '客户端 IP', type: 'terms' },
      { field: 'upstream_addr', label: 'upstream', type: 'terms' }
    ],
    chartTemplates: [
      { id: 'web-status-dist', template: 'errors', title: '状态码分布', chartType: 'pie', options: { group_by: 'status_code' } },
      { id: 'web-latency-trend', template: 'latency', title: 'request_time 趋势', chartType: 'trend' },
      { id: 'web-uri-top', template: 'traffic', title: 'Top N URI', chartType: 'bar', options: { group_by: 'request_uri', top_n: 10 } }
    ],
    levelColorKey: 'http-status'
  },
  performance: {
    logType: 'performance',
    title: '性能指标日志',
    icon: 'performance',
    route: '/monitor/performance',
    defaultColumns: ['时间', '服务', '指标名', '指标值', '主机'],
    fallbackFilters: [
      { field: 'service_name', label: '服务', type: 'terms' },
      { field: 'metric_name', label: '指标名', type: 'terms' },
      { field: 'host', label: '主机', type: 'terms' }
    ],
    chartTemplates: [
      { id: 'perf-metric-trend', template: 'infra_health', title: '指标趋势', chartType: 'trend', options: { switchable: 'metric_name' } },
      { id: 'perf-p95-compare', template: 'latency', title: 'p95 对比', chartType: 'bar' }
    ],
    levelColorKey: 'metric-value'
  },
  security: {
    logType: 'security',
    title: '安全日志',
    icon: 'security',
    route: '/monitor/security',
    defaultColumns: ['时间', '事件类型', '风险级', 'IP', '规则', '状态'],
    fallbackFilters: [
      { field: 'risk_level', label: '风险级', type: 'terms' },
      { field: 'client_ip', label: 'IP', type: 'terms' },
      { field: 'rule_name', label: '规则', type: 'terms' },
      { field: 'attack_type', label: '攻击类型', type: 'terms' }
    ],
    chartTemplates: [
      { id: 'sec-risk-dist', template: 'security', title: '风险级分布', chartType: 'pie', options: { group_by: 'risk_level' } },
      { id: 'sec-ip-top', template: 'security', title: 'Top N 风险 IP', chartType: 'bar', options: { group_by: 'client_ip', top_n: 10 } },
      { id: 'sec-block-trend', template: 'security', title: '拦截次数趋势', chartType: 'trend' }
    ],
    levelColorKey: 'risk-level'
  },
  infrastructure: {
    logType: 'infrastructure',
    title: '基础设施日志',
    icon: 'infrastructure',
    route: '/monitor/infrastructure',
    defaultColumns: ['时间', '组件', '资源类型', '状态', '详情'],
    fallbackFilters: [
      { field: 'component', label: '组件', type: 'terms' },
      { field: 'resource_type', label: '资源类型', type: 'terms' },
      { field: 'severity', label: '严重度', type: 'terms' },
      { field: 'status', label: '状态', type: 'terms' }
    ],
    chartTemplates: [
      { id: 'infra-component-health', template: 'infra_health', title: '组件健康比率', chartType: 'pie', options: { group_by: 'component' } },
      { id: 'infra-kafka-lag', template: 'infra_health', title: 'Kafka lag 趋势', chartType: 'trend', options: { metric: 'kafka_lag' } },
      { id: 'infra-resource-trend', template: 'infra_health', title: '资源使用趋势', chartType: 'trend', options: { metric: 'resource_usage' } }
    ],
    levelColorKey: 'resource-status'
  },
  audit: {
    logType: 'audit',
    title: '审计日志',
    icon: 'audit',
    route: '/monitor/audit',
    defaultColumns: ['时间', '操作人', '操作', '对象', '变更前后值'],
    fallbackFilters: [
      { field: 'operator_name', label: '操作人', type: 'terms' },
      { field: 'action', label: '操作', type: 'terms' },
      { field: 'target_type', label: '对象类型', type: 'terms' },
      { field: 'status', label: '状态', type: 'terms' }
    ],
    chartTemplates: [
      { id: 'audit-operator-top', template: 'traffic', title: '操作人 Top N', chartType: 'bar', options: { group_by: 'operator_name', top_n: 10 } },
      { id: 'audit-action-dist', template: 'traffic', title: '操作类型分布', chartType: 'pie', options: { group_by: 'action' } }
    ],
    levelColorKey: 'default'
  }
}

/** 路由键 / API log_type 别名 → 元数据键 */
const META_KEY_ALIASES = {
  web_server: 'web-server'
}

const DEFAULT_META_KEY = 'application'

/**
 * 按路由键或 log_type 取监控子页配置
 * @param {string} key - 如 application、web-server、web_server
 */
export function getLogTypeMeta(key) {
  const metaKey = META_KEY_ALIASES[key] || key
  const meta = logTypeMeta[metaKey]
  if (!meta) {
    console.warn(`[logTypeMeta] 未知日志类型 "${key}"，回退至 ${DEFAULT_META_KEY}`)
    return logTypeMeta[DEFAULT_META_KEY]
  }
  return meta
}

/** 返回全部 7 类元数据（数组形式，供目录/批量渲染） */
export function getAllLogTypeMeta() {
  return Object.values(logTypeMeta)
}
