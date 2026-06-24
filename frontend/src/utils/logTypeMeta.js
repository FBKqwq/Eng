/**
 * 7 类日志监控页元数据：列定义、筛选兜底、图表模板、钻取与口径说明
 */

/** @typedef {'timestamp'|'log_level'|'http_status'|'duration'|'metric'|'risk_level'|'severity'|'text'|'copyable'|'trace'|'change_summary'|'status'} ColumnRenderType */

/**
 * @typedef {object} MonitorColumn
 * @property {string} label
 * @property {string} key
 * @property {ColumnRenderType} [renderType]
 * @property {boolean} [sortable]
 * @property {string} [width]
 * @property {string} [unit]
 * @property {boolean} [drillable]
 * @property {'trace'|'user'|'keyword'} [drillTarget]
 */

/**
 * @typedef {object} ChartTemplateConfig
 * @property {string} id
 * @property {'traffic'|'errors'|'latency'|'behavior_funnel'|'security'|'infra_health'} [template]
 * @property {'log_level'|'service_name'|'log_type'|'event_type'|'error_code'|'status_code'|'user_id'|'client_ip'} [groupBy]
 * @property {string} title
 * @property {string} description
 * @property {'trend'|'bar'|'pie'} chartType
 * @property {boolean} [primary]
 * @property {Record<string, unknown>} [options]
 */

const COL = {
  time: { label: '时间', key: 'timestamp', renderType: 'timestamp', sortable: true, width: '168px' },
  level: { label: '级别', key: 'log_level', renderType: 'log_level', sortable: true, width: '88px' },
  service: { label: '服务', key: 'service_name', renderType: 'text', sortable: true },
  message: { label: '消息', key: 'message', renderType: 'text' },
  user: { label: '用户', key: 'user_id', renderType: 'copyable', drillable: true, drillTarget: 'user' },
  action: { label: '行为', key: 'action', renderType: 'text' },
  page: { label: '页面', key: 'page', renderType: 'text' },
  product: { label: '商品', key: 'product_name', renderType: 'text' },
  path: { label: '接口', key: 'request_path', renderType: 'copyable' },
  statusCode: {
    label: '状态码',
    key: 'status_code',
    renderType: 'http_status',
    sortable: true,
    width: '88px'
  },
  duration: {
    label: '耗时',
    key: 'response_time_ms',
    renderType: 'duration',
    sortable: true,
    width: '88px',
    unit: 'ms'
  },
  errorCode: { label: '错误码', key: 'error_code', renderType: 'text' },
  uri: { label: 'URI', key: 'request_uri', renderType: 'copyable', drillable: true, drillTarget: 'keyword' },
  upstream: { label: 'upstream', key: 'upstream_addr', renderType: 'copyable' },
  ua: { label: 'UA', key: 'http_user_agent', renderType: 'text' },
  metricName: { label: '指标名', key: 'metric_name', renderType: 'text' },
  metricValue: {
    label: '指标值',
    key: 'metric_value',
    renderType: 'metric',
    sortable: true,
    unit: 'auto'
  },
  host: { label: '主机', key: 'host', renderType: 'text' },
  eventType: { label: '事件类型', key: 'event_type', renderType: 'text' },
  risk: { label: '风险级', key: 'risk_level', renderType: 'risk_level', width: '88px' },
  ip: { label: 'IP', key: 'client_ip', renderType: 'copyable', drillable: true, drillTarget: 'keyword' },
  rule: { label: '规则', key: 'rule_name', renderType: 'text' },
  component: { label: '组件', key: 'component', renderType: 'text' },
  resource: { label: '资源类型', key: 'resource_type', renderType: 'text' },
  status: { label: '状态', key: 'status', renderType: 'status', width: '80px' },
  summary: { label: '详情', key: 'summary', renderType: 'text' },
  operator: { label: '操作人', key: 'operator_name', renderType: 'text' },
  auditAction: { label: '操作', key: 'action', renderType: 'text' },
  target: { label: '对象', key: 'target_name', renderType: 'text' },
  change: { label: '变更摘要', key: 'change_summary', renderType: 'change_summary' },
  trace: {
    label: '链路',
    key: 'trace_id',
    renderType: 'trace',
    drillable: true,
    drillTarget: 'trace',
    width: '120px'
  }
}

/** @type {Record<string, object>} */
export const logTypeMeta = {
  application: {
    logType: 'application',
    title: '应用服务日志',
    pageDescription: 'API 请求、服务调用与异常事件；支持按服务、级别、错误码精确筛选。',
    icon: 'app-service',
    route: '/monitor/application',
    defaultSort: { field: 'timestamp', order: 'desc' },
    coreMetrics: [
      { id: 'error_rate', label: '错误日志', hint: 'ERROR 级别或异常事件' },
      { id: 'latency', label: '接口耗时', hint: 'response_time_ms 分位' },
      { id: 'top_service', label: '活跃服务', hint: 'service_name 分布' }
    ],
    primaryChartId: 'app-level-trend',
    columns: [
      COL.time,
      COL.level,
      COL.service,
      COL.path,
      COL.statusCode,
      COL.duration,
      COL.errorCode,
      COL.trace
    ],
    drillableFields: ['trace_id', 'user_id', 'request_path'],
    fallbackFilters: [
      { field: 'log_level', label: '级别', type: 'terms' },
      { field: 'service_name', label: '服务', type: 'terms' },
      { field: 'status_code', label: '状态码', type: 'terms' },
      { field: 'error_code', label: '错误码', type: 'terms' }
    ],
    chartTemplates: [
      {
        id: 'app-level-trend',
        groupBy: 'log_level',
        title: '日志级别趋势',
        description: '仅聚合 application 日志，按级别拆分时间序列',
        chartType: 'trend',
        primary: true,
        options: { interval: '1m' }
      },
      {
        id: 'app-service-top',
        groupBy: 'service_name',
        title: '活跃服务 Top N',
        description: 'application 日志按 service_name 聚合',
        chartType: 'bar',
        options: { top_n: 10 }
      },
      {
        id: 'app-error-code-dist',
        groupBy: 'error_code',
        title: 'error_code 分布',
        description: '仅聚合 application 日志的 error_code',
        chartType: 'pie'
      }
    ],
    levelColorKey: 'log-level'
  },

  behavior: {
    logType: 'behavior',
    title: '用户行为日志',
    pageDescription: '浏览、搜索、加购与支付等行为轨迹；action 等字段请用关键字模糊搜索。',
    icon: 'user-behavior',
    route: '/monitor/behavior',
    defaultSort: { field: 'timestamp', order: 'desc' },
    coreMetrics: [
      { id: 'funnel', label: '转化漏斗', hint: '五步固定漏斗' },
      { id: 'users', label: '活跃用户', hint: 'user_id 去重' },
      { id: 'events', label: '行为事件', hint: 'event_type 计数' }
    ],
    primaryChartId: 'behavior-event-trend',
    columns: [COL.time, COL.user, COL.action, COL.page, COL.product, COL.eventType],
    drillableFields: ['user_id', 'session_id'],
    fallbackFilters: [
      { field: 'user_id', label: '用户', type: 'keyword' },
      { field: 'event_type', label: '事件类型', type: 'terms' },
      { field: 'session_id', label: '会话', type: 'keyword' }
    ],
    chartTemplates: [
      {
        id: 'behavior-event-trend',
        groupBy: 'event_type',
        title: '行为事件趋势',
        description: '仅聚合 behavior 日志，按 event_type 拆分时间序列',
        chartType: 'trend',
        primary: true,
        options: { interval: '1m' }
      },
      {
        id: 'behavior-funnel',
        template: 'behavior_funnel',
        title: '转化步骤分布',
        description: 'page_view → pay_button_click 五步计数',
        chartType: 'pie'
      },
      {
        id: 'behavior-user-top',
        groupBy: 'user_id',
        title: '活跃用户 Top N',
        description: 'behavior 日志按 user_id 聚合',
        chartType: 'bar',
        options: { top_n: 10 }
      }
    ],
    levelColorKey: 'default'
  },

  'web-server': {
    logType: 'web_server',
    title: 'Web 服务器日志',
    pageDescription: 'Nginx access/error 日志；URI/IP 请用关键字搜索 request_path 或 message。',
    icon: 'web-server',
    route: '/monitor/web-server',
    defaultSort: { field: 'timestamp', order: 'desc' },
    coreMetrics: [
      { id: 'qps', label: '请求量', hint: 'traffic 模板时间序列' },
      { id: 'status', label: '状态码', hint: '4xx/5xx 占比' },
      { id: 'latency', label: 'request_time', hint: 'upstream 耗时' }
    ],
    primaryChartId: 'web-status-trend',
    columns: [COL.time, COL.uri, COL.statusCode, COL.duration, COL.upstream, COL.ua],
    drillableFields: ['request_uri', 'trace_id'],
    fallbackFilters: [
      { field: 'status_code', label: '状态码', type: 'terms' },
      { field: 'service_name', label: '服务', type: 'terms' },
      { field: 'event_type', label: '事件类型', type: 'terms' }
    ],
    chartTemplates: [
      {
        id: 'web-status-trend',
        groupBy: 'status_code',
        title: '状态码趋势',
        description: '仅聚合 web_server 日志，按状态码拆分时间序列',
        chartType: 'trend',
        primary: true,
        options: { interval: '1m' }
      },
      {
        id: 'web-status-dist',
        groupBy: 'status_code',
        title: '状态码分布',
        description: 'web_server 日志 HTTP 状态码分布',
        chartType: 'pie'
      },
      {
        id: 'web-service-top',
        groupBy: 'service_name',
        title: '服务请求 Top N',
        description: 'web_server 日志按 service_name 聚合',
        chartType: 'bar',
        options: { top_n: 10 }
      }
    ],
    levelColorKey: 'http-status'
  },

  performance: {
    logType: 'performance',
    title: '性能指标日志',
    pageDescription: 'QPS、延迟、资源占用等指标快照；metric_name 请用关键字搜索。',
    icon: 'performance',
    route: '/monitor/performance',
    defaultSort: { field: 'timestamp', order: 'desc' },
    coreMetrics: [
      { id: 'p95', label: 'P95 延迟', hint: 'latency 模板' },
      { id: 'metric', label: '指标值', hint: 'metric_value' },
      { id: 'resource', label: '资源占用', hint: 'cpu/memory/disk' }
    ],
    primaryChartId: 'perf-service-trend',
    columns: [COL.time, COL.service, COL.metricName, COL.metricValue, COL.host],
    drillableFields: ['service_name'],
    fallbackFilters: [
      { field: 'service_name', label: '服务', type: 'terms' },
      { field: 'log_level', label: '级别', type: 'terms' },
      { field: 'host', label: '主机', type: 'keyword' }
    ],
    chartTemplates: [
      {
        id: 'perf-service-trend',
        groupBy: 'service_name',
        title: '性能采样趋势',
        description: '仅聚合 performance 日志，按服务拆分采样量',
        chartType: 'trend',
        primary: true,
        options: { interval: '1m', top_n: 8 }
      },
      {
        id: 'perf-service-top',
        groupBy: 'service_name',
        title: '性能样本 Top 服务',
        description: 'performance 日志按 service_name 聚合',
        chartType: 'bar',
        options: { top_n: 10 }
      },
      {
        id: 'perf-level-dist',
        groupBy: 'log_level',
        title: '采样级别分布',
        description: 'performance 日志 log_level 分布',
        chartType: 'pie'
      }
    ],
    levelColorKey: 'metric-value'
  },

  security: {
    logType: 'security',
    title: '安全日志',
    pageDescription: '登录失败、非法 token、高频 IP 等安全事件；IP/规则名请用关键字搜索。',
    icon: 'security',
    route: '/monitor/security',
    defaultSort: { field: 'timestamp', order: 'desc' },
    coreMetrics: [
      { id: 'risk', label: '风险分布', hint: 'risk_level' },
      { id: 'blocked', label: '拦截次数', hint: 'is_blocked' },
      { id: 'top_ip', label: '风险 IP', hint: 'client_ip Top N' }
    ],
    primaryChartId: 'sec-event-trend',
    columns: [COL.time, COL.eventType, COL.risk, COL.ip, COL.rule, COL.status],
    drillableFields: ['client_ip', 'trace_id'],
    fallbackFilters: [
      { field: 'event_type', label: '事件类型', type: 'terms' },
      { field: 'log_level', label: '级别', type: 'terms' },
      { field: 'status', label: '状态', type: 'terms' }
    ],
    chartTemplates: [
      {
        id: 'sec-event-trend',
        groupBy: 'event_type',
        title: '安全事件趋势',
        description: '仅聚合 security 日志，按 event_type 拆分时间序列',
        chartType: 'trend',
        primary: true,
        options: { interval: '1m' }
      },
      {
        id: 'sec-risk-dist',
        template: 'security',
        title: '风险级分布',
        description: 'security 日志 risk_level 计数',
        chartType: 'pie'
      },
      {
        id: 'sec-ip-top',
        groupBy: 'client_ip',
        title: 'Top N 风险 IP',
        description: 'client_ip 访问次数 Top N',
        chartType: 'bar',
        options: { top_n: 10 }
      }
    ],
    levelColorKey: 'risk-level'
  },

  infrastructure: {
    logType: 'infrastructure',
    title: '基础设施日志',
    pageDescription: '主机、Kafka、ES 等组件资源与健康状态；component 请用关键字搜索。',
    icon: 'infrastructure',
    route: '/monitor/infrastructure',
    defaultSort: { field: 'timestamp', order: 'desc' },
    coreMetrics: [
      { id: 'component', label: '组件健康', hint: 'component 分组' },
      { id: 'cpu', label: 'CPU', hint: 'cpu_percent 均值' },
      { id: 'lag', label: 'Kafka lag', hint: '需关键字检索 lag 字段' }
    ],
    primaryChartId: 'infra-service-trend',
    columns: [COL.time, COL.component, COL.resource, COL.status, COL.summary],
    drillableFields: ['component'],
    fallbackFilters: [
      { field: 'service_name', label: '服务', type: 'terms' },
      { field: 'log_level', label: '级别', type: 'terms' },
      { field: 'status', label: '状态', type: 'terms' }
    ],
    chartTemplates: [
      {
        id: 'infra-service-trend',
        groupBy: 'service_name',
        title: '基础设施事件趋势',
        description: '仅聚合 infrastructure 日志，按服务拆分时间序列',
        chartType: 'trend',
        primary: true,
        options: { interval: '1m' }
      },
      {
        id: 'infra-component-health',
        template: 'infra_health',
        title: '组件 CPU 均值',
        description: 'infrastructure + performance 的 component CPU 均值',
        chartType: 'bar',
        options: { top_n: 10 }
      },
      {
        id: 'infra-event-dist',
        groupBy: 'event_type',
        title: '基础设施事件分布',
        description: 'infrastructure 日志 event_type 分布',
        chartType: 'pie'
      }
    ],
    levelColorKey: 'resource-status'
  },

  audit: {
    logType: 'audit',
    title: '审计日志',
    pageDescription: '管理员操作与配置变更；操作人/操作类型请用关键字搜索 message。',
    icon: 'audit',
    route: '/monitor/audit',
    defaultSort: { field: 'timestamp', order: 'desc' },
    coreMetrics: [
      { id: 'ops', label: '操作次数', hint: '审计事件总量' },
      { id: 'operators', label: '操作人', hint: 'operator 关键字' },
      { id: 'manual', label: '人工操作', hint: 'is_manual' }
    ],
    primaryChartId: 'audit-event-trend',
    columns: [COL.time, COL.operator, COL.auditAction, COL.target, COL.change, COL.status],
    drillableFields: ['operator_id'],
    fallbackFilters: [
      { field: 'user_id', label: '关联用户', type: 'keyword' },
      { field: 'event_type', label: '事件类型', type: 'terms' },
      { field: 'status', label: '状态', type: 'terms' }
    ],
    chartTemplates: [
      {
        id: 'audit-event-trend',
        groupBy: 'event_type',
        title: '审计事件量趋势',
        description: '仅聚合 audit 日志，按 event_type 拆分时间序列',
        chartType: 'trend',
        primary: true,
        options: { interval: '1h' }
      },
      {
        id: 'audit-operator-top',
        groupBy: 'user_id',
        title: '操作人 Top N',
        description: 'audit 日志按 user_id 聚合',
        chartType: 'bar',
        options: { top_n: 10 }
      },
      {
        id: 'audit-level-dist',
        groupBy: 'log_level',
        title: '审计级别分布',
        description: 'audit 日志 log_level 分布',
        chartType: 'pie'
      }
    ],
    levelColorKey: 'default'
  }
}

const META_KEY_ALIASES = {
  web_server: 'web-server'
}

const DEFAULT_META_KEY = 'application'

export function getLogTypeMeta(key) {
  const metaKey = META_KEY_ALIASES[key] || key
  const meta = logTypeMeta[metaKey]
  if (!meta) {
    console.warn(`[logTypeMeta] 未知日志类型 "${key}"，回退至 ${DEFAULT_META_KEY}`)
    return logTypeMeta[DEFAULT_META_KEY]
  }
  return meta
}

export function getAllLogTypeMeta() {
  return Object.values(logTypeMeta)
}

/** 从 meta 取表格列（兼容旧 defaultColumns 字符串标签） */
export function resolveMonitorColumns(meta) {
  if (meta?.columns?.length) return meta.columns
  return [
    COL.time,
    COL.level,
    COL.service,
    { label: '消息', key: 'message', renderType: 'text' }
  ]
}
