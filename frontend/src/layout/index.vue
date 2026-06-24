<template>
  <div class="layout" :class="`layout--${mainTheme}`">
    <aside class="sidebar" :class="`sidebar--${mainTheme}`">
      <div class="brand">
        <h2>日志分析系统</h2>
        <p>ELK + Kafka + LangGraph</p>
      </div>
      <nav class="sidebar-nav" aria-label="主导航">
        <SidebarTree />
      </nav>
      <PipelineHealthDot />
    </aside>
    <div class="content">
      <TopBar />
      <main class="main" :class="[`main--${mainTheme}`, { 'main--analysis': isAnalysisRoute }]">
        <router-view />
      </main>
    </div>
    <ToastContainer />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { provideTimeRange } from '../composables/useTimeRange.js'
import { provideTheme } from '../composables/useTheme.js'
import { provideToast } from '../composables/useToast.js'
import SidebarTree from './components/SidebarTree.vue'
import TopBar from './components/TopBar.vue'
import PipelineHealthDot from './components/PipelineHealthDot.vue'
import ToastContainer from '../components/common/ToastContainer.vue'

const route = useRoute()
const isAnalysisRoute = computed(() => String(route.path || '').startsWith('/analysis/'))
const mainTheme = computed(() => isAnalysisRoute.value ? 'dark' : 'light')

provideTimeRange()
provideTheme()
provideToast()
</script>

<style scoped>
.layout {
  display: flex;
  height: 100%;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.4), rgba(245, 247, 251, 0)),
    var(--color-bg);
}
.sidebar {
  --color-sidebar-text: #e2e8f0;
  --color-sidebar-text-muted: #94a3b8;
  --color-sidebar-border: rgba(148, 163, 184, 0.18);
  --color-sidebar-hover: rgba(37, 99, 235, 0.14);
  --color-sidebar-active: rgba(37, 99, 235, 0.24);
  --sidebar-active-text: #fff;
  --sidebar-active-border: rgba(96, 165, 250, 0.4);
  --sidebar-active-gradient: linear-gradient(90deg, rgba(37, 99, 235, 0.32), rgba(8, 145, 178, 0.16));
  position: relative;
  display: flex;
  flex-direction: column;
  width: 240px;
  flex-shrink: 0;
  height: 100%;
  overflow: hidden;
  background: transparent;
  color: var(--color-sidebar-text);
  border-right: 1px solid var(--color-sidebar-border);
  transition:
    color 520ms cubic-bezier(0.22, 1, 0.36, 1),
    border-color 520ms cubic-bezier(0.22, 1, 0.36, 1);
}

.sidebar::before,
.sidebar::after {
  position: absolute;
  z-index: 0;
  inset: 0;
  pointer-events: none;
  content: '';
  transition: opacity 620ms cubic-bezier(0.22, 1, 0.36, 1);
}

.sidebar::before {
  opacity: 1;
  background:
    radial-gradient(circle at 18% 4%, rgba(59, 130, 246, 0.2), transparent 28%),
    linear-gradient(180deg, #0b1426, #09111f);
}

.sidebar::after {
  opacity: 0;
  background:
    radial-gradient(circle at 12% 4%, rgba(0, 122, 255, 0.1), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(244, 248, 252, 0.98));
}

.sidebar--light {
  --color-sidebar-text: #172033;
  --color-sidebar-text-muted: #64748b;
  --color-sidebar-border: rgba(148, 163, 184, 0.24);
  --color-sidebar-hover: rgba(0, 122, 255, 0.08);
  --color-sidebar-active: rgba(0, 122, 255, 0.1);
  --sidebar-active-text: #0756b8;
  --sidebar-active-border: rgba(0, 122, 255, 0.2);
  --sidebar-active-gradient: linear-gradient(90deg, rgba(0, 122, 255, 0.13), rgba(90, 200, 250, 0.06));
}

.sidebar--light::before {
  opacity: 0;
}

.sidebar--light::after {
  opacity: 1;
}

.sidebar > * {
  position: relative;
  z-index: 1;
}
.brand {
  flex-shrink: 0;
  padding: 22px 16px 16px;
  border-bottom: 1px solid var(--color-sidebar-border);
}
.brand h2 {
  margin: 0;
  font-size: 17px;
  font-weight: 800;
  color: var(--color-sidebar-text);
  transition: color 480ms ease;
}
.brand p {
  margin: 5px 0 0;
  font-size: 11px;
  color: var(--color-sidebar-text-muted);
  transition: color 480ms ease;
}
.sidebar-nav {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.2), rgba(245, 247, 251, 0)),
    var(--color-bg);
}

/* Dark mode content gradient override */
[data-theme="dark"] .content {
  background:
    linear-gradient(180deg, rgba(37, 99, 235, 0.04), transparent 24%),
    var(--color-bg);
}
.main {
  flex: 1;
  min-height: 0;
  padding: 24px;
  overflow-y: auto;
  overflow-x: hidden;
}

.main--light {
  background: #f5f7fb;
}

.main--analysis {
  padding: 0;
  background: #080b10;
}

@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .sidebar::before,
  .sidebar::after,
  .brand h2,
  .brand p {
    transition-duration: 0.01ms;
  }
}
</style>
