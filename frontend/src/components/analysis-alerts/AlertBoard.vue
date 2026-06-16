<template>
  <div class="page-grid page-grid-3">
    <StatCard label="Active" hint="活跃预警计数占位" />
    <StatCard label="Acknowledged" hint="已确认计数占位" />
    <StatCard label="Resolved" hint="已解决计数占位" />
  </div>
</template>

<script setup>
import StatCard from '../common/StatCard.vue'
</script>
