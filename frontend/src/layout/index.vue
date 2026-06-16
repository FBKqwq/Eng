<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">
        <h2>日志分析系统</h2>
        <p>ELK + Kafka + LangGraph</p>
      </div>
      <SidebarTree />
      <PipelineHealthDot />
    </aside>
    <div class="content">
      <TopBar />
      <main class="main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { provideTimeRange } from '../composables/useTimeRange.js'
import SidebarTree from './components/SidebarTree.vue'
import TopBar from './components/TopBar.vue'
import PipelineHealthDot from './components/PipelineHealthDot.vue'

provideTimeRange()
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
  background: var(--color-bg);
}
.sidebar {
  display: flex;
  flex-direction: column;
  width: 240px;
  flex-shrink: 0;
  background: var(--color-sidebar);
  color: var(--color-sidebar-text);
}
.brand {
  padding: 20px 16px 12px;
  border-bottom: 1px solid var(--color-sidebar-border);
}
.brand h2 {
  margin: 0;
  font-size: 16px;
  color: #fff;
}
.brand p {
  margin: 4px 0 0;
  font-size: 11px;
  color: var(--color-sidebar-text-muted);
}
.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.main {
  flex: 1;
  padding: 24px;
  overflow: auto;
}
</style>
