import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../layout/index.vue'
import DashboardView from '../views/dashboard/index.vue'
import MonitorApplication from '../views/monitor/application.vue'
import MonitorBehavior from '../views/monitor/behavior.vue'
import MonitorWebServer from '../views/monitor/web-server.vue'
import MonitorPerformance from '../views/monitor/performance.vue'
import MonitorSecurity from '../views/monitor/security.vue'
import MonitorInfrastructure from '../views/monitor/infrastructure.vue'
import MonitorAudit from '../views/monitor/audit.vue'
import AnalysisDiagnosis from '../views/analysis/diagnosis.vue'
import AnalysisReports from '../views/analysis/reports.vue'
import AnalysisAlerts from '../views/analysis/alerts.vue'
import AnalysisTrace from '../views/analysis/trace.vue'
import AnalysisFunnel from '../views/analysis/funnel.vue'
import SystemPipeline from '../views/system/pipeline.vue'
import SystemComponents from '../views/system/components.vue'
import SystemConfig from '../views/system/config.vue'
import GoulingmingStat from '../views/goulingming/stat/index.vue'
import GoulingmingLogSearch from '../views/goulingming/log-search/index.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: DashboardView,
        meta: { title: '总览驾驶舱' }
      },
      { path: 'monitor', redirect: '/monitor/application' },
      {
        path: 'monitor/application',
        name: 'monitor-application',
        component: MonitorApplication,
        meta: { title: '应用服务日志' }
      },
      {
        path: 'monitor/behavior',
        name: 'monitor-behavior',
        component: MonitorBehavior,
        meta: { title: '用户行为日志' }
      },
      {
        path: 'monitor/web-server',
        name: 'monitor-web-server',
        component: MonitorWebServer,
        meta: { title: 'Web服务器日志' }
      },
      {
        path: 'monitor/performance',
        name: 'monitor-performance',
        component: MonitorPerformance,
        meta: { title: '性能指标日志' }
      },
      {
        path: 'monitor/security',
        name: 'monitor-security',
        component: MonitorSecurity,
        meta: { title: '安全日志' }
      },
      {
        path: 'monitor/infrastructure',
        name: 'monitor-infrastructure',
        component: MonitorInfrastructure,
        meta: { title: '基础设施日志' }
      },
      {
        path: 'monitor/audit',
        name: 'monitor-audit',
        component: MonitorAudit,
        meta: { title: '审计日志' }
      },
      {
        path: 'analysis/diagnosis',
        name: 'analysis-diagnosis',
        component: AnalysisDiagnosis,
        meta: { title: '异常诊断中心' }
      },
      {
        path: 'analysis/reports',
        name: 'analysis-reports',
        component: AnalysisReports,
        meta: { title: '周期体检报告' }
      },
      {
        path: 'analysis/alerts',
        name: 'analysis-alerts',
        component: AnalysisAlerts,
        meta: { title: '预警中心' }
      },
      {
        path: 'analysis/trace',
        name: 'analysis-trace',
        component: AnalysisTrace,
        meta: { title: '调用链路追踪' }
      },
      {
        path: 'analysis/funnel',
        name: 'analysis-funnel',
        component: AnalysisFunnel,
        meta: { title: '业务漏斗洞察' }
      },
      {
        path: 'system/pipeline',
        name: 'system-pipeline',
        component: SystemPipeline,
        meta: { title: '链路健康与验证' }
      },
      {
        path: 'system/components',
        name: 'system-components',
        component: SystemComponents,
        meta: { title: '组件运行状态' }
      },
      {
        path: 'system/config',
        name: 'system-config',
        component: SystemConfig,
        meta: { title: '配置快照' }
      },
      {
        path: 'goulingming/stat',
        name: 'goulingming-stat',
        component: GoulingmingStat,
        meta: { title: 'Goulingming 统计看板' }
      },
      {
        path: 'goulingming/log-search',
        name: 'goulingming-log-search',
        component: GoulingmingLogSearch,
        meta: { title: 'Goulingming 日志检索' }
      },
      // 旧路由重定向
      { path: 'diagnosis', redirect: '/analysis/diagnosis' },
      { path: 'results', redirect: '/analysis/reports' },
      { path: 'system', redirect: '/system/components' }
    ]
  },
  {
    path: '/temp/developer',
    name: 'developer',
    component: SystemComponents
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
