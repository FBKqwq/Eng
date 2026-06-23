<template>
  <section class="page-section">
    <h2>流量与错误</h2>
    <TrendChart placeholder="流量趋势占位：请求量面积折线 + 错误量柱状叠加（application + web_server）" />
  </section>
</template>

<script setup>
import TrendChart from '../common/charts/TrendChart.vue'
</script>
