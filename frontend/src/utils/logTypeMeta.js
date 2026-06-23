/**
 * 7 类日志展示元数据：名称、路由键、默认列、图表模板键、级别配色键
 * 默认列与图表模板对齐总体规划 §3.2 监控子页表
 */

/** @type {Record<string, object>} */
export const logTypeMeta = {
  application: {
    logType: 'application',
    title: '应用服务日志',
    route: '/monitor/application',
    defaultColumns: ['时间', '级别', '服务', '接口', '状态码', '耗时', '错误码'],
    chartTemplates: ['errors', 'latency', 'traffic'],
    levelColorKey: 'log-level'
  },
  behavior: {
    logType: 'behavior',
    title: '用户行为日志',
    route: '/monitor/behavior',
    defaultColumns: ['时间', '用户', 'action', '页面', '商品', '停留时长'],
    chartTemplates: ['behavior_funnel', 'traffic'],
    levelColorKey: 'default'
  },
  'web-server': {
    logType: 'web_server',
    title: 'Web服务器日志',
    route: '/monitor/web-server',
    defaultColumns: ['时间', 'URI', '状态码', '耗时', 'upstream', 'UA'],
    chartTemplates: ['errors', 'latency', 'traffic'],
    levelColorKey: 'http-status'
  },
  performance: {
    logType: 'performance',
    title: '性能指标日志',
    route: '/monitor/performance',
    defaultColumns: ['时间', '服务', '指标名', '指标值', '主机'],
    chartTemplates: ['infra_health', 'latency'],
    levelColorKey: 'metric-value'
  },
  security: {
    logType: 'security',
    title: '安全日志',
    route: '/monitor/security',
    defaultColumns: ['时间', '事件类型', '风险级', 'IP', '规则', '状态'],
    chartTemplates: ['security'],
    levelColorKey: 'risk-level'
  },
  infrastructure: {
    logType: 'infrastructure',
    title: '基础设施日志',
    route: '/monitor/infrastructure',
    defaultColumns: ['时间', '组件', '资源类型', '状态', '详情'],
    chartTemplates: ['infra_health'],
    levelColorKey: 'resource-status'
  },
  audit: {
    logType: 'audit',
    title: '审计日志',
    route: '/monitor/audit',
    defaultColumns: ['时间', '操作人', '操作', '对象', '变更前后值'],
    chartTemplates: ['traffic'],
    levelColorKey: 'default'
  }
}

/** 路由键 / API log_type 别名 → 元数据键 */
const META_KEY_ALIASES = {
  web_server: 'web-server'
}

/**
 * 按路由键或 log_type 取监控子页配置
 * @param {string} key - 如 application、web-server、web_server
 */
export function getLogTypeMeta(key) {
  const metaKey = META_KEY_ALIASES[key] || key
  return logTypeMeta[metaKey] || logTypeMeta.application
}

/** 返回全部 7 类元数据（数组形式，供目录/批量渲染） */
export function getAllLogTypeMeta() {
  return Object.values(logTypeMeta)
}
