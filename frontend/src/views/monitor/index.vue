<template>
  <section>
    <h1>日志监控</h1>
    <p>这里建议后续嵌入 Kibana Dashboard，当前先提供快速跳转。</p>
    <a :href="kibanaUrl" target="_blank">打开 Kibana</a>
  </section>
</template>

<script setup>
const kibanaUrl = import.meta.env.VITE_KIBANA_URL
</script>
