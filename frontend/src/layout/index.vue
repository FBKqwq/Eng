<template>
  <div class="layout">
    <aside class="sidebar">
      <h2>日志分析系统</h2>
      <nav>
        <router-link to="/">首页</router-link>
        <router-link to="/monitor">日志监控</router-link>
        <router-link to="/diagnosis">智能诊断</router-link>
        <router-link to="/results">实验结果</router-link>
        <router-link to="/system">系统状态</router-link>
      </nav>
    </aside>
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.layout { display: flex; min-height: 100vh; }
.sidebar { width: 220px; background: #111827; color: white; padding: 24px; }
.sidebar nav { display: flex; flex-direction: column; gap: 12px; margin-top: 24px; }
.sidebar a { color: #d1d5db; }
.sidebar a.router-link-active { color: white; font-weight: bold; }
.main { flex: 1; padding: 24px; }
</style>
