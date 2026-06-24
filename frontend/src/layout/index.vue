<template>
  <div class="layout">
    <aside class="sidebar">
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
      <main class="main" :class="{ 'main--analysis': isAnalysisRoute }">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { provideTimeRange } from '../composables/useTimeRange.js'
import SidebarTree from './components/SidebarTree.vue'
import TopBar from './components/TopBar.vue'
import PipelineHealthDot from './components/PipelineHealthDot.vue'

const route = useRoute()
const isAnalysisRoute = computed(() => String(route.path || '').startsWith('/analysis/'))

provideTimeRange()
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
  display: flex;
  flex-direction: column;
  width: 240px;
  flex-shrink: 0;
  height: 100%;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(37, 99, 235, 0.12), transparent 24%),
    var(--color-sidebar);
  color: var(--color-sidebar-text);
  border-right: 1px solid var(--color-sidebar-border);
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
  color: #fff;
}
.brand p {
  margin: 5px 0 0;
  font-size: 11px;
  color: var(--color-sidebar-text-muted);
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
}
.main {
  flex: 1;
  min-height: 0;
  padding: 24px;
  overflow-y: auto;
  overflow-x: hidden;
}

.main--analysis {
  padding: 0;
  background: #080b10;
}
</style>
