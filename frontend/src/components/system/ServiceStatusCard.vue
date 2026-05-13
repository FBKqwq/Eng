<template>
  <article class="service-card">
    <div class="service-header">
      <div>
        <p class="service-type">{{ service.type }}</p>
        <h3>{{ service.name }}</h3>
      </div>
      <span class="status-pill" :class="`status-${meta.tone}`">{{ meta.label }}</span>
    </div>

    <dl>
      <div>
        <dt>访问地址</dt>
        <dd>{{ service.endpoint }}</dd>
      </div>
      <div>
        <dt>状态说明</dt>
        <dd>{{ service.detail }}</dd>
      </div>
    </dl>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { getStatusMeta } from '../../utils/systemStatus'

const props = defineProps({
  service: {
    type: Object,
    required: true
  }
})

const meta = computed(() => getStatusMeta(props.service.status))
</script>

<style scoped>
.service-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  min-height: 174px;
  padding: 18px;
}

.service-header {
  align-items: flex-start;
  display: flex;
  gap: 16px;
  justify-content: space-between;
}

.service-type {
  color: #6b7280;
  font-size: 13px;
  margin: 0 0 6px;
}

h3 {
  color: #111827;
  font-size: 20px;
  margin: 0;
}

.status-pill {
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  padding: 5px 10px;
  white-space: nowrap;
}

.status-success {
  background: #dcfce7;
  color: #166534;
}

.status-danger {
  background: #fee2e2;
  color: #991b1b;
}

.status-warning {
  background: #fef3c7;
  color: #92400e;
}

.status-neutral {
  background: #f3f4f6;
  color: #4b5563;
}

dl {
  display: grid;
  gap: 12px;
  margin: 18px 0 0;
}

dt {
  color: #6b7280;
  font-size: 12px;
  margin-bottom: 4px;
}

dd {
  color: #1f2937;
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
  overflow-wrap: anywhere;
}
</style>
