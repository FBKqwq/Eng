<template>
  <div class="alert-table-placeholder">
    <table class="table-skeleton">
      <thead>
        <tr>
          <th>类型</th>
          <th>严重度</th>
          <th>服务</th>
          <th>首次时间</th>
          <th>最近时间</th>
          <th>证据数</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in placeholderRows" :key="row">
          <td colspan="7" class="empty-row">— 等待预警数据 —</td>
        </tr>
      </tbody>
    </table>
    <p class="table-note">active 行支持确认操作（POST /alerts/{id}/ack，F6 阶段）</p>
  </div>
</template>

<script setup>
const placeholderRows = [1, 2, 3]
</script>

<style scoped>
.table-skeleton {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.table-skeleton th {
  padding: 10px 12px;
  text-align: left;
  font-weight: 500;
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
}

.empty-row {
  padding: 16px 12px;
  text-align: center;
  color: var(--color-text-muted);
  border-bottom: 1px dashed var(--color-border);
}

.table-note {
  margin: var(--spacing-sm) 0 0;
  font-size: 11px;
  color: var(--color-text-muted);
}
</style>
