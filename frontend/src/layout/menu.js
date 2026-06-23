/** 侧边栏树状目录唯一配置源：新增页面只改此文件与路由 */
export const menuTree = [
  {
    title: '总览驾驶舱',
    icon: 'dashboard',
    path: '/dashboard'
  },
  {
    title: '日志监控',
    icon: 'monitor',
    children: [
      { title: '应用服务日志', path: '/monitor/application' },
      { title: '用户行为日志', path: '/monitor/behavior' },
      { title: 'Web服务器日志', path: '/monitor/web-server' },
      { title: '性能指标日志', path: '/monitor/performance' },
      { title: '安全日志', path: '/monitor/security' },
      { title: '基础设施日志', path: '/monitor/infrastructure' },
      { title: '审计日志', path: '/monitor/audit' }
    ]
  },
  {
    title: '智能分析',
    icon: 'analysis',
    children: [
      { title: '异常诊断中心', path: '/analysis/diagnosis' },
      { title: '分析轨迹', path: '/analysis/langgraph-history' },
      { title: '周期体检报告', path: '/analysis/reports' },
      { title: '预警中心', path: '/analysis/alerts' },
      { title: '调用链路追踪', path: '/analysis/trace' },
      { title: '业务漏斗洞察', path: '/analysis/funnel' }
    ]
  },
  {
    title: '系统运维',
    icon: 'system',
    children: [
      { title: '链路健康与验证', path: '/system/pipeline' },
      { title: '组件运行状态', path: '/system/components' },
      { title: '配置快照', path: '/system/config' },
      { title: 'Goulingming 统计', path: '/goulingming/stat' },
      { title: 'Goulingming 日志检索', path: '/goulingming/log-search' }
    ]
  }
]
