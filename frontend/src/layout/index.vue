<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-title">
          <h2>日志分析系统</h2>
          <router-link to="/analysis/yw/ym" class="ai-assistant-btn" title="AI日志问答助手">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </router-link>
        </div>
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
const isAnalysisRoute = computed(() => {
  const path = String(route.path || '')
  return path.startsWith('/analysis/') && !path.startsWith('/analysis/yw/ym')
})

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
.brand-title {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand h2 {
  margin: 0;
  font-size: 17px;
  font-weight: 800;
  color: #fff;
}
.ai-assistant-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  text-decoration: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
  animation: pulse 2s infinite;
}
.ai-assistant-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}
.ai-assistant-btn svg {
  width: 16px;
  height: 16px;
}
@keyframes pulse {
  0%, 100% {
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }
  50% {
    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.6);
  }
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
