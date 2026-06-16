<template>
  <div class="components-page">
    <div class="page-grid page-grid-3">
      <StatusCard title="Backend" status-label="占位" />
      <StatusCard title="Kafka" status-label="占位" />
      <StatusCard title="Elasticsearch" status-label="占位" />
      <StatusCard title="Logstash" status-label="占位" />
      <StatusCard title="Kibana" status-label="占位" />
      <StatusCard title="LLM" status-label="占位" />
    </div>
    <p class="dev-note">F3 阶段将迁移现有系统状态页能力至本页（含 containers/services 兜底规则）。</p>
  </div>
</template>

<script setup>
import StatusCard from '../../components/common/StatusCard.vue'
</script>

<style scoped>
.dev-note {
  margin-top: 16px;
  font-size: 13px;
  color: var(--color-text-secondary);
}
</style>
