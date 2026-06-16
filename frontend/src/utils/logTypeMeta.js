/** 7 类日志展示元数据：名称、路由键、默认列、级别配色键 */

const LOG_TYPE_META = {
  application: {
    logType: 'application',
    title: '应用服务日志',
    route: '/monitor/application',
    defaultColumns: ['时间', '级别', '服务', '接口', '状态码', '耗时', '错误码'],
    chartTemplates: ['errors', 'latency', 'traffic']
  },
  behavior: {
    logType: 'behavior',
    title: '用户行为日志',
    route: '/monitor/behavior',
    defaultColumns: ['时间', '用户', 'action', '页面', '商品', '停留时长'],
    chartTemplates: ['behavior_funnel', 'traffic']
  },
  'web-server': {
    logType: 'web_server',
    title: 'Web服务器日志',
    route: '/monitor/web-server',
    defaultColumns: ['时间', 'URI', '状态码', '耗时', 'upstream', 'UA'],
    chartTemplates: ['errors', 'latency', 'traffic']
  },
  performance: {
    logType: 'performance',
    title: '性能指标日志',
    route: '/monitor/performance',
    defaultColumns: ['时间', '服务', '指标名', '指标值', '主机'],
    chartTemplates: ['infra_health', 'latency']
  },
  security: {
    logType: 'security',
    title: '安全日志',
    route: '/monitor/security',
    defaultColumns: ['时间', '事件类型', '风险级', 'IP', '规则', '状态'],
    chartTemplates: ['security']
  },
  infrastructure: {
    logType: 'infrastructure',
    title: '基础设施日志',
    route: '/monitor/infrastructure',
    defaultColumns: ['时间', '组件', '资源类型', '状态', '详情'],
    chartTemplates: ['infra_health']
  },
  audit: {
    logType: 'audit',
    title: '审计日志',
    route: '/monitor/audit',
    defaultColumns: ['时间', '操作人', '操作', '对象', '变更前后值'],
    chartTemplates: ['traffic']
  }
}

export function getLogTypeMeta(key) {
  return LOG_TYPE_META[key] || LOG_TYPE_META.application
}

export function getAllLogTypeMeta() {
  return Object.values(LOG_TYPE_META)
}
