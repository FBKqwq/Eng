<template>
  <div class="components-page">
    <header class="page-intro">
      <p class="intro-desc">各基础设施组件运行状态矩阵，数据来自 <code>GET /system/status</code>（F3 阶段接入真实状态）。</p>
    </header>

    <div class="page-grid page-grid-3">
      <StatusCard
        v-for="card in serviceCards"
        :key="card.title"
        :title="card.title"
        status-label="占位"
        tone="neutral"
        :description="card.description"
      />
    </div>

    <p class="dev-note">
      F3 阶段将迁移现有系统状态页能力至本页（含 containers/services 兜底规则、ES health unknown 时容器态兜底）。
    </p>
  </div>
</template>

<script setup>
import StatusCard from '../../components/common/StatusCard.vue'

const serviceCards = [
  { title: 'Backend', description: 'API 服务健康与端口' },
  { title: 'Kafka', description: '消息队列容器与 broker 状态' },
  { title: 'Elasticsearch', description: '集群健康与节点可用性' },
  { title: 'Logstash', description: '管道处理服务状态' },
  { title: 'Kibana', description: '可视化入口可用性' },
  { title: 'LLM', description: '智能诊断模型配置与连通性' }
]
</script>

<style scoped>
.page-intro {
  margin-bottom: var(--spacing-md);
}

.intro-desc {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.intro-desc code {
  font-size: 12px;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--color-bg);
  color: var(--color-text);
}

.dev-note {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  border-left: 3px solid var(--color-primary);
  font-size: 13px;
  color: var(--color-text-secondary);
  background: var(--color-bg);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}
</style>
