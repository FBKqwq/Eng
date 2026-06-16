<template>
  <section class="page-section">
    <EmptyState title="健康总仪表 + 核心指标带" description="综合健康分仪表盘 + 5 个数字指标卡（日志总量/错误率/响应/预警）" pending-api="metrics 聚合接口" />
  </section>
</template>

<script setup>
import EmptyState from '../common/EmptyState.vue'
</script>
