import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../layout/index.vue'
import HomeView from '../views/home/index.vue'
import MonitorView from '../views/monitor/index.vue'
import DiagnosisView from '../views/diagnosis/index.vue'
import ResultsView from '../views/results/index.vue'
import SystemView from '../views/system/index.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    children: [
      { path: '', name: 'home', component: HomeView },
      { path: 'monitor', name: 'monitor', component: MonitorView },
      { path: 'diagnosis', name: 'diagnosis', component: DiagnosisView },
      { path: 'results', name: 'results', component: ResultsView },
      { path: 'system', name: 'system', component: SystemView }
    ]
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
