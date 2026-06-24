<template>
  <DashboardFrame title="error_code 分布" subtitle="TOP 10">
    <BaseChart :option="option" height="126px" empty-text="暂无错误码数据" />
  </DashboardFrame>
</template>

<script setup>
import { computed } from 'vue'
import DashboardFrame from './DashboardFrame.vue'
import BaseChart from '../common/charts/BaseChart.vue'
const props = defineProps({ buckets: { type: Array, default: () => [] } })
const option = computed(() => props.buckets.length ? ({
  color: ['#2563eb', '#38bdf8', '#f59e0b', '#ef4444', '#f97316', '#22c55e', '#64748b'],
  tooltip: { trigger: 'item' },
  legend: { orient: 'vertical', right: 0, top: 'center', itemWidth: 8, itemHeight: 5, textStyle: { fontSize: 8, color: '#52677b' } },
  series: [{
    type: 'pie',
    radius: ['43%', '70%'],
    center: ['34%', '50%'],
    label: { show: false },
    itemStyle: { borderColor: '#fff', borderWidth: 2 },
    data: props.buckets.map((item) => ({ name: item.key, value: item.count }))
  }]
}) : null)
</script>
