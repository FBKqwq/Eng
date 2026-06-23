<template>
  <section class="page-section">
    <h2>耗时分布</h2>
    <TrendChart placeholder="耗时分布占位：avg / p95 / p99 多系列折线图" />
  </section>
</template>

<script setup>
import TrendChart from '../common/charts/TrendChart.vue'
</script>
