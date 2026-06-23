<template>
  <div class="report-sections">
    <article v-for="section in sections" :key="section.title" class="section-card">
      <h3>{{ section.title }}</h3>
      <ul>
        <li v-for="point in section.points" :key="point">{{ point }}</li>
      </ul>
    </article>
    <p class="pending-tag">待接入：GET /api/v1/reports/{id}</p>
  </div>
</template>

<script setup>
const sections = [
  {
    title: '总体结论',
    points: ['窗口内系统整体健康度占位', '关键指标变化摘要占位']
  },
  {
    title: '异常发现',
    points: ['错误率异常服务占位', '耗时劣化接口占位']
  },
  {
    title: '业务洞察',
    points: ['漏斗转化变化占位', '用户行为异常占位']
  }
]
</script>

<style scoped>
.report-sections {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.section-card {
  padding: var(--spacing-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg);
}

.section-card h3 {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.section-card ul {
  margin: 0;
  padding-left: 1.2em;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.pending-tag {
  display: inline-block;
  margin: 0;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--color-warning-bg);
  color: var(--color-warning);
  font-size: 12px;
}
</style>
