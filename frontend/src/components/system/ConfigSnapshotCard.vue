<template>
  <EmptyState title="配置快照卡占位" description="Kafka/ES/索引模式/LLM 只读键值展示 + Kibana 入口" pending-api="GET /api/v1/system/status" />
</template>

<script setup>
import EmptyState from '../common/EmptyState.vue'
</script>
